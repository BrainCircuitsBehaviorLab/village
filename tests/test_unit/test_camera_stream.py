"""Tests for the web view of a camera (CameraStream).

OpenCV is replaced in the tests (see conftest.py), so the compression is
replaced here too: the "JPEG" is the bytes of the frame, which lets the tests
check the color conversion.
"""

import threading
import time
import urllib.error
import urllib.request
from types import SimpleNamespace

import numpy as np
import pytest

from village.scripts import camera_stream
from village.scripts.camera_stream import CameraStream


def fake_cvt_color(frame: np.ndarray, code: str) -> np.ndarray:
    if code.startswith("RGB"):
        return frame[:, :, 2::-1].copy()  # the first 3 channels, reversed
    return frame[:, :, :3].copy()


FAKE_CV2 = SimpleNamespace(
    COLOR_RGBA2BGR="RGBA2BGR",
    COLOR_BGRA2BGR="BGRA2BGR",
    COLOR_RGB2BGR="RGB2BGR",
    IMWRITE_JPEG_QUALITY=1,
    cvtColor=fake_cvt_color,
    imencode=lambda ext, frame, params: (
        True,
        np.frombuffer(frame.tobytes(), np.uint8),
    ),
)


@pytest.fixture(autouse=True)
def fake_cv2(monkeypatch) -> None:
    monkeypatch.setattr(camera_stream, "cv2", FAKE_CV2)


def make_stream(rgb_order: bool = True) -> tuple[CameraStream, str]:
    stream = CameraStream(0, fps=100, title="village01 BOX", rgb_order=rgb_order)
    port = stream.server.server_address[1]
    return stream, f"http://127.0.0.1:{port}"


def wait_for(condition, timeout: float = 5.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


def offer_frames(stream: CameraStream, frame: np.ndarray) -> threading.Event:
    """Offers the frame continuously, as the camera does, until the returned
    event is set."""
    stop = threading.Event()

    def offer() -> None:
        while not stop.is_set():
            stream.offer(frame)
            time.sleep(0.02)

    threading.Thread(target=offer, daemon=True).start()
    return stop


def read_first_jpeg(url: str) -> bytes:
    """Connects to the stream and returns its first image."""
    with urllib.request.urlopen(url + "/stream", timeout=5) as response:
        assert response.headers["Content-Type"].startswith("multipart/x-mixed-replace")
        assert response.readline() == b"--frame\r\n"
        assert response.readline() == b"Content-Type: image/jpeg\r\n"
        length = int(response.readline().split(b":")[1])
        assert response.readline() == b"\r\n"
        return response.read(length)


def test_page_shows_the_stream() -> None:
    stream, url = make_stream()
    try:
        with urllib.request.urlopen(url + "/", timeout=5) as response:
            page = response.read().decode()
        assert "<title>village01 BOX</title>" in page
        assert 'src="stream"' in page
    finally:
        stream.close()


def test_nothing_is_copied_without_clients() -> None:
    stream, _ = make_stream()
    try:
        stream.offer(np.zeros((48, 64, 4), np.uint8))
        assert stream._frame is None
    finally:
        stream.close()


def test_stream_sends_jpeg_in_the_right_colors() -> None:
    """A red frame in RGBX order, as picamera2 gives it, is sent in BGR order."""
    stream, url = make_stream(rgb_order=True)
    try:
        frame = np.zeros((48, 64, 4), np.uint8)
        frame[:, :, 0] = 255  # R
        frame[:, :, 3] = 255  # X
        stop = offer_frames(stream, frame)
        try:
            jpeg = read_first_jpeg(url)
            image = np.frombuffer(jpeg, np.uint8).reshape(48, 64, 3)
            assert image[24, 32].tolist() == [0, 0, 255]  # BGR, as OpenCV expects
            assert wait_for(lambda: stream.clients == 0)  # the client has gone
        finally:
            stop.set()
    finally:
        stream.close()


def test_unknown_path() -> None:
    stream, url = make_stream()
    try:
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(url + "/other", timeout=5)
        assert error.value.code == 404
        error.value.close()
    finally:
        stream.close()
