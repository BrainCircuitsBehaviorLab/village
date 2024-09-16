from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QWidget

if TYPE_CHECKING:
    from village.gui.gui import Gui


class BehaviourWindow(QWidget):
    def __init__(self, gui: Gui) -> None:
        super().__init__()
        self.gui = gui
        self.x_displacement: int = gui.primary_width
        self.window_width: int = gui.secondary_width
        self.window_height: int = gui.secondary_height
        rect = QRect(self.x_displacement, 0, self.window_width, self.window_height)
        self.setGeometry(rect)
        self.setFixedSize(QSize(self.window_width, self.window_height))
        self.setWindowTitle("Village2")
        self.setStyleSheet("background-color: black")
        self.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
