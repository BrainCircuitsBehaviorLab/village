from PyQt5.QtCore import QRect, QSize
from PyQt5.QtWidgets import QWidget


class BehaviourWindow(QWidget):
    def __init__(self, app, width, height):
        super().__init__()
        self.app = app
        self.setStyleSheet("background-color: black")

        rect = QRect(width, 0, width, height)
        self.setGeometry(rect)
        self.setFixedSize(QSize(width, height))
        self.show()

    def closeEvent(self, event):
        event.ignore()
