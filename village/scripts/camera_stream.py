"""Live view of a camera in a web browser, as an MJPEG video served over HTTP."""

import html
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

JPEG_QUALITY = 80
# A client waits at most this long for a new frame before checking that it is
# still connected (a stopped camera sends no frames).
WAIT_FRAME_S = 5.0

PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  html, body {{ margin: 0; height: 100%; background: #000; }}
  img {{ display: block; width: 100%; height: 100%; object-fit: contain; }}
</style>
</head>
<body>
<img id="video" src="stream" alt="{title}">
<script>
  // If the connection is lost (Village restarted), try again every 2 s.
  const video = document.getElementById("video");
  video.onerror = () => setTimeout(() => {{
    video.src = "stream?" + Date.now();
  }}, 2000);
</script>
</body>
</html>
"""


class CameraStream:
    """Serves the frames of a camera as a live video that any web browser on
    the same network can show, at http://<raspberry address>:<port>.

    The camera uses its frames as always: offer() is called from its frame
    callback and only copies a frame, at most `fps` times per second and only
    while someone is watching, so it costs nothing otherwise. The JPEG
    compression and the sending happen in the server threads (one per
    client), so a slow client or network never delays the camera. Each frame
    is compressed only once, whatever the number of clients.
    """

    def __init__(self, port: int, fps: int, title: str, rgb_order: bool) -> None:
        """Starts the server in a background thread.

        Args:
            port (int): The TCP port.
            fps (int): The maximum number of frames per second sent.
            title (str): The title of the page (the name of the browser tab).
            rgb_order (bool): True if the frames have their channels in RGB
                order, False if in BGR order (as OpenCV expects).

        Raises:
            OSError: If the port cannot be used (e.g. it is already in use).
        """
        self.period = 1 / max(fps, 1)
        self.page = PAGE.format(title=html.escape(title)).encode()
        self.rgb_order = rgb_order
        self.clients = 0
        self._last_copy = 0.0
        self._condition = threading.Condition()
        self._frame: np.ndarray | None = None
        self._frame_number = 0
        self._encode_lock = threading.Lock()
        self._jpeg = b""
        self._jpeg_number = 0
        self.server = ThreadingHTTPServer(("", port), self._handler_class())
        self.server.daemon_threads = True
        threading.Thread(
            target=self.server.serve_forever, name="camera_stream", daemon=True
        ).start()

    def offer(self, frame: np.ndarray) -> None:
        """Keeps a copy of the frame for the clients, if any client is watching
        and enough time has passed since the previous copy.

        Called from the camera callback on every frame: the frame is a view of
        a camera buffer that is reused afterwards, hence the copy.

        Args:
            frame (np.ndarray): The frame, with 3 or 4 channels.
        """
        if self.clients == 0:
            return
        now = time.monotonic()
        if now - self._last_copy < self.period:
            return
        self._last_copy = now
        if frame.ndim == 3 and frame.shape[2] == 4:
            code = cv2.COLOR_RGBA2BGR if self.rgb_order else cv2.COLOR_BGRA2BGR
            copy = cv2.cvtColor(frame, code)
        elif self.rgb_order:
            copy = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            copy = frame.copy()
        with self._condition:
            self._frame = copy
            self._frame_number += 1
            self._condition.notify_all()

    def close(self) -> None:
        """Stops the server and closes its port."""
        self.server.shutdown()
        self.server.server_close()

    def _next_jpeg(self, last_number: int) -> tuple[int, bytes]:
        """Waits for a frame newer than last_number and returns it as JPEG.

        Args:
            last_number (int): The number of the last frame sent to the client.

        Returns:
            tuple[int, bytes]: The number of the frame and its JPEG, or
            (last_number, b"") if no new frame arrived in WAIT_FRAME_S.
        """
        with self._condition:
            if not self._condition.wait_for(
                lambda: self._frame_number > last_number, timeout=WAIT_FRAME_S
            ):
                return last_number, b""
            number, frame = self._frame_number, self._frame
        # compressed outside the condition, which offer() (the camera
        # callback) needs: a frame is never changed once offered
        with self._encode_lock:
            if self._jpeg_number < number:
                ok, encoded = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                )
                if ok:
                    self._jpeg = encoded.tobytes()
                    self._jpeg_number = number
            return self._jpeg_number, self._jpeg

    def _add_client(self, change: int) -> None:
        with self._condition:
            self.clients += change

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        stream = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = self.path.split("?")[0]
                if path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(stream.page)))
                    self.end_headers()
                    self.wfile.write(stream.page)
                elif path == "/stream":
                    self.send_stream()
                else:
                    self.send_error(404)

            def send_stream(self) -> None:
                self.send_response(200)
                self.send_header("Cache-Control", "no-cache, private")
                self.send_header(
                    "Content-Type", "multipart/x-mixed-replace; boundary=frame"
                )
                self.end_headers()
                stream._add_client(1)
                number = 0
                try:
                    while True:
                        new_number, jpeg = stream._next_jpeg(number)
                        if new_number == number:
                            # no new frame (camera stopped): the last one is
                            # sent again, so a client that has gone is noticed
                            # and its thread ends
                            jpeg = stream._jpeg
                            if not jpeg:
                                continue
                        number = new_number
                        self.wfile.write(
                            b"--frame\r\nContent-Type: image/jpeg\r\n"
                            b"Content-Length: "
                            + str(len(jpeg)).encode()
                            + b"\r\n\r\n"
                            + jpeg
                            + b"\r\n"
                        )
                except OSError:  # the client has gone (or the connection failed)
                    pass
                finally:
                    stream._add_client(-1)

            def log_message(self, *args) -> None:
                pass  # no line on the console for every request

        return Handler
