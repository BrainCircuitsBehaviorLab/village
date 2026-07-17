import os
import sys
from pathlib import Path

from PyQt5.QtGui import QFont, QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication

from village.devices.camera import cam_box, cam_corridor
from village.devices.sound_device import sound_device
from village.gui.gui_window import GuiWindow
from village.scripts.log import log
from village.settings import settings


class Gui:
    """Main GUI application controller.

    Manages the application lifecycle, including initializing the main window,
    handling secondary screens (behavior window), and managing application exit/reload.
    """

    def __init__(self) -> None:
        """Initializes the GUI application."""
        self.q_app = QApplication.instance()
        self.q_app.setStyle("Fusion")
        QFont.insertSubstitution("DejaVu Sans Condensed", "Cantarell")
        self.q_app.setFont(QFont("DejaVu Sans Condensed", 9))
        self.q_app.setStyleSheet(
            "* { font-family: 'DejaVu Sans Condensed'; font-size: 9pt; }"
            "QLineEdit:disabled { background-color: #f0f0f0; }"
        )

        # put a pretty icon
        iconpath = Path(__file__).parent.parent.parent / "resources/favicon.ico"
        self.q_app.setWindowIcon(QIcon(str(iconpath)))  # Set the icon

        # get the resolution of the primary monitor
        primary_screen = QGuiApplication.screens()[0]
        self.geometry = primary_screen.geometry()

        self.gui_window = GuiWindow(self)

    def exit_app(self) -> None:
        """Exits the application gracefully.

        Stops recordings, logs the end of the session, and quits the Qt application.
        """
        log.end("VILLAGE")
        cam_corridor.stop_recording()
        cam_box.stop_recording()
        sound_device.shutdown()
        self.q_app.quit()
        sys.exit()

    def reload_app(self) -> None:
        """Reloads the application by restarting the process.

        Stops recordings, syncs settings, and re-executes the current script.
        This is useful for applying configuration changes that require a restart.
        """
        try:  # can fail if we are changing the system name
            log.end("VILLAGE")
        except Exception:
            pass
        cam_corridor.stop_recording()
        cam_box.stop_recording()
        sound_device.shutdown()
        settings.sync()
        self.q_app.quit()
        python = sys.executable
        os.execv(python, [python] + sys.argv)
