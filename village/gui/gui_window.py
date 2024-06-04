from __future__ import annotations

from typing import TYPE_CHECKING

from app.data import data
from app.utils import utils
from PyQt5.QtCore import QObjectCleanupHandler, QRect, QSize
from PyQt5.QtWidgets import QWidget

from village.gui.data_layout import DataLayout
from village.gui.layout import Layout
from village.gui.main_layout import MainLayout
from village.gui.monitor_layout import MonitorLayout
from village.gui.settings_layout import SettingsLayout
from village.gui.tasks_layout import TasksLayout

if TYPE_CHECKING:
    from village.gui.gui import Gui


class GuiWindow(QWidget):
    def __init__(self, gui: Gui) -> None:
        super().__init__()
        self.gui = gui
        self.window_width: int = gui.primary_width
        self.window_height: int = gui.primary_height
        rect = QRect(0, 0, self.window_width, self.window_height)
        self.setGeometry(rect)
        self.setFixedSize(QSize(self.window_width, self.window_height))
        self.setWindowTitle("Village")
        self.layout: Layout = MainLayout(self)
        self.setLayout(self.layout)
        self.show()

    def create_main_layout(self) -> None:
        utils.delete_all_elements(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = MainLayout(self)
        self.setLayout(self.layout)

    def create_monitor_layout(self) -> None:
        utils.delete_all_elements(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = MonitorLayout(self, data.events.df)
        self.setLayout(self.layout)

    def create_tasks_layout(self) -> None:
        utils.delete_all_elements(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = TasksLayout(self)
        self.setLayout(self.layout)

    def create_data_layout(self) -> None:
        utils.delete_all_elements(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = DataLayout(self, data.events.df)
        self.setLayout(self.layout)

    def create_settings_layout(self) -> None:
        utils.delete_all_elements(self.layout)
        QObjectCleanupHandler().add(self.layout)
        self.layout = SettingsLayout(self)
        self.setLayout(self.layout)

    def exit_app(self) -> None:
        self.gui.exit_app()
