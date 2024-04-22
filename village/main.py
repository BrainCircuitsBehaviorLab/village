from PyQt5.QtWidgets import QApplication

from village.gui.gui import Gui
from village.utils import create_directories

create_directories()


q_app = QApplication([])
q_app.setStyle("Fusion")
gui = Gui(q_app)
q_app.exec()
