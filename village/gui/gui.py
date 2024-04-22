from PyQt5.QtGui import QGuiApplication

from village.gui.behaviour_window import BehaviourWindow
from village.gui.gui_window import GuiWindow
from village.settings import settings


# TODO: need explanation of this class and how
# it interacts with main.py, settings, and screens
class Gui:
    def __init__(self, app):
        self.app = app
        # get the resolution of the primary monitor
        screen = QGuiApplication.screens()[0]
        availableGeometry = screen.availableGeometry()
        # use the available geometry but subtract some pixels for the border
        # and the top menu bar
        self.primary_width = availableGeometry.width() - 8
        self.primary_height = availableGeometry.height() - 30
        self.gui_window = GuiWindow(app, self.primary_width, self.primary_height)

        if settings.get("USE_SCREEN") != "No Screen":
            # get the resolution of the secondary monitor
            screen = QGuiApplication.screens()[1]
            availableGeometry = screen.availableGeometry()
            self.secondary_width = availableGeometry.width()
            self.secondary_height = availableGeometry.height()
            self.behaviour_window = BehaviourWindow(
                app, self.secondary_width, self.secondary_height
            )
