from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QEvent, QObjectCleanupHandler, QTimer
from PyQt5.QtWidgets import QWidget

from village.gui.data_layout import DataLayout
from village.gui.main_layout import MainLayout
from village.gui.monitor_layout import MonitorLayout
from village.gui.settings_layout import SettingsLayout
from village.gui.sound_calibration_layout import SoundCalibrationLayout
from village.gui.tasks_layout import TasksLayout
from village.gui.water_calibration_layout import WaterCalibrationLayout
from village.scripts import utils
from village.scripts.time_utils import time_utils
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui import Gui
    from village.gui.layout import Layout


class GuiWindow(QWidget):
    """The main window widget for the Village application.

    Handles the switching between different layouts (Main, Monitor, Tasks, Data,
    Calibration, Settings) and manages the main update loop via a QTimer.
    """

    def __init__(self, gui: Gui) -> None:
        """Initializes the GuiWindow.

        Args:
            gui (Gui): The parent Gui controller instance.
        """
        super().__init__()
        self.gui = gui
        self.window_width: int = gui.geometry.width()
        self.window_height: int = gui.geometry.height() - 33
        self.setGeometry(0, 0, self.window_width, self.window_height)
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Village")
        self.layout: Layout = MainLayout(self, first_draw=True)
        self.setLayout(self.layout)
        self.screensave_time: int = int(settings.get("SCREENSAVE_TIME"))
        self.update_chrono = time_utils.Chrono()
        self.update_timer = QTimer()
        self.update_timer.setInterval(settings.get("UPDATE_TIME_TABLE") * 1000)
        self.update_timer.timeout.connect(self.update_gui)
        self.update_timer.start()
        self.gui.q_app.installEventFilter(self)
        self.show()

    def eventFilter(self, source, event) -> bool:
        """Filters events to detect user activity and reset the screensaver timer.

        Args:
            source: The object that triggered the event.
            event: The event object.

        Returns:
            bool: True if event is handled, False otherwise.
        """
        if event.type() == QEvent.MouseButtonPress:
            self.update_chrono.reset()
        return super().eventFilter(source, event)

    def create_main_layout(self) -> None:
        """Switches the current view to the Main Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = MainLayout(self)
        self.setLayout(self.layout)

    def create_monitor_layout(self) -> None:
        """Switches the current view to the Monitor Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = MonitorLayout(self)
        self.setLayout(self.layout)

    def create_tasks_layout(self) -> None:
        """Switches the current view to the Tasks Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = TasksLayout(self)
        self.setLayout(self.layout)

    def create_data_layout(self) -> None:
        """Switches the current view to the Data Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = DataLayout(self)
        self.setLayout(self.layout)

    def create_water_calibration_layout(self) -> None:
        """Switches the current view to the Water Calibration Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = WaterCalibrationLayout(self)
        self.setLayout(self.layout)

    def create_sound_calibration_layout(self) -> None:
        """Switches the current view to the Sound Calibration Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = SoundCalibrationLayout(self)
        self.setLayout(self.layout)

    def create_settings_layout(self) -> None:
        """Switches the current view to the Settings Layout."""
        utils.delete_all_elements_from_layout(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = SettingsLayout(self)
        self.setLayout(self.layout)

    def exit_app(self) -> None:
        """Requests application exit from the parent controller."""
        self.gui.exit_app()

    def reload_app(self) -> None:
        """Requests application reload from the parent controller."""
        self.gui.reload_app()

    def update_gui(self) -> None:
        """Periodic update method called by the timer.

        Updates the current layout and checks the screensaver timer.
        """
        self.layout.check_errors()
        self.layout.update_gui()
        self.check_update_chrono()

    def check_update_chrono(self) -> None:
        """Checks if the inactivity timeout has been reached.

        If so, automatically returns to the Main Menu.
        """
        if self.update_chrono.get_seconds() > self.screensave_time:
            self.layout.main_button_clicked(auto=True)

