from __future__ import annotations

import os
from typing import Callable, Optional

import gpiod
from gpiod.line import Direction, Value
from PyQt5.QtCore import QRect, Qt, QThread
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QOpenGLWidget

from village.manager import manager
from village.screen.video_worker import VideoWorker
from village.scripts.time_utils import time_utils
from village.settings import settings


class BehaviorWindow(QOpenGLWidget):
    """Window for displaying stimuli, video monitoring, and visual behavior tasks.

    This class handles the rendering loop, GPIO synchronization (for timestamps),
    and displaying images or video streams.
    """

    def __init__(self, geometry: QRect) -> None:
        """Initializes the BehaviorWindow.

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

        self.active: bool = False
        self._draw_fn: Optional[Callable] = None

        # timing
        self._start_timing: float = 0.0

        # render loop
        self._swap_connected: bool = False

        # persistent GPIO
        self._gpio_request = None
        self._gpio_line_offset = 26
        self._init_gpio()

        # video
        self._video_thread: Optional[QThread] = None
        self._video_worker: Optional[VideoWorker] = None

        # timing
        self.frame = 0
        self.elapsed_time = 0.0

        # background color
        self.background_color = QColor("black")

        # images or videos
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
        """Initializes OpenGL resources (placeholder)."""
        pass

    def resizeGL(self, width: int, height: int) -> None:
        """Handles window resize events (placeholder).

        Args:
            width (int): New width.
            height (int): New height.
        """
        pass

    def closeEvent(self, event) -> None:
        """Handles window close events, stopping updates and threads."""
        self.stop_video()
        event.ignore()

    def load_draw_function(
        self,
        draw_fn: Optional[Callable],
        image: str | None = None,
        video: str | None = None,
    ) -> None:
        """Sets the drawing function and optionally loads background media.

        Args:
            draw_fn (Optional[Callable]): The function to call during paint events.
            image (str | None, optional): Filename of an image to load. Defaults to None.
            video (str | None, optional): Filename of a video to load. Defaults to None.
        """
        self.stop_drawing()
        if image is not None:
            self.load_image(image)
        elif video is not None:
            self.load_video(video)
        self._draw_fn = draw_fn

    def start_drawing(self) -> None:
        """Starts the rendering loop and video playback with synchronization."""
        self.active = True
        self._start_timing = time_utils.get_time_monotonic()
        if not self._swap_connected:
            self.frameSwapped.connect(self.update, Qt.ConnectionType.UniqueConnection)
            self._swap_connected = True
        self.start_video()
        self.update()

    def stop_drawing(self) -> None:
        """Stops the rendering loop and video playback."""
        self.active = False
        if self._swap_connected:
            try:
                self.frameSwapped.disconnect(self.update)
            except Exception:
                pass
            self._swap_connected = False
        self.frame = 0
        self.elapsed_time = 0.0
        self.stop_video()
        self.update()

    def load_image(self, file: str) -> None:
        """Loads an image from the media directory.

        Args:
            file (str): Filename of the image.
        """
        media_directory = settings.get("MEDIA_DIRECTORY")
        image_path = os.path.join(media_directory, file)
        self.image = QPixmap(image_path)

    def load_video(self, file: str) -> None:
        """Loads a video from the media directory and prepares the playback thread.

        Args:
            file (str): Filename of the video.
        """
        self.stop_video()
        media_directory = settings.get("MEDIA_DIRECTORY")
        video_path = os.path.join(media_directory, file)
        self._video_thread = QThread(self)
        self._video_worker = VideoWorker(video_path)
        self._video_worker.moveToThread(self._video_thread)
        self._video_thread.started.connect(self._video_worker.run)
        self._video_thread.finished.connect(self._on_video_thread_finished)

    def start_video(self) -> None:
        """Starts the video playback thread."""
        if self._video_thread is not None and not self._video_thread.isRunning():
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
        """Main rendering loop called by OpenGL widget update.

        Handles clearing, GPIO signaling, timing updates, and executing the
        custom draw function.
        """
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

        # timing/frame
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
            # clean the window
            painter.fillRect(manager.behavior_window.rect(), self.background_color)

