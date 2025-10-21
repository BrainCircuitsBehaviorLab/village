from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from classes.enums import State
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QCloseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

from village.classes.enums import DataTable
from village.manager import manager
from village.scripts.log import log
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class Label(QLabel):
    def __init__(
        self,
        text: str,
        color: str,
        right_aligment: bool,
        bold: bool,
        description: str,
        background: str,
    ) -> None:
        super().__init__(text)
        style = "QLabel {color: " + color
        if bold:
            style += "; font-weight: bold"
        if background == "":
            style += "}"
        else:
            style += "; background-color: " + background + "}"
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
        color: str = "lightgray",
    ) -> None:
        super().__init__()
        self.key = key
        self.possible_values = possible_values
        self.index = index
        self.action = action
        self.complete_name = complete_name
        self.description = description
        self.value = self.possible_values[self.index]
        self.color = color
        self.update_style()
        self.pressed.connect(self.on_pressed)

    def update_style(self) -> None:
        if self.complete_name:
            self.setText(self.key + " " + self.value)
        else:
            self.setText(self.value)
        color = "darkgray" if self.value == "OFF" else self.color
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
        try:
            self.value = self.possible_values[self.index]
        except Exception:
            self.index = 0
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


class Layout(QGridLayout):
    def __init__(
        self,
        window: GuiWindow,
        stacked: bool = False,
        rows: int = 51,
        columns: int = 200,
    ) -> None:
        super().__init__()
        self.window = window
        self.stacked = stacked

        if stacked:
            self.width = int(window.window_width / 200 * columns)  # 1600 / 200 = 8
            self.height = int(window.window_height / 51 * rows)  # 867 / 51 = 17
            self.num_of_columns = columns
            self.num_of_rows = rows

        else:
            self.width = window.window_width
            self.height = window.window_height
            self.num_of_columns = columns
            self.num_of_rows = rows

        self.setContentsMargins(0, 0, 0, 0)

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

    def create_common_elements(self) -> None:
        self.status_label = self.create_and_add_label(
            "", 3, 0, 200, 2, "white", background="black"
        )
        # self.status_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        size = 18

        self.main_button = self.create_and_add_button(
            "MAIN",
            1,
            0,
            size,
            2,
            self.main_button_clicked,
            "Go to the main menu",
        )

        self.monitor_button = self.create_and_add_button(
            "MONITOR",
            1,
            size,
            size,
            2,
            self.monitor_button_clicked,
            "Go to the monitor menu",
        )

        self.tasks_button = self.create_and_add_button(
            "TASKS",
            1,
            2 * size,
            size,
            2,
            self.tasks_button_clicked,
            "Go to the tasks menu",
        )

        self.data_button = self.create_and_add_button(
            "DATA",
            1,
            3 * size,
            size,
            2,
            self.data_button_clicked,
            "Go to the data menu",
        )

        self.water_calibration_button = self.create_and_add_button(
            "WATER CALIBRATION",
            1,
            4 * size,
            size,
            2,
            self.water_calibration_button_clicked,
            "Go to the water calibration menu",
        )

        self.sound_calibration_button = self.create_and_add_button(
            "SOUND CALIBRATION",
            1,
            5 * size,
            size,
            2,
            self.sound_calibration_button_clicked,
            "Go to the sound calibration menu",
        )

        self.settings_button = self.create_and_add_button(
            "SETTINGS",
            1,
            6 * size,
            size,
            2,
            self.settings_button_clicked,
            "Go to the setting menu",
        )

        self.online_plots_button = self.create_and_add_button(
            "ONLINE PLOTS",
            1,
            158,
            14,
            2,
            self.show_online_plots_clicked,
            "Show the online plots when a task is running",
            "powderblue",
        )

        self.stop_button = self.create_and_add_button(
            "",
            1,
            172,
            14,
            2,
            self.stop_button_clicked,
            "Stop a running task",
            "lightcoral",
        )

        self.exit_button = self.create_and_add_button(
            "EXIT",
            1,
            186,
            14,
            2,
            self.exit_button_clicked,
            "Exit the application",
            "lightcoral",
        )

        self.update_status_label_buttons()

    def update_status_label_buttons(self) -> None:
        manager.update_text()
        self.status_label.setText(manager.text)
        if manager.state.can_stop_task():
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop a running task")
            self.stop_button.setEnabled(True)
            self.online_plots_button.setEnabled(True)
        elif manager.state.can_go_to_wait():
            self.stop_button.setText("GO TO WAIT STATE")
            text = (
                "If the systems thinks there is a subject in the corridor or the "
                + "box, but there isn't, you can force going to the WAIT state."
            )
            self.stop_button.setToolTip(text)
            self.stop_button.setEnabled(True)
        elif manager.state.can_stop_syncing():
            self.stop_button.setText("STOP SYNC")
            text = (
                "Stop data synchronization. Sync will resume automatically after "
                + "the next session."
            )
            self.stop_button.setToolTip(text)
            self.stop_button.setEnabled(True)
            self.online_plots_button.setEnabled(False)
        else:
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop a running task")
            self.stop_button.setEnabled(False)
            self.online_plots_button.setEnabled(False)

    def exit_button_clicked(self) -> None:
        if manager.table == DataTable.SUBJECTS:
            try:
                if self.page1Layout.df["name"].duplicated().any():
                    text = "There are repeated names in the subjects table."
                    QMessageBox.information(self.window, "WARNING", text)
                    return
                elif self.page1Layout.df["name"].str.strip().eq("").any():
                    text = "There are empty names in the subjects table."
                    QMessageBox.information(self.window, "WARNING", text)
                    return
            except Exception:
                pass

        if manager.state.can_exit():
            old_state = manager.state
            manager.state = State.EXIT_GUI
            self.update_status_label_buttons()
            text = "Are you sure you want to exit?"
            if manager.changing_settings:
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
                manager.state = old_state
                self.update_status_label_buttons()
        else:
            text = "Wait until the box is empty or synchronization is complete"
            text += " before exiting the application"
            QMessageBox.information(
                self.window,
                "EXIT",
                text,
            )

    def change_layout(self, auto: bool = False) -> bool:
        return True

    def main_button_clicked(self, auto: bool = False) -> None:
        if self.change_layout(auto=auto):
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            self.close_online_plot_window()
            self.window.create_main_layout()

    def monitor_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            manager.detection_change = True
            self.close_online_plot_window()
            self.window.create_monitor_layout()

    def tasks_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state in [State.WAIT, State.MANUAL_MODE]:
                manager.state = State.MANUAL_MODE
                manager.reset_subject_task_training()
                self.close_online_plot_window()
                self.window.create_tasks_layout()
            else:
                text = (
                    "Tasks cannot start while a subject is in the box, a detection is "
                    + "ongoing, or data is syncing."
                )
                QMessageBox.information(
                    self.window,
                    "SETTINGS",
                    text,
                )

    def data_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            self.close_online_plot_window()
            self.window.create_data_layout()

    def water_calibration_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state in [State.WAIT, State.MANUAL_MODE]:
                manager.state = State.MANUAL_MODE
                manager.reset_subject_task_training()
                self.close_online_plot_window()
                self.window.create_water_calibration_layout()
            else:
                text = (
                    "Calibration is not available while a subject is in the box, a "
                    + "detection is ongoing, or data is syncing."
                )
                QMessageBox.information(
                    self.window,
                    "CALIBRATION",
                    text,
                )

    def sound_calibration_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state in [State.WAIT, State.MANUAL_MODE]:
                manager.state = State.MANUAL_MODE
                manager.reset_subject_task_training()
                self.close_online_plot_window()
                self.window.create_sound_calibration_layout()
            else:
                text = (
                    "Calibration is not available while a subject is in the box, a "
                    + "detection is ongoing, or data is syncing."
                )
                QMessageBox.information(
                    self.window,
                    "CALIBRATION",
                    text,
                )

    def settings_button_clicked(self) -> None:
        if self.change_layout():
            if manager.state in [State.WAIT, State.MANUAL_MODE]:
                manager.state = State.MANUAL_MODE
                manager.reset_subject_task_training()
                self.close_online_plot_window()
                self.window.create_settings_layout()
            else:
                text = (
                    "Settings can not be changed while a subject is in the box, a "
                    + "detection is ongoing, or data is syncing."
                )
                QMessageBox.information(
                    self.window,
                    "SETTINGS",
                    text,
                )

    def stop_button_clicked(self) -> None:
        if manager.state.can_stop_task():
            if manager.state == State.RUN_MANUAL:
                log.info("Task manually stopped.", subject=manager.subject.name)
                manager.state = State.SAVE_MANUAL
            else:
                log.info(
                    "Task manually stopped. Disconnecting RFID Reader.",
                    subject=manager.subject.name,
                )
                manager.state = State.OPEN_DOOR2_STOP
                log.info("Going to OPEN_DOOR2_STOP State")
        elif manager.state.can_go_to_wait():
            manager.getting_weights = False
            manager.state = State.WAIT
            log.info("Going to WAIT State")
        elif manager.state.can_stop_syncing():
            manager.after_session.cancel_event.set()
        self.update_gui()

    def close_online_plot_window(self) -> None:
        try:
            self.plot_dialog.close()
        except Exception:
            pass

    def show_online_plots_clicked(self) -> None:
        try:
            manager.online_plot.update_canvas(manager.task.session_df)
        except Exception:
            log.error(
                "Error in online plot",
                subject=manager.subject.name,
                exception=traceback.format_exc(),
            )

        if not manager.online_plot.active:
            manager.online_plot.active = True
            manager.online_plot.update_canvas(manager.task.session_df.copy())
            geom = (
                self.column_width * 10,
                self.row_height * 5,
                self.column_width * 62,
                self.row_height * 20,
            )
            self.plot_dialog = OnlinePlotDialog()
            self.plot_dialog.setGeometry(*geom)
            self.plot_dialog.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

    def delete_optional_widgets(self, type: str) -> None:
        for i in reversed(range(self.count())):
            widget = self.itemAt(i).widget()
            if widget is not None:
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
        background: str = "",
    ) -> Label:

        label = Label(text, color, right_aligment, bold, description, background)
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
        color: str = "lightgray",
    ) -> ToggleButton:

        button = ToggleButton(
            key,
            possible_values,
            index,
            action,
            complete_name,
            description,
            color,
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

    def update_gui(self) -> None:
        pass

    def check_errors(self) -> None:
        if manager.error_in_manual_task:
            text = "Error in manual task"
            QMessageBox.information(self.window, "ERROR", text)
            manager.error_in_manual_task = False


class OnlinePlotDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Online Plots")
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(manager.online_plot.fig)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        if manager.online_plot.fig is not None and self.canvas is not None:
            try:
                self.canvas.draw_idle()
            except Exception:
                pass

    def closeEvent(self, event) -> None:
        manager.online_plot.close()
        super().closeEvent(event)
