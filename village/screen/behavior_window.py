from __future__ import annotations

from typing import Callable, Optional

import gpiod
from gpiod.line import Direction, Value
from PyQt5.QtCore import QRect, Qt, QThread
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtWidgets import QOpenGLWidget

from village.manager import manager
from village.screen.video_worker import VideoWorker
from village.scripts.time_utils import time_utils


class BehaviorWindow(QOpenGLWidget):
    def __init__(self, geometry: QRect) -> None:
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

        self.show()

    def _init_gpio(self) -> None:
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
        event.ignore()

    def load_draw_function(self, draw_fn: Optional[Callable]) -> None:
        self.stop_drawing()
        self._draw_fn = draw_fn

    def start_drawing(self) -> None:
        self.active = True
        self._start_timing = time_utils.get_time()
        if not self._swap_connected:
            self.frameSwapped.connect(self.update, Qt.ConnectionType.UniqueConnection)
            self._swap_connected = True
        self.update()

    def stop_drawing(self) -> None:
        self.active = False
        if self._swap_connected:
            try:
                self.frameSwapped.disconnect(self.update)
            except Exception:
                pass
            self._swap_connected = False
        self.frame = 0
        self.elapsed_time = 0.0
        self.update()

    def start_video(self, path: str) -> None:
        self.stop_video()
        self._video_thread = QThread()
        self._video_worker = VideoWorker(path)
        self._video_worker.moveToThread(self._video_thread)
        self._video_thread.started.connect(self._video_worker.run)
        self._video_thread.start()

    def stop_video(self) -> None:
        if self._video_worker:
            self._video_worker.stop()
        if self._video_thread:
            self._video_thread.quit()
            self._video_thread.wait(500)
        self._video_worker = None
        self._video_thread = None

    def get_video_frame(self) -> Optional[QImage]:
        if not self._video_worker:
            return None
        return self._video_worker.get_latest_qimage()

    def paintGL(self) -> None:
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
        now = time_utils.get_time()
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
        with QPainter(self) as painter:
            # clean the window
            painter.fillRect(manager.behavior_window.rect(), self.background_color)
