from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
)

from village.app_state import app
from village.settings import settings

if TYPE_CHECKING:
    from village.window.gui_window import GuiWindow


class ComboBox(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("QComboBox {font-size: 10px}")
        self.currentIndexChanged.connect(self.update_style)
        self.update_style()

    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()

    def update_style(self) -> None:
        if self.currentText() in ("No", "No Screen"):
            self.setStyleSheet("QComboBox {background-color: lightcoral}")
        else:
            self.setStyleSheet("QComboBox {background-color: lightgreen}")


class Button(QPushButton):
    def __init__(self, title: str, default_on: bool, action: Callable) -> None:
        super().__init__(title)
        self.setCheckable(True)
        self.isChecked = default_on
        self.action = action
        self.title = title
        self.update_style()
        self.pressed.connect(self.on_pressed)

    def update_style(self):
        if self.isChecked:
            self.setText(self.title + " ON")
            self.setStyleSheet(
                "QPushButton {background-color: lightgreen; font-weight: bold}"
            )
        else:
            self.setText(self.title + " OFF")
            self.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}"
            )

    def on_pressed(self):
        self.isChecked = not self.isChecked
        self.update_style()
        self.action()


class Layout(QGridLayout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__()

        self.window = window
        self.width = window.width
        self.height = window.height
        self.num_of_columns = 212
        self.num_of_rows = 50
        self.column_width = int(self.width / self.num_of_columns)
        self.row_height = int(self.height / self.num_of_rows)

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
        self.status_label = self.create_and_add_label(text, 2, 56, 100, 2, "black")
        self.exit_button = self.create_and_add_button(
            "EXIT", 0, 192, 20, 2, "lightcoral", self.exit_button_clicked
        )
        self.main_button = self.create_and_add_button(
            "MAIN", 0, 56, 20, 2, "white", self.main_button_clicked
        )

        self.monitor_button = self.create_and_add_button(
            "MONITOR", 0, 76, 20, 2, "white", self.monitor_button_clicked
        )

        self.tasks_button = self.create_and_add_button(
            "TASKS", 0, 96, 20, 2, "white", self.tasks_button_clicked
        )

        self.data_button = self.create_and_add_button(
            "DATA", 0, 116, 20, 2, "white", self.data_button_clicked
        )

        self.settings_button = self.create_and_add_button(
            "SETTINGS", 0, 136, 20, 2, "white", self.settings_button_clicked
        )

    def exit_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "EXIT",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
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

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

    def delete_optional_widgets(self, type: str) -> None:
        for i in reversed(range(self.count())):
            widget = self.itemAt(i).widget()
            if widget.property("type") == type:
                widget.hide()

    def delete_all_elements(self) -> None:
        for i in reversed(range(self.count())):
            layoutItem = self.itemAt(i)
            if layoutItem is not None:
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.deleteLater()

    def create_and_add_label(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        color: str,
        right_aligment: bool = False,
        bold: bool = True,
        description: str = "",
    ) -> QLabel:

        label = QLabel(text)
        if bold:
            label.setStyleSheet("QLabel {color: " + color + "; font-weight: bold}")
        else:
            label.setStyleSheet("QLabel {color: " + color + "}")
        if right_aligment:
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if description != "":
            label.setToolTip(description)
            label.setStyleSheet("QToolTip {background-color: white; color: black}")
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
        button.setStyleSheet(
            "QPushButton {background-color: " + color + "; font-weight: bold}"
        )
        button.setFixedSize(width * self.column_width, height * self.row_height)
        button.pressed.connect(action)
        self.addWidget(
            button,
            row,
            column,
            height,
            width,
        )
        return button

    def create_and_add_button_toggle(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        default_on: bool,
        action: Callable,
    ) -> Button:

        text = text + " ON" if default_on else text + " OFF"
        button = Button(text, default_on, action)
        button.setFixedSize(width * self.column_width, height * self.row_height)
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

    def create_and_add_line_edit(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        action: Callable,
    ) -> QLineEdit:

        line_edit = QLineEdit(text)
        line_edit.setFixedSize(width * self.column_width, height * self.row_height)
        line_edit.textChanged.connect(action)
        self.addWidget(
            line_edit,
            row,
            column,
            height,
            width,
        )
        return line_edit

    def create_and_add_combo_box(
        self,
        text: str,
        possible_values: list,
        row: int,
        column: int,
        width: int,
        height: int,
        action: Callable,
    ) -> ComboBox:

        combo_box = ComboBox()
        combo_box.setCurrentText(text)
        combo_box.addItems(possible_values)
        combo_box.setCurrentText(text)
        combo_box.setFixedSize(width * self.column_width, height * self.row_height)
        combo_box.currentTextChanged.connect(action)
        combo_box.update_style()
        self.addWidget(
            combo_box,
            row,
            column,
            height,
            width,
        )
        return combo_box

    def disable(self, button: QPushButton) -> None:
        button.setDisabled(True)
        button.setStyleSheet(
            "QPushButton {background-color: lightblue; font-weight: bold}"
        )
