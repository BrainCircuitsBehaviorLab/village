import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication

from village.classes.enums import ScreenActive
from village.classes.null_classes import NullBehaviorWindow
from village.devices.camera import cam_box, cam_corridor
from village.gui.gui_window import GuiWindow
from village.screen.behavior_window import BehaviorWindow
from village.scripts.log import log
from village.settings import settings

if TYPE_CHECKING:
    from village.screen.behavior_window import BehaviorWindow


class Gui:
    def __init__(self) -> None:
        self.q_app = QApplication.instance()
        self.q_app.setStyle("Fusion")
        self.q_app.setStyleSheet("QLineEdit:disabled {background-color: #f0f0f0;}")

        # put a pretty icon
        iconpath = Path(__file__).parent.parent.parent / "resources/favicon.ico"
        self.q_app.setWindowIcon(QIcon(str(iconpath)))  # Set the icon

        # get the resolution of the primary monitor
        screen = QGuiApplication.screens()[0]
        self.geometry = screen.geometry()

        if settings.get("USE_SCREEN") != ScreenActive.OFF:
            self.create_behavior_window()
        else:
            self.behavior_window: BehaviorWindow | NullBehaviorWindow = (
                NullBehaviorWindow()
            )

        self.gui_window = GuiWindow(self)

    def create_behavior_window(self) -> None:
        # get the resolution of the secondary monitor
        screen = QGuiApplication.screens()[1]
        geometry = screen.geometry()

        self.behavior_window = BehaviorWindow(geometry)
        settings.set("SCREEN_RESOLUTION", (geometry.width(), geometry.height()))

    def exit_app(self) -> None:
        log.end("VILLAGE")
        cam_corridor.stop_recording()
        cam_box.stop_recording()
        self.q_app.quit()
        sys.exit()

    def reload_app(self) -> None:
        try:  # can fail if we are changing the system name
            log.end("VILLAGE")
        except Exception:
            pass
        cam_corridor.stop_recording()
        cam_box.stop_recording()
        settings.sync()
        self.q_app.quit()
        python = sys.executable
        os.execv(python, [python] + sys.argv)
