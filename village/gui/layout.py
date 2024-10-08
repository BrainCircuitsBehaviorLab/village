from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import pandas as pd
from classes.enums import State
from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QTime,
)
from PyQt5.QtGui import QCloseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTimeEdit,
)

from village.data import data
from village.devices.camera import cam_box, cam_corridor
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class Label(QLabel):
    def __init__(
        self, text: str, color: str, right_aligment: bool, bold: bool, description: str
    ) -> None:
        super().__init__(text)
        style = "QLabel {color: " + color
        if bold:
            style += "; font-weight: bold}"
        else:
            style += "}"
        if description != "":
            style += "QToolTip {background-color: white; color: black; font-size: 12px}"
            self.setToolTip(description)
        self.setStyleSheet(style)
        if right_aligment:
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


class LabelImage(QLabel):
    def __init__(self, file) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        image_path = os.path.join(settings.get("APP_DIRECTORY"), "resources", file)
        pixmap = QPixmap(image_path)
        self.setPixmap(pixmap)


class LineEdit(QLineEdit):
    def __init__(self, text: str, action: Callable) -> None:
        super().__init__()
        self.setText(text)
        self.textChanged.connect(action)


class TimeEdit(QTimeEdit):
    def __init__(self, text: str, action: Callable) -> None:
        super().__init__()
        self.setDisplayFormat("HH:mm")
        self.setTime(QTime.fromString(text, "HH:mm"))
        self.timeChanged.connect(action)


class PushButton(QPushButton):
    def __init__(
        self, text: str, color: str, action: Callable, description: str
    ) -> None:
        super().__init__(text)
        style = "QPushButton {background-color: " + color + "; font-weight: bold}"
        if description != "":
            style += "QToolTip {background-color: white; color: black; font-size: 12px}"
            self.setToolTip(description)
        self.setStyleSheet(style)
        self.pressed.connect(action)


class ToggleButton(QPushButton):
    def __init__(
        self,
        key: str,
        possible_values: list[str],
        index: int,
        action: Callable,
        complete_name: bool,
        description: str,
    ) -> None:
        super().__init__()
        self.key = key
        self.possible_values = possible_values
        self.index = index
        self.action = action
        self.complete_name = complete_name
        self.description = description
        self.value = self.possible_values[self.index]
        self.update_style()
        self.pressed.connect(self.on_pressed)

    def update_style(self) -> None:
        if self.complete_name:
            self.setText(self.key + " " + self.value)
        else:
            self.setText(self.value)
        color = "darkgray" if self.value == "OFF" else "lightgray"
        style = "QPushButton {background-color: " + color + "; font-weight: bold}"
        if self.description != "":
            style += "QToolTip {background-color: white; color: black; font-size: 12px}"
            self.setToolTip(self.description)
        self.setStyleSheet(style)

    def on_pressed(self) -> None:
        self.index = (self.index + 1) % len(self.possible_values)
        self.value = self.possible_values[self.index]
        self.update_style()
        self.action(self.value, self.key)


class ComboBox(QComboBox):
    def __init__(
        self, key: str, possible_values: list[str], index: int, action: Callable
    ) -> None:
        super().__init__()
        self.addItems(possible_values)
        self.key = key
        self.possible_values = possible_values
        self.index = index
        self.action = action
        self.value = self.possible_values[self.index]
        self.setCurrentText(self.value)
        self.currentTextChanged.connect(self.handleTextChanged)
        self.update_style()

    def update_style(self) -> None:
        color = "darkgray" if self.value == "OFF" else "lightgray"
        self.setStyleSheet(
            "QComboBox {background-color: " + color + "; font-size: 10px}"
        )

    def handleTextChanged(self, value: str) -> None:
        self.value = value
        self.update_style()
        self.action(self.value, self.key)

    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class Table(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame) -> None:
        super().__init__()
        self.df = df
        self.editable = False
        self.table_view = QTableView()
        self.table_view.setModel(self)

    def rowCount(self, parent=None) -> int:
        return self.df.shape[0]

    def columnCount(self, parent=None) -> int:
        return self.df.shape[1]

    def data(self, index, role=Qt.DisplayRole) -> str | None:
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                return str(self.df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section: int, orientation: Any, role: int) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.df.columns[section])
            elif orientation == Qt.Vertical:
                return str(self.df.index[section])
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole:
            self.df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index) -> Any:
        if self.editable:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def insertRows(self, position, rows=1, index=None) -> bool:
        self.beginInsertRows(index or QModelIndex(), position, position + rows - 1)
        for _ in range(rows):
            new_row = pd.DataFrame([[""] * self.columnCount()], columns=self.df.columns)
            self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.endInsertRows()
        return True

    def add_rows(self, new_df: pd.DataFrame) -> None:
        scroll_position = self.table_view.verticalScrollBar().value()
        scroll_max = self.table_view.verticalScrollBar().maximum()
        rows_before = self.rowCount()
        move_to_bottom = True if scroll_position == scroll_max else False
        self.df = new_df
        self.beginInsertRows(QModelIndex(), rows_before, self.rowCount() - 1)
        self.endInsertRows()

        if move_to_bottom:
            self.table_view.scrollToBottom()


class Layout(QGridLayout):
    def __init__(
        self,
        window: GuiWindow,
        stacked: bool = False,
        rows: int = 50,
        columns: int = 212,
    ) -> None:
        super().__init__()
        self.window = window
        self.stacked = stacked

        if stacked:
            self.width = int(window.window_width / 212 * columns)
            self.height = int(window.window_height / 50 * rows)
            self.num_of_columns = columns
            self.num_of_rows = rows
        else:
            self.width = window.window_width
            self.height = window.window_height
            self.num_of_columns = columns
            self.num_of_rows = rows

        self.column_width = int(self.width / self.num_of_columns)
        self.row_height = int(self.height / self.num_of_rows)

        self.setHorizontalSpacing(0)
        self.setVerticalSpacing(0)

        for i in range(self.num_of_columns):
            self.setColumnMinimumWidth(i, self.column_width)

        for i in range(self.num_of_rows):
            self.setRowMinimumHeight(i, self.row_height)

        if not stacked:
            self.create_common_elements()

    def switch_to_main_layout(self) -> None:
        if data.state == State.SETTINGS:
            data.state = State.WAIT
        self.window.create_main_layout()

    def create_common_elements(self) -> None:
        self.status_label = self.create_and_add_label("", 2, 0, 212, 2, "black")
        self.status_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.update_status_label(force=True)
        self.exit_button = self.create_and_add_button(
            "EXIT",
            0,
            192,
            20,
            2,
            self.exit_button_clicked,
            "Exit the application",
            "lightcoral",
        )
        self.main_button = self.create_and_add_button(
            "MAIN",
            0,
            56,
            20,
            2,
            self.main_button_clicked,
            "Go to the main menu",
        )

        self.monitor_button = self.create_and_add_button(
            "MONITOR",
            0,
            76,
            20,
            2,
            self.monitor_button_clicked,
            "Go to the monitor menu",
        )

        self.tasks_button = self.create_and_add_button(
            "TASKS", 0, 96, 20, 2, self.tasks_button_clicked, "Go to the tasks menu"
        )

        self.data_button = self.create_and_add_button(
            "DATA", 0, 116, 20, 2, self.data_button_clicked, "Go to the data menu"
        )

        self.settings_button = self.create_and_add_button(
            "SETTINGS",
            0,
            136,
            20,
            2,
            self.settings_button_clicked,
            "Go to the setting menu",
        )

    def update_status_label(self, force=False) -> None:
        data.update_cycle()
        if data.update_text() or force:
            self.status_label.setText(data.text)
            cam_box.change = True
            cam_corridor.change = True

    def exit_button_clicked(self) -> None:
        match data.state:
            case State.WAIT | State.SETTINGS | State.ERROR:
                old_state = data.state
                data.state = State.EXIT_GUI
                self.update_status_label()
                text = "Are you sure you want to exit?"
                if data.changing_settings:
                    text += " Changes will not be saved."
                reply = QMessageBox.question(
                    self.window,
                    "EXIT",
                    text,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.window.exit_app()
                else:
                    data.state = old_state
                    self.update_status_label()
            case State.DETECTION | State.ACCESS | State.LAUNCH:
                text = "Wait until the box is empty before exiting the application"
                text = "Subject is being detected. " + text
                QMessageBox.information(
                    self.window,
                    "EXIT",
                    text,
                )
            case (
                State.RUN_ACTION
                | State.CLOSE_DOOR2
                | State.RUN_CLOSED
                | State.OPEN_DOOR2
                | State.RUN_OPENED
                | State.EXIT_UNSAVED
                | State.SAVE_OUTSIDE
                | State.SAVE_INSIDE
                | State.WAIT_EXIT
                | State.EXIT_SAVED
                | State.OPEN_DOOR1
                | State.CLOSE_DOOR1
                | State.RUN_TRAPPED
                | State.SAVE_TRAPPED
                | State.OPEN_DOOR2_STOP
                | State.OPEN_DOORS_STOP
                | State.MANUAL_RUN
            ):
                QMessageBox.information(
                    self.window,
                    "EXIT",
                    "Wait until the box is empty before exiting the application",
                )
            case State.EXIT_GUI:
                pass

    SAVE_OUTSIDE = "task saved, subject is already outside"
    SAVE_INSIDE = "task saved, subject is still inside"
    STOP = "automatic task, manually stopped"
    ERROR = "error occurred, disconnecting rfids and stopping the task"

    def change_layout(self) -> bool:
        return True

    def main_button_clicked(self) -> None:
        if self.change_layout():
            if data.state == State.SETTINGS:
                data.state = State.WAIT
            self.window.create_main_layout()

    def monitor_button_clicked(self) -> None:
        if self.change_layout():
            if data.state == State.SETTINGS:
                data.state = State.WAIT
            self.window.create_monitor_layout()

    def tasks_button_clicked(self) -> None:
        if self.change_layout():
            if data.state == State.SETTINGS:
                data.state = State.WAIT
            self.window.create_tasks_layout()

    def data_button_clicked(self) -> None:
        if self.change_layout():
            if data.state == State.SETTINGS:
                data.state = State.WAIT
            self.window.create_data_layout()

    def settings_button_clicked(self) -> None:
        if self.change_layout():
            if data.state == State.WAIT:
                data.state = State.SETTINGS
                self.window.create_settings_layout()
            else:
                text = "Settings can not be changed if there is a detection in progress"
                text += " or a subject in the box."
                QMessageBox.information(
                    self.window,
                    "SETTINGS",
                    text,
                )

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

    def delete_optional_widgets(self, type: str) -> None:
        for i in reversed(range(self.count())):
            widget = self.itemAt(i).widget()
            if widget.property("type") == type:
                widget.hide()

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
    ) -> Label:

        label = Label(text, color, right_aligment, bold, description)
        label.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(label, row, column, height, width)
        return label

    def create_and_add_image(
        self, row: int, column: int, width: int, height: int, file: str
    ) -> LabelImage:

        path = Path(settings.get("APP_DIRECTORY")) / "resources" / file

        label = LabelImage(path)
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
    ) -> LineEdit:

        line_edit = LineEdit(text, action)
        line_edit.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(line_edit, row, column, height, width)
        return line_edit

    def create_and_add_time_edit(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        action: Callable,
    ) -> TimeEdit:

        time_edit = TimeEdit(text, action)
        time_edit.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(time_edit, row, column, height, width)
        return time_edit

    def create_and_add_button(
        self,
        text: str,
        row: int,
        column: int,
        width: int,
        height: int,
        action: Callable,
        description: str,
        color: str = "lightgray",
    ) -> PushButton:

        button = PushButton(text, color, action, description)
        button.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(button, row, column, height, width)
        return button

    def create_and_add_toggle_button(
        self,
        key: str,
        row: int,
        column: int,
        width: int,
        height: int,
        possible_values: list,
        index: int,
        action: Callable,
        description: str,
        complete_name: bool = False,
    ) -> ToggleButton:

        button = ToggleButton(
            key,
            possible_values,
            index,
            action,
            complete_name,
            description,
        )
        button.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(button, row, column, height, width)
        return button

    def create_and_add_combo_box(
        self,
        key: str,
        row: int,
        column: int,
        width: int,
        height: int,
        possible_values: list,
        index: int,
        action: Callable,
    ) -> ComboBox:

        combo_box = ComboBox(key, possible_values, index, action)
        combo_box.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(combo_box, row, column, height, width)
        return combo_box

    def create_and_add_table(
        self,
        df: pd.DataFrame,
        row: int,
        column: int,
        width: int,
        height: int,
        widths: list[int] = [],
    ) -> Table:

        model = Table(df)
        model.table_view.setFixedSize(
            width * self.column_width, height * self.row_height
        )
        model.table_view.setSelectionBehavior(QTableView.SelectRows)
        model.table_view.setSelectionMode(QTableView.SingleSelection)
        for i in range(len(widths)):
            model.table_view.setColumnWidth(i, widths[i] * self.column_width)

        model.table_view.scrollToBottom()

        self.addWidget(model.table_view, row, column, height, width)

        return model

    def update_gui(self) -> None:
        if not self.stacked:
            self.update_status_label()
