import sys
from pathlib import Path

from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication

from village.app.data import data
from village.app.settings import settings
from village.app.utils import utils
from village.classes.enums import ScreenActive
from village.devices.camera import cam_box, cam_corridor
from village.gui.gui_window import GuiWindow
from village.screen.behaviour_window import BehaviourWindow


class Gui:
    def __init__(self) -> None:
        self.q_app = QApplication([])
        self.q_app.setStyle("Fusion")
        # put a pretty icon
        iconpath = Path(__file__).parent.parent.parent / "resources/favicon.ico"
        self.q_app.setWindowIcon(QIcon(str(iconpath)))  # Set the icon

        # get the resolution of the primary monitor
        screen = QGuiApplication.screens()[0]
        availableGeometry = screen.availableGeometry()
        # use the available geometry but subtract some pixels for the border
        # and the top menu bar
        self.primary_width = availableGeometry.width() - 8
        self.primary_height = availableGeometry.height() - 30
        self.gui_window = GuiWindow(self)

        if settings.get("USE_SCREEN") != ScreenActive.OFF:
            # get the resolution of the secondary monitor
            screen = QGuiApplication.screens()[1]
            availableGeometry = screen.availableGeometry()
            self.secondary_width = availableGeometry.width()
            self.secondary_height = availableGeometry.height()
            self.behaviour_window = BehaviourWindow(self)

        self.q_app.exec()

    def exit_app(self) -> None:
        utils.log("VILLAGE Closed", destinations=[data.events])
        cam_corridor.stop_record()
        cam_box.stop_record()
        self.q_app.quit()
        sys.exit()
