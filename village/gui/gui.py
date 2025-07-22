import os
import sys
from pathlib import Path

from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication

from village.classes.abstract_classes import BehaviorWindowBase
from village.classes.enums import ScreenActive
from village.devices.camera import cam_box, cam_corridor
from village.gui.gui_window import GuiWindow
from village.log import log
from village.screen.behavior_window import BehaviorWindow
from village.settings import settings


class Gui:
    def __init__(self) -> None:
        self.q_app = QApplication([])
        self.q_app.setStyle("Fusion")
        self.q_app.setStyleSheet("QLineEdit:disabled {background-color: #f0f0f0;}")

        # put a pretty icon
        iconpath = Path(__file__).parent.parent.parent / "resources/favicon.ico"
        self.q_app.setWindowIcon(QIcon(str(iconpath)))  # Set the icon

        # get the resolution of the primary monitor
        screen = QGuiApplication.screens()[0]
        self.geometry = screen.geometry()

        print(screen.availableGeometry())
        print(screen.geometry())
        print(QGuiApplication.primaryScreen().devicePixelRatio())

        if settings.get("USE_SCREEN") != ScreenActive.OFF:
            self.create_behavior_window()
        else:
            self.behavior_window = BehaviorWindowBase()

        self.gui_window = GuiWindow(self)

    def create_behavior_window(self) -> None:
        # get the resolution of the secondary monitor
        screen = QGuiApplication.screens()[1]
        geometry = screen.geometry()

        print(screen.availableGeometry())
        print(screen.geometry())
        self.behavior_window = BehaviorWindow(geometry)
        settings.set("SCREEN_RESOLUTION", (geometry.width(), geometry.height()))

    def exit_app(self) -> None:
        log.end("VILLAGE")
        cam_corridor.stop_record()
        cam_box.stop_record()
        self.q_app.quit()
        sys.exit()

    def reload_app(self) -> None:
        log.end("VILLAGE")
        cam_corridor.stop_record()
        cam_box.stop_record()
        settings.sync()
        self.q_app.quit()
        python = sys.executable
        os.execv(python, [python] + sys.argv)
