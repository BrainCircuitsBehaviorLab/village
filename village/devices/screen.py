from __future__ import annotations

import queue
import subprocess
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
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
from village.classes.null_classes import NullGpio, NullScreen
from village.devices.sound_device import sound_device
from village.scripts.error_queue import error_queue
from village.scripts.time_utils import time_utils
from village.settings import settings

if TYPE_CHECKING:
    from village.controllers.trial_recorder import TrialRecorder
    from village.custom_classes.gpio_base import GpioBase


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
        self.cap: cv2.VideoCapture | None = None

        self._running: bool = False
        self.mtx = QMutex()

        self._latest_img: QImage | None = None
        self._latest_idx: int = -1

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

            # Do not decode ahead of playback: wait until start_drawing() calls
            # play(). Otherwise the whole file is consumed before it is shown.
            while self._running and not self._started:
                time.sleep(0.001)

            produced_idx = -1

            while self._running:
                # Drop frames we are already late for: grab() advances the
                # decoder without the costly colour convert + QImage copy, so
                # playback tracks the wall clock instead of running in slow
                # motion when the Pi cannot decode every frame in time.
                if self._frame_dt > 0:
                    want = int((time.monotonic() - self._play_start) / self._frame_dt)
                    while produced_idx < want - 1 and self._running:
                        if not self.cap.grab():
                            break
                        produced_idx += 1

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

                # If we are ahead of the wall clock, wait until this frame's
                # time. Absolute target (not cumulative sleeps) so it never
                # drifts. When behind, the grab() loop above catches up instead.
                if self._frame_dt > 0:
                    ahead = (
                        self._play_start + produced_idx * self._frame_dt
                    ) - time.monotonic()
                    if ahead > 0:
                        time.sleep(ahead)

        except Exception:
            try:
                error_queue.put_nowait(
                    ("video", "Error in video worker", traceback.format_exc())
                )
            except queue.Full:
                pass
        finally:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self._running = False
            self.finished.emit()

    def get_latest_qimage(self) -> QImage | None:
        """Returns the current video frame.

        The decode loop paces itself to real time, so the latest decoded frame
        is the one to show now. paintGL samples this at the vsync rate.

        Returns:
            Optional[QImage]: The current video frame.
        """
        if not self._started:
            return None
        self.mtx.lock()
        try:
            return self._latest_img
        finally:
            self.mtx.unlock()

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
        self._draw_fn: Callable | None = None

        self._start_timing: float = 0.0
        self._swap_connected: bool = False

        # injected by manager.run_task(); NullGpio (no-op) until then. set_on/
        # set_off drive the GPIO_OUT pin for the sync pulse (see GpioBase).
        self.gpio: GpioBase | NullGpio = NullGpio()

        self._video_thread: QThread | None = None
        self._video_worker: VideoWorker | None = None
        self._audio_left: np.ndarray | None = None
        self._audio_right: np.ndarray | None = None

        self.frame = 0
        self.elapsed_time = 0.0

        self.background_color = QColor("black")

        self.x = 0
        self.y = 0
        self.blend = False
        self.image: QPixmap | None = None
        # When new visual content is requested, this holds its label until the
        # first paintGL that actually draws it -- at which point that frame's
        # timestamp is recorded as the on-screen onset, then this is cleared.
        self._pending_onset_label: str | None = None
        # Injected by manager.run_task() to the running task's recorder, so
        # paintGL can log the on-screen onset without importing manager (which
        # would be a circular import). None until a task is running.
        self.recorder: TrialRecorder | None = None

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop_video)

        self.show()

    def initializeGL(self) -> None:
        pass

    def resizeGL(self, width: int, height: int) -> None:
        pass

    def closeEvent(self, event) -> None:
        """Handles window close events, stopping updates and threads."""
        self.stop_video()
        event.ignore()

    def load_draw_function(self, draw_fn: Callable | None) -> None:
        """Sets the drawing function. Stops any active rendering.

        Call load_image() or load_video() separately before or after this.

        Args:
            draw_fn (Optional[Callable]): The function to call during paint events.
        """
        self.stop_drawing()
        self._draw_fn = draw_fn
        self._pending_onset_label = "screen_draw"

    def start_drawing(self) -> None:
        """Starts the rendering loop. Call this when you want the stimulus to appear."""
        if self.active:
            return
        self.active = True
        # Fallback label if nothing was loaded since the last show.
        self._pending_onset_label = self._pending_onset_label or "screen_start"
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
        image_path = str(Path(media_directory) / file)
        self.image = QPixmap(image_path)
        self._pending_onset_label = "screen_image_" + file

    def _extract_audio(
        self, video_path: str
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
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

    def load_video(self, file: str, volume_gain: float = 0.1) -> None:
        """Loads a video from the media directory and prepares the playback thread.

        Args:
            file (str): Filename of the video.
            volume_gain (float): Factor applied to the video's audio before
                playback, clamped to [0, 1]. The extracted audio plays at its
                native (often loud) level, so it is scaled down by this factor.
                A value of 0 skips audio entirely (no extraction, no playback).
                Defaults to 0.1.
        """
        self.stop_video()
        volume_gain = min(1.0, max(0.0, volume_gain))
        media_directory = settings.get("MEDIA_DIRECTORY")
        video_path = str(Path(media_directory) / file)
        if volume_gain > 0:
            left, right = self._extract_audio(video_path)
            if left is not None and right is not None:
                left = left * volume_gain
                right = right * volume_gain
                self._audio_left, self._audio_right = left, right
                sound_device.load(left, right)
        self._video_thread = QThread()
        self._video_worker = VideoWorker(video_path)
        self._video_worker.moveToThread(self._video_thread)
        self._video_thread.started.connect(self._video_worker.run)
        # On end-of-file run() returns and emits finished; quit the thread's
        # event loop so it stops cleanly. Cleanup is done synchronously in
        # stop_video() before the next load -- do NOT connect thread.finished to
        # cleanup, or a queued call could delete the next worker/thread after a
        # restart (the object accessed later would be a deleted C++ instance).
        self._video_worker.finished.connect(self._video_thread.quit)
        self._video_thread.start()
        self._pending_onset_label = "screen_video_" + file

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

    def get_video_frame(self) -> QImage | None:
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

        self.gpio.set_on()

        now = time_utils.get_time_monotonic()
        self.elapsed_time = now - self._start_timing
        self.frame += 1

        # First frame that actually draws newly-requested content: record its
        # on-screen onset (aligned with the GPIO sync pulse just set above), then
        # clear so it is recorded once per new content.
        rec = self.recorder
        if self._pending_onset_label is not None and rec is not None:
            try:
                rec.register_event_if_active(
                    self._pending_onset_label, time_utils.now_timestamp()
                )
            except Exception:
                pass
        self._pending_onset_label = None

        try:
            self._draw_fn()
        except Exception:
            pass

        self.gpio.set_off()

    def clear_function(self) -> None:
        """Clears the window by filling it with the background color."""
        with QPainter(self) as painter:
            painter.fillRect(self.rect(), self.background_color)


def get_screen() -> Screen | NullScreen:
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
