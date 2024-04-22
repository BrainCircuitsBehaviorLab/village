import os
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QLabel, QMessageBox, QPushButton, QWidget

from village.app_state import app
from village.settings import settings


class Layout(QGridLayout):
    def __init__(self, window: QWidget):
        super().__init__()

        self.window = window
        self.width = window.width
        self.height = window.height
        self.num_of_columns = 212
        self.num_of_rows = 50
        self.column_width = int(self.width / self.num_of_columns)
        self.row_height = int(self.height / self.num_of_rows)
        self.widget_height = 2
        self.top_row = 0

        self.button_width = 20
        self.label_width = 30

        self.first_menu_button = 56
        self.last_menu_button = 192

        self.setHorizontalSpacing(0)
        self.setVerticalSpacing(0)

        for i in range(self.num_of_columns):
            self.setColumnMinimumWidth(i, self.column_width)

        for i in range(self.num_of_rows):
            self.setRowMinimumHeight(i, self.row_height)

        self.create_common_elements()

    def create_common_elements(self) -> None:
        text = (
            "SYSTEM STATE: "
            + app.state.name
            + " ("
            + app.state.description
            + ")     //////     "
            + "SUBJECT: "
            + app.subject.name
            + "     /////     "
            + "TASK: "
            + app.task.name
        )
        self.status_label = self.create_and_add_label(
            text=text, row=2, column=56, width=100, height=2, color="black"
        )
        self.exit_button = self.create_and_add_button(
            text="EXIT",
            row=0,
            column=192,
            width=20,
            height=2,
            color="lightcoral",
            action=self.exit_button_clicked,
        )
        self.main_button = self.create_and_add_button(
            text="MAIN",
            row=0,
            column=56,
            width=20,
            height=2,
            color="white",
            action=self.main_button_clicked,
        )

        self.monitor_button = self.create_and_add_button(
            text="MONITOR",
            row=0,
            column=76,
            width=20,
            height=2,
            color="white",
            action=self.monitor_button_clicked,
        )

        self.tasks_button = self.create_and_add_button(
            text="TASKS",
            row=0,
            column=96,
            width=20,
            height=2,
            color="white",
            action=self.tasks_button_clicked,
        )

        self.data_button = self.create_and_add_button(
            text="DATA",
            row=0,
            column=116,
            width=20,
            height=2,
            color="white",
            action=self.data_button_clicked,
        )

        self.settings_button = self.create_and_add_button(
            text="SETTINGS",
            row=0,
            column=136,
            width=20,
            height=2,
            color="white",
            action=self.settings_button_clicked,
        )

    def exit_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "EXIT",
            "Are you sure you want to exit?",
            QMessageBox.Yes,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.window.exit_app()

    def change_layout(self) -> bool:
        return True

    def main_button_clicked(self) -> None:
        if self.change_layout():
            self.window.create_main_layout()

    def monitor_button_clicked(self) -> None:
        if self.change_layout():
            self.window.create_monitor_layout()

    def tasks_button_clicked(self) -> None:
        if self.change_layout():
            self.window.create_tasks_layout()

    def data_button_clicked(self) -> None:
        if self.change_layout():
            self.window.create_data_layout()

    def settings_button_clicked(self) -> None:
        if self.change_layout():
            self.window.create_settings_layout()

    def closeEvent(self, event) -> None:
        event.ignore()

    def delete_optional_widgets(self, type):
        for i in reversed(range(self.count())):
            widget = self.itemAt(i).widget()
            if widget.property("type") == type:
                widget.hide()

    def delete_all_elements(self):
        for i in reversed(range(self.count())):
            layoutItem = self.itemAt(i)
            if layoutItem is not None:
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.deleteLater()

    def create_and_add_label(
        self, text: str, row: int, column: int, width: int, height: int, color: str
    ) -> QLabel:
        label = QLabel(text)
        color = "color: " + color
        label.setStyleSheet(color)
        label.setStyleSheet("font-weight: bold")
        label.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(label, row, column, height, width)
        return label

    def create_and_add_button(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        color: str,
        action: Callable,
    ) -> QPushButton:
        button = QPushButton(text)
        color = "QPushButton {background-color: " + color + "}"
        button.setStyleSheet(color)
        button.setFixedSize(width * self.column_width, height * self.row_height)
        button.clicked.connect(action)
        self.addWidget(
            button,
            row,
            column,
            height,
            width,
        )
        return button

    def create_and_add_image(
        self, row: int, column: int, width: int, height: int, file: str
    ) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        image_path = os.path.join(settings.get("APP_DIRECTORY"), "resources", file)
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(label, row, column, height, width)
        return label

    def disable(self, button: QPushButton) -> None:
        button.setDisabled(True)
        button.setStyleSheet("QPushButton {background-color: lightblue}")
