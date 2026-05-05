from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QCloseEvent, QFont, QPixmap, QWheelEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTimeEdit,
    QVBoxLayout,
)

from village.classes.enums import DataTable, State
from village.manager import manager
from village.scripts.log import log
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class NavTabProxy:
    """Proxy for a nav QTabBar tab, exposing a QPushButton-compatible interface."""

    def __init__(self, tab_bar: QTabBar, index: int) -> None:
        self._bar = tab_bar
        self._idx = index

    def setDisabled(self, disabled: bool) -> None:
        # Disabling the currently selected tab causes QTabBar to auto-advance
        # to the next tab, firing currentChanged during construction. Skip it.
        if disabled and self._bar.currentIndex() == self._idx:
            return
        self._bar.setTabEnabled(self._idx, not disabled)

    def setEnabled(self, enabled: bool) -> None:
        self._bar.setTabEnabled(self._idx, enabled)

    def isEnabled(self) -> bool:
        return self._bar.isTabEnabled(self._idx)


class Label(QLabel):
    """Custom styled QLabel."""

    def __init__(
        self,
        text: str,
        color: str,
        right_aligment: bool,
        bold: bool,
        description: str,
        background: str,
    ) -> None:
        """Initializes a Label with specific styling."""
        super().__init__(text)
        style = "QLabel {color: " + color
        if bold:
            style += "; font-weight: bold"
        if background == "":
            style += "}"
        else:
            style += "; background-color: " + background + "}"
        if description != "":
            style += "QToolTip {background-color: white; color: black; font-size: 9pt}"
            self.setToolTip(description)
        self.setStyleSheet(style)
        if right_aligment:
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


class LabelImage(QLabel):
    """QLabel for displaying an image from the resources directory."""

    def __init__(self, file) -> None:
        """Initializes a LabelImage."""
        super().__init__()
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        image_path = os.path.join(settings.get("APP_DIRECTORY"), "resources", file)
        pixmap = QPixmap(image_path)
        self.setPixmap(pixmap)


class LineEdit(QLineEdit):
    """Custom QLineEdit that triggers an action on text change."""

    def __init__(self, text: str, action: Callable) -> None:
        """Initializes a LineEdit."""
        super().__init__()
        self.setText(text)
        self.textChanged.connect(action)


class TimeEdit(QTimeEdit):
    """Custom QTimeEdit with HH:mm format."""

    def __init__(self, text: str, action: Callable) -> None:
        """Initializes a TimeEdit."""
        super().__init__()
        self.setDisplayFormat("HH:mm")
        self.setTime(QTime.fromString(text, "HH:mm"))
        self.timeChanged.connect(action)


class PushButton(QPushButton):
    """Custom styled QPushButton."""

    def __init__(
        self, text: str, color: str, action: Callable, description: str
    ) -> None:
        """Initializes a PushButton."""
        super().__init__(text)
        style = "QPushButton {background-color: " + color + "; font-weight: bold}"
        if description != "":
            style += "Tip {background-color: white; color: black; font-size: 9pt}"
            self.setToolTip(description)
        self.setStyleSheet(style)
        self.pressed.connect(action)


class ToggleButton(QPushButton):
    """Button that cycles through a list of values when pressed."""

    def __init__(
        self,
        key: str,
        possible_values: list[str],
        index: int,
        action: Callable,
        description: str,
        color: str = "lightgray",
    ) -> None:
        """Initializes a ToggleButton."""
        super().__init__()
        self.key = key
        self.possible_values = possible_values
        self.index = index
        self.action = action
        self.description = description
        self.value = self.possible_values[self.index]
        self.color = color
        self.update_style()
        self.pressed.connect(self.on_pressed)

    def update_style(self) -> None:
        """Updates the button text and color based on current value."""

        self.setText(self.value)
        color = "darkgray" if self.value == "OFF" else self.color
        style = "QPushButton {background-color: " + color + "; font-weight: bold}"
        if self.description != "":
            style += "QToolTip {background-color: white; color: black; font-size: 9pt}"
            self.setToolTip(self.description)
        self.setStyleSheet(style)

    def on_pressed(self) -> None:
        """Handles button press, cycling value and triggering action."""
        self.index = (self.index + 1) % len(self.possible_values)
        self.value = self.possible_values[self.index]
        self.update_style()
        self.action(self.value, self.key)


class ComboBox(QComboBox):
    """Custom QComboBox linked to a setting or variable."""

    def __init__(
        self, key: str, possible_values: list[str], index: int, action: Callable
    ) -> None:
        """Initializes a ComboBox."""
        super().__init__()
        self.addItems(possible_values)
        self.key = key
        self.possible_values = possible_values
        self.index = index
        self.action = action
        if not self.possible_values:
            self.index = 0
            self.value = ""
        else:
            try:
                self.value = self.possible_values[self.index]
            except Exception:
                self.index = 0
                self.value = self.possible_values[0]
        self.setCurrentText(self.value)
        self.currentTextChanged.connect(self.handleTextChanged)
        self.update_style()

    def update_style(self) -> None:
        """Updates the combo box styling."""
        color = "darkgray" if self.value == "OFF" else "lightgray"
        self.setStyleSheet(
            "QComboBox {background-color: " + color + "; font-size: 8pt}"
        )

    def handleTextChanged(self, value: str) -> None:
        """Handles value changes."""
        self.value = value
        self.update_style()
        self.action(self.value, self.key)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Ignores wheel events to prevent accidental changes."""
        event.ignore()


class Layout(QGridLayout):
    """Base class for all GUI layouts in the application.

    Provides common methods for creating widgets (buttons, labels, inputs) and
    managing the layout grid.
    """

    def __init__(
        self,
        window: GuiWindow,
        stacked: bool = False,
        rows: int = 51,
        columns: int = 200,
    ) -> None:
        """Initializes the Layout.

        Args:
            window (GuiWindow): The parent window.
            stacked (bool, optional): Whether this layout is part of a stacked widget.
            Defaults to False.
            rows (int, optional): Number of rows in the grid. Defaults to 51.
            columns (int, optional): Number of columns in the grid. Defaults to 200.
        """
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
        """Creates the navigation menu buttons common to all main layouts."""
        self.status_label = self.create_and_add_label(
            "", 1, 0, 200, 2, "black", background="powderblue"
        )

        _nav_items = [
            ("MAIN", "Go to the main menu"),
            ("MONITOR", "Go to the monitor menu"),
            ("TASKS", "Go to the tasks menu"),
            ("DATA", "Go to the data menu"),
            ("WATER CALIBRATION", "Go to the water calibration menu"),
            ("SOUND CALIBRATION", "Go to the sound calibration menu"),
            ("SETTINGS", "Go to the settings menu"),
        ]
        self.nav_tab_bar = QTabBar()
        _nav_font = QFont("DejaVu Sans Condensed", 10)
        _nav_font.setBold(True)
        self.nav_tab_bar.setFont(_nav_font)
        self.nav_tab_bar.setExpanding(False)
        self.nav_tab_bar.setStyleSheet(
            "QTabBar::tab { background: lightgray;"
            " padding: 6px 30px;"
            " border: 1px solid #aaaaaa; border-bottom: none;"
            " border-radius: 4px 4px 0 0; margin-right: 2px; }"
            "QTabBar::tab:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QTabBar::tab:selected:disabled { background: steelblue; color: white; }"
            "QTabBar::tab:hover:!selected { background: #b0c4de; }"
            "QTabBar::tab:disabled { background: #cccccc; color: #999999; }"
            "QToolTip { background-color: white; color: black; font-size: 9pt; }"
        )
        for label, tooltip in _nav_items:
            idx = self.nav_tab_bar.addTab(label)
            self.nav_tab_bar.setTabToolTip(idx, tooltip)
        self.nav_tab_bar.currentChanged.connect(self._on_nav_tab_changed)
        self.addWidget(self.nav_tab_bar, 4, 0, 2, 200)

        self.main_button = NavTabProxy(self.nav_tab_bar, 0)
        self.monitor_button = NavTabProxy(self.nav_tab_bar, 1)
        self.tasks_button = NavTabProxy(self.nav_tab_bar, 2)
        self.data_button = NavTabProxy(self.nav_tab_bar, 3)
        self.water_calibration_button = NavTabProxy(self.nav_tab_bar, 4)
        self.sound_calibration_button = NavTabProxy(self.nav_tab_bar, 5)
        self.settings_button = NavTabProxy(self.nav_tab_bar, 6)

        self.online_or_force_button = self.create_and_add_button(
            "ONLINE PLOTS",
            3,
            150,
            16,
            3,
            self.online_or_force_button_clicked,
            "Show live plots while a task is running",
            "white",
        )

        self.stop_button = self.create_and_add_button(
            "",
            3,
            166,
            22,
            3,
            self.stop_button_clicked,
            "Stop a running task",
            "lightcoral",
        )

        self.exit_button = self.create_and_add_button(
            "EXIT",
            3,
            188,
            12,
            3,
            self.exit_button_clicked,
            "Exit the application",
            "lightcoral",
        )

        self.update_status_label_buttons()

    def update_status_label_buttons(self) -> None:
        """Updates the status label and button states based on manager state."""
        _tt = "QToolTip {background-color: white; color: black; font-size: 9pt}"
        manager.update_text()
        self.status_label.setText(manager.text)
        if manager.state.can_stop_task():
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop a running task")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
            )
            self.online_or_force_button.setText("ONLINE PLOTS")
            self.online_or_force_button.setToolTip(
                "Show live plots while a task is running"
            )
            self.online_or_force_button.setEnabled(True)
            self.online_or_force_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
            )
        elif manager.state.can_go_to_wait():
            self.stop_button.setText("GO TO WAIT STATE")
            text = (
                "The system thinks there is a subject in the box, but there isn't. "
                + "Use this to return to WAIT state."
            )
            self.stop_button.setToolTip(text)
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(
                "QPushButton {background-color: lightgray; font-weight: bold}" + _tt
            )
            self.online_or_force_button.setText("FORCE SYNC")
            self.online_or_force_button.setToolTip(
                "Force synchronisation with external device or server"
            )
            self.online_or_force_button.setEnabled(False)
            self.online_or_force_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
            )
        elif manager.state.can_stop_syncing():
            self.stop_button.setText("STOP SYNC")
            text = (
                "Stop data synchronization. Sync will resume automatically after "
                + "the next session."
            )
            self.stop_button.setToolTip(text)
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
            )
            self.online_or_force_button.setText("FORCE SYNC")
            self.online_or_force_button.setToolTip(
                "Force synchronisation with external device or server"
            )
            self.online_or_force_button.setEnabled(False)
            self.online_or_force_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
            )
        else:
            self.stop_button.setText("WAIT FOR SUBJECT EXIT")
            text = (
                "The system thinks there is no subject in the box (currently in WAIT) "
                + "but there is one. Use this to make the system wait for the "
                + "subject to exit."
            )
            self.stop_button.setToolTip(text)
            self.stop_button.setStyleSheet(
                "QPushButton {background-color: lightgray; font-weight: bold}" + _tt
            )
            self.online_or_force_button.setText("FORCE SYNC")
            self.online_or_force_button.setToolTip(
                "Force synchronisation with external device or server"
            )
            self.online_or_force_button.setStyleSheet(
                "QPushButton {background-color: lightgray; font-weight: bold}" + _tt
            )

            if manager.state == State.WAIT:
                self.stop_button.setEnabled(True)
                self.online_or_force_button.setEnabled(True)
            else:
                self.stop_button.setEnabled(False)
                self.online_or_force_button.setEnabled(False)

    def exit_button_clicked(self) -> None:
        """Handles exit button click, confirming exit and saving data if needed."""
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
        """Checks if layout change is allowed (placeholder base method).

        Args:
            auto (bool, optional): Whether the change is automatic. Defaults to False.

        Returns:
            bool: Always True in the base class.
        """
        return True

    def main_button_clicked(self, auto: bool = False) -> None:
        """Handles main menu button click.

        Args:
            auto (bool, optional): Whether the click is automatic. Defaults to False.
        """
        if self.change_layout(auto=auto):
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            self.close_online_plot_window()
            self.window.create_main_layout()

    def monitor_button_clicked(self) -> None:
        """Handles monitor button click."""
        if self.change_layout():
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            manager.detection_change = True
            self.close_online_plot_window()
            self.window.create_monitor_layout()

    def tasks_button_clicked(self) -> None:
        """Handles tasks button click."""
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
        """Handles data button click."""
        if self.change_layout():
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            self.close_online_plot_window()
            self.window.create_data_layout()

    def water_calibration_button_clicked(self) -> None:
        """Handles water calibration button click."""
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
        """Handles sound calibration button click."""
        if not manager.sound_calibration_functions:
            text = "To calibrate the sound, you must first create a list of functions "
            text += "that generate the sounds you want to use for calibration in "
            text += "your project. Please refer to the documentation for instructions "
            text += "on how to do this."
            QMessageBox.information(self.window, "WARNING", text)
            return
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
        """Handles settings button click."""
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
        """Handles stop button click to stop tasks, sync, or reset state."""
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
        elif manager.state == State.WAIT:
            manager.state = State.WAIT_EXIT
            log.info("Going to WAIT_EXIT State")
        self.update_gui()

    def close_online_plot_window(self) -> None:
        """Closes the online plot window if it is open."""
        try:
            self.plot_dialog.close()
        except Exception:
            pass

    def online_or_force_button_clicked(self) -> None:
        """Handles the online plots button click to show or update the plot window."""
        if manager.state == State.WAIT:
            manager.detection_change = True
            manager.state = State.SYNC
            manager.after_session_flag = True
            log.info("Going to SYNC State")
            manager.state = State.SYNC
        else:
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
        """Ignores the close event to prevent closing the layout directly."""
        event.ignore()

    def delete_optional_widgets(self, type: str) -> None:
        """Deletes widgets of a specific type from the layout.

        Args:
            type (str): The type property value to match.
        """
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
        """Creates and adds a Label to the layout.

        Args:
            text (str): The label text.
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            color (str): The text color.
            right_aligment (bool, optional): Whether to right align. Defaults to False.
            bold (bool, optional): Whether to use bold font. Defaults to True.
            description (str, optional): Tooltip text. Defaults to "".
            background (str, optional): Background color. Defaults to "".

        Returns:
            Label: The created label.
        """
        label = Label(text, color, right_aligment, bold, description, background)
        label.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(label, row, column, height, width)
        return label

    def create_and_add_image(
        self, row: int, column: int, width: int, height: int, file: str
    ) -> LabelImage:
        """Creates and adds an image label to the layout.

        Args:
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            file (str): The image filename.

        Returns:
            LabelImage: The created image label.
        """
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
        """Creates and adds a LineEdit to the layout.

        Args:
            text (str): The initial text.
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            action (Callable): The function to call on text change.

        Returns:
            LineEdit: The created line edit.
        """
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
        """Creates and adds a TimeEdit to the layout.

        Args:
            text (str): The initial time text (HH:mm).
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            action (Callable): The function to call on time change.

        Returns:
            TimeEdit: The created time edit.
        """
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
        """Creates and adds a PushButton to the layout.

        Args:
            text (str): The button text.
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            action (Callable): The function to call on button press.
            description (str): Tooltip text.
            color (str, optional): Background color. Defaults to "lightgray".

        Returns:
            PushButton: The created button.
        """
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
        color: str = "lightgray",
    ) -> ToggleButton:
        """Creates and adds a ToggleButton to the layout.

        Args:
            key (str): The key associated with the button.
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            possible_values (list): List of possible values to cycle through.
            index (int): Initial index in possible_values.
            action (Callable): The function to call on toggle.
            description (str): Tooltip text.
            Defaults to False.
            color (str, optional): Background color. Defaults to "lightgray".

        Returns:
            ToggleButton: The created toggle button.
        """
        button = ToggleButton(
            key,
            possible_values,
            index,
            action,
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
        """Creates and adds a ComboBox to the layout.

        Args:
            key (str): The key associated with the combo box.
            row (int): The row index.
            column (int): The column index.
            width (int): The width span.
            height (int): The height span.
            possible_values (list): List of items.
            index (int): Initial selected index.
            action (Callable): The function to call on selection change.

        Returns:
            ComboBox: The created combo box.
        """
        combo_box = ComboBox(key, possible_values, index, action)
        combo_box.setFixedSize(width * self.column_width, height * self.row_height)
        self.addWidget(combo_box, row, column, height, width)
        return combo_box

    def _on_nav_tab_changed(self, index: int) -> None:
        """Dispatches tab click to the appropriate navigation action."""
        if "layout" not in self.window.__dict__:
            return
        if self.window.layout is not self:
            return
        actions: list[Callable[[], None]] = [
            self.main_button_clicked,
            self.monitor_button_clicked,
            self.tasks_button_clicked,
            self.data_button_clicked,
            self.water_calibration_button_clicked,
            self.sound_calibration_button_clicked,
            self.settings_button_clicked,
        ]
        if 0 <= index < len(actions):
            actions[index]()

    def _highlight_nav_button(self, active_button: NavTabProxy) -> None:
        """Selects the active navigation tab."""
        self.nav_tab_bar.blockSignals(True)
        self.nav_tab_bar.setCurrentIndex(active_button._idx)
        self.nav_tab_bar.blockSignals(False)

    def update_gui(self) -> None:
        """Updates the GUI elements (placeholder base method)."""
        pass

    def check_errors(self) -> None:
        """Checks for errors in the manual task and displays a warning if needed."""
        if manager.error_in_manual_task:
            text = "Error in manual task"
            QMessageBox.information(self.window, "ERROR", text)
            manager.error_in_manual_task = False


class OnlinePlotDialog(QDialog):
    """Dialog for displaying real-time plots during a task."""

    def __init__(self) -> None:
        """Initializes the OnlinePlotDialog."""
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
        """Handles the close event to ensure the plot is properly closed."""
        manager.online_plot.close()
        super().closeEvent(event)
