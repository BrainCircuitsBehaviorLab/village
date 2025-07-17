import time
from typing import Callable, Optional

import gpiod
from gpiod.line import Direction, Value
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QOpenGLWidget

from village.manager import manager


class BehaviorWindow(QOpenGLWidget):
    def __init__(self, gui) -> None:
        super().__init__()
        self.gui = gui
        self.x_displacement = gui.primary_width
        self.window_width = gui.secondary_width
        self.window_height = gui.secondary_height
        self.setGeometry(
            QRect(self.x_displacement, 0, self.window_width, self.window_height)
        )
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Village2")
        self.setStyleSheet("background-color: black")
        self.active: int = 0  # 0 inactive, 1 active, 2 cleaning
        self.draw_function: Optional[Callable] = None

        # minimum latency OpenGL configuration
        self.setUpdateBehavior(QOpenGLWidget.NoPartialUpdate)

        self.start_timing: float = 0.0

        self.show()

    def initializeGL(self) -> None:
        pass

    def closeEvent(self, event) -> None:
        event.ignore()

    def set_active(self, value: bool) -> None:
        self.active = value
        self.start_timing = time.time()
        self.update()

    def set_draw_function(self, draw_fn: Callable) -> None:
        self.draw_function = draw_fn

    def paintGL(self) -> None:
        if not self.active or self.draw_function is None:
            self.clear_function()
            manager.stimulus_timing = 0
            manager.stimulus_frame = 0
        else:
            line_offset = 26
            with gpiod.request_lines(
                "/dev/gpiochip0",
                consumer="toggle_value",
                config={
                    line_offset: gpiod.LineSettings(
                        direction=Direction.OUTPUT, output_value=Value.ACTIVE
                    )
                },
            ) as request:
                request.set_value(line_offset, Value.ACTIVE)

                current_time = time.time()
                manager.stimulus_timing = current_time - self.start_timing
                manager.stimulus_frame += 1
                self.draw_function()
                self.update()

                request.set_value(line_offset, Value.INACTIVE)

    def resizeGL(self, width: int, height: int) -> None:
        pass

    def clear_function(self) -> None:
        with QPainter(self) as painter:
            # clean the window
            painter.fillRect(manager.behavior_window.rect(), QColor("black"))
