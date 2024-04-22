from PyQt5.QtCore import QRect, QSize
from PyQt5.QtWidgets import QApplication, QWidget


class BehaviourWindow(QWidget):
    def __init__(self, q_app: QApplication, width: int, height: int):
        super().__init__()
        self.q_app = q_app
        self.setStyleSheet("background-color: black")

        rect = QRect(width, 0, width, height)
        self.setGeometry(rect)
        self.setFixedSize(QSize(width, height))
        self.show()

    def closeEvent(self, event) -> None:
        event.ignore()
