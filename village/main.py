from PyQt5.QtWidgets import QApplication

from village.utils import create_directories
from village.window.window import Window

create_directories()


q_app = QApplication([])
q_app.setStyle("Fusion")
gui = Window(q_app)
q_app.exec()
