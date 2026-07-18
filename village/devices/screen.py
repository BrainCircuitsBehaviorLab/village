from __future__ import annotations

import os
import queue
import subprocess
import time
import traceback
from typing import Callable, Optional

import cv2
import gpiod
import numpy as np
from gpiod.line import Direction, Value
from PyQt5.QtCore import (
    QMetaObject,
    QMutex,
    QObject,
    QRect,
    Qt,
    QThread,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QColor, QGuiApplication, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QOpenGLWidget

from village.classes.enums import ScreenActive
from village.classes.null_classes import NullScreen
from village.devices.sound_device import sound_device
from village.scripts.error_queue import error_queue
from village.scripts.time_utils import time_utils
from village.settings import settings


class VideoWorker(QObject):
    """Worker class for decoding video frames in a separate thread.

    Uses OpenCV to read frames and serves them as QImages for display.
    Maintains synchronization with real-time based on the video's FPS.
    """

    finished = pyqtSignal()

    def __init__(self, path: str) -> None:
        """Initializes the VideoWorker.

        Args:
            path (str): Path to the video file.
        """
        super().__init__()
        self.path = path
        self.cap: Optional[cv2.VideoCapture] = None

        self._running: bool = False
        self.mtx = QMutex()

        self._latest_img: Optional[QImage] = None
        self._latest_idx: int = -1

        self._served_img: Optional[QImage] = None
        self._served_idx: int = -1

        self._fps: float = 0.0
        self._frame_dt: float = 0.0
        self._play_start: float = 0.0
        self._started: bool = False

    @pyqtSlot()
    def run(self) -> None:
        """Main loop for reading and processing video frames."""
        self._running = True
        try:
            self.cap = cv2.VideoCapture(self.path)
            if self.cap is None or not self.cap.isOpened():
                self._running = False
                return

            try:
                fps = float(self.cap.get(cv2.CAP_PROP_FPS))
                if fps <= 0:
                    fps = 30.0
            except Exception:
                fps = 30.0

            self._fps = fps
            self._frame_dt = 1.0 / fps if fps > 0 else 0.0

            produced_idx = -1

            while self._running:
                ok, bgr = self.cap.read()
                if not ok:
                    break

                rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
                h, w = rgba.shape[:2]
                img = QImage(rgba.data, w, h, QImage.Format_RGBA8888).copy()

                produced_idx += 1

                self.mtx.lock()
                try:
                    self._latest_img = img
                    self._latest_idx = produced_idx
                finally:
                    self.mtx.unlock()

        except Exception:
            try:
                error_queue.put_nowait(("video", traceback.format_exc()))
            except queue.Full:
                pass
        finally:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self._running = False
            self.finished.emit()

    def get_latest_qimage(self) -> Optional[QImage]:
        """Returns the most appropriate video frame for the current time.

        Calculates the target frame based on elapsed time since start.

        Returns:
            Optional[QImage]: The current video frame.
        """
        if not self._started or self._frame_dt <= 0:
            return None

        now = time.monotonic()
        target_idx = int((now - self._play_start) / self._frame_dt)

        if self._served_idx == target_idx and self._served_img is not None:
            return self._served_img

        self.mtx.lock()
        try:
            latest_img = self._latest_img
            latest_idx = self._latest_idx
        finally:
            self.mtx.unlock()

        if latest_img is None or latest_idx < 0:
            return self._served_img

        if latest_idx >= target_idx:
            self._served_idx = target_idx
            self._served_img = latest_img
            return self._served_img

        return self._served_img

    def play(self) -> None:
        """Sets the playback start time so get_latest_qimage starts serving frames."""
        self._play_start = time.monotonic()
        self._started = True

    def stop(self) -> None:
        """Stops the video decoding loop."""
        self._running = False


class Screen(QOpenGLWidget):
    """Window for displaying stimuli (images or video) in visual behavior tasks.

    This class handles the rendering loop, GPIO synchronization (for timestamps),
    and displaying images or video streams.
    """

    def __init__(self, geometry: QRect) -> None:
        """Initializes the Screen.

        Args:
            geometry (QRect): The geometry (position and size) of the window.
        """
        super().__init__()
        self.setGeometry(geometry)
        self.setFixedSize(geometry.width(), geometry.height())
        self.setWindowTitle("Village_Box")
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)
        self.setUpdateBehavior(QOpenGLWidget.NoPartialUpdate)

        self.width_px: int = geometry.width()
        self.height_px: int = geometry.height()
        self.error: str = ""

        self.active: bool = False
        self._draw_fn: Optional[Callable] = None

        self._start_timing: float = 0.0
        self._swap_connected: bool = False

        self._gpio_request = None
        self._gpio_line_offset = 26
        self._init_gpio()

        self._video_thread: Optional[QThread] = None
        self._video_worker: Optional[VideoWorker] = None
        self._audio_left: Optional[np.ndarray] = None
        self._audio_right: Optional[np.ndarray] = None

        self.frame = 0
        self.elapsed_time = 0.0

        self.background_color = QColor("black")

        self.x = 0
        self.y = 0
        self.blend = False
        self.image: Optional[QPixmap] = None

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop_video)

        self.show()

    def _init_gpio(self) -> None:
        """Initializes the GPIO line for timestamp synchronization."""
        try:
            cfg = {
                self._gpio_line_offset: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                )
            }
            self._gpio_request = gpiod.request_lines(
                "/dev/gpiochip0", consumer="village_stim", config=cfg
            )
        except Exception:
            self._gpio_request = None

    def initializeGL(self) -> None:
        pass

    def resizeGL(self, width: int, height: int) -> None:
        pass

    def closeEvent(self, event) -> None:
        """Handles window close events, stopping updates and threads."""
        self.stop_video()
        event.ignore()

    def load_draw_function(self, draw_fn: Optional[Callable]) -> None:
        """Sets the drawing function. Stops any active rendering.

        Call load_image() or load_video() separately before or after this.

        Args:
            draw_fn (Optional[Callable]): The function to call during paint events.
        """
        self.stop_drawing()
        self._draw_fn = draw_fn

    def start_drawing(self) -> None:
        """Starts the rendering loop. Call this when you want the stimulus to appear."""
        if self.active:
            return
        self.active = True
        self._start_timing = time_utils.get_time_monotonic()
        if not self._swap_connected:
            self.frameSwapped.connect(self.update, Qt.ConnectionType.UniqueConnection)
            self._swap_connected = True
        if self._video_worker is not None:
            self._video_worker.play()
        if self._audio_left is not None:
            sound_device.play()
        QMetaObject.invokeMethod(self, "update", Qt.ConnectionType.QueuedConnection)

    def stop_drawing(self) -> None:
        """Stops the rendering loop. The video thread keeps
        running for a fast restart."""
        self.active = False
        if self._swap_connected:
            try:
                self.frameSwapped.disconnect(self.update)
            except Exception:
                pass
            self._swap_connected = False
        self.frame = 0
        self.elapsed_time = 0.0
        if self._audio_left is not None:
            sound_device.stop()
        QMetaObject.invokeMethod(self, "update", Qt.ConnectionType.QueuedConnection)

    def load_image(self, file: str) -> None:
        """Loads an image from the media directory.

        Args:
            file (str): Filename of the image.
        """
        media_directory = settings.get("MEDIA_DIRECTORY")
        image_path = os.path.join(media_directory, file)
        self.image = QPixmap(image_path)

    def _extract_audio(
        self, video_path: str
    ) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        samplerate = int(settings.get("SAMPLERATE"))
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    video_path,
                    "-vn",
                    "-f",
                    "f32le",
                    "-acodec",
                    "pcm_f32le",
                    "-ar",
                    str(samplerate),
                    "-ac",
                    "2",
                    "pipe:1",
                ],
                capture_output=True,
                timeout=30,
            )
            if len(result.stdout) == 0:
                return None, None
            audio = np.frombuffer(result.stdout, dtype=np.float32).reshape(-1, 2)
            return audio[:, 0].copy(), audio[:, 1].copy()
        except Exception:
            return None, None

    def load_video(self, file: str) -> None:
        """Loads a video from the media directory and prepares the playback thread.

        Args:
            file (str): Filename of the video.
        """
        self.stop_video()
        media_directory = settings.get("MEDIA_DIRECTORY")
        video_path = os.path.join(media_directory, file)
        self._audio_left, self._audio_right = self._extract_audio(video_path)
        if self._audio_left is not None:
            sound_device.load(self._audio_left, self._audio_right)
        self._video_thread = QThread()
        self._video_worker = VideoWorker(video_path)
        self._video_worker.moveToThread(self._video_thread)
        self._video_thread.started.connect(self._video_worker.run)
        self._video_thread.finished.connect(self._on_video_thread_finished)
        self._video_thread.start()

    def stop_video(self) -> None:
        """Stops the video playback and waits for the thread to finish."""
        if self._video_worker is not None:
            self._video_worker.stop()
        if self._video_thread is not None:
            if self._video_thread.isRunning():
                self._video_thread.quit()
                self._video_thread.wait()
            self._on_video_thread_finished()
        self._audio_left = None
        self._audio_right = None

    def _on_video_thread_finished(self) -> None:
        """Cleans up video worker/thread resources after playback stops."""
        if self._video_worker is not None:
            try:
                self._video_worker.deleteLater()
            except Exception:
                pass
            self._video_worker = None
        if self._video_thread is not None:
            try:
                self._video_thread.deleteLater()
            except Exception:
                pass
            self._video_thread = None

    def get_video_frame(self) -> Optional[QImage]:
        """Retrieves current video frame if available.

        Returns:
            Optional[QImage]: The current video frame or None.
        """
        if not self._video_worker:
            return None
        return self._video_worker.get_latest_qimage()

    def paintGL(self) -> None:
        """Main rendering loop called by OpenGL widget update."""
        if not self.active or self._draw_fn is None:
            self.clear_function()
            self.frame = 0
            self.elapsed_time = 0.0
            return

        if self._gpio_request is not None:
            try:
                self._gpio_request.set_value(self._gpio_line_offset, Value.ACTIVE)
            except Exception:
                pass

        now = time_utils.get_time_monotonic()
        self.elapsed_time = now - self._start_timing
        self.frame += 1

        try:
            self._draw_fn()
        except Exception:
            pass

        if self._gpio_request is not None:
            try:
                self._gpio_request.set_value(self._gpio_line_offset, Value.INACTIVE)
            except Exception:
                pass

    def clear_function(self) -> None:
        """Clears the window by filling it with the background color."""
        with QPainter(self) as painter:
            painter.fillRect(self.rect(), self.background_color)


def get_screen() -> "Screen | NullScreen":
    try:
        secondary_screen = QGuiApplication.screens()[1]
        geometry = secondary_screen.geometry()
        settings.set("SCREEN_RESOLUTION", (geometry.width(), geometry.height()))
    except IndexError:
        geometry = None

    if settings.get("USE_SCREEN") == ScreenActive.OFF:
        return NullScreen()

    if geometry is None:
        null_screen = NullScreen()
        null_screen.error = (
            "Secondary screen not detected. Behavior window will not be displayed."
        )
        return null_screen

    return Screen(geometry)


screen = get_screen()
