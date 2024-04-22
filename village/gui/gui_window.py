import sys

from PyQt5.QtCore import QObjectCleanupHandler, QRect, QSize
from PyQt5.QtWidgets import QApplication, QWidget

from village.camera import cam_box, cam_corridor
from village.gui.data_layout import DataLayout
from village.gui.main_layout import MainLayout
from village.gui.monitor_layout import MonitorLayout
from village.gui.settings_layout import SettingsLayout
from village.gui.tasks_layout import TasksLayout


class GuiWindow(QWidget):
    def __init__(self, q_app: QApplication, width: int, height: int):
        super().__init__()
        self.q_app = q_app

        self.width = width
        self.height = height
        rect = QRect(0, 0, width, height)
        self.setGeometry(rect)
        self.setFixedSize(QSize(width, height))
        self.setStyleSheet("QToolTip {background-color: white; color: black}")
        self.setStyleSheet("QPushButton {font-weight: bold}")

        self.layout = MainLayout(self)
        self.setLayout(self.layout)
        self.show()

    def create_main_layout(self) -> None:
        self.layout.delete_all_elements()
        QObjectCleanupHandler().add(self.layout)
        self.layout = MainLayout(self)
        self.setLayout(self.layout)

    def create_monitor_layout(self) -> None:
        self.layout.delete_all_elements()
        QObjectCleanupHandler().add(self.layout)
        self.layout = MonitorLayout(self)
        self.setLayout(self.layout)

    def create_tasks_layout(self) -> None:
        self.layout.delete_all_elements()
        QObjectCleanupHandler().add(self.layout)
        self.layout = TasksLayout(self)
        self.setLayout(self.layout)

    def create_data_layout(self) -> None:
        self.layout.delete_all_elements()
        QObjectCleanupHandler().add(self.layout)
        self.layout = DataLayout(self)
        self.setLayout(self.layout)

    def create_settings_layout(self) -> None:
        self.layout.delete_all_elements()
        QObjectCleanupHandler().add(self.layout)
        self.layout = SettingsLayout(self)
        self.setLayout(self.layout)

    def exit_app(self) -> None:
        cam_corridor.stop_record()
        cam_box.stop_record()
        self.q_app.quit()
        sys.exit()
