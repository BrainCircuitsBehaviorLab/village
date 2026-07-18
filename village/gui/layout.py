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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
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
            style += (
                "QToolTip {background-color: white; color: black;"
                " font-size: 10pt; padding: 4px}"
            )
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
            style += (
                "QToolTip {background-color: white; color: black;"
                " font-size: 10pt; padding: 4px}"
            )
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
            style += (
                "QToolTip {background-color: white; color: black;"
                " font-size: 10pt; padding: 4px}"
            )
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
            self.setColumnStretch(i, 0)

        for i in range(self.num_of_rows):
            self.setRowMinimumHeight(i, self.row_height)
            self.setRowStretch(i, 0)

        if not stacked:
            self.create_common_elements()

    def create_common_elements(self) -> None:
        """Creates the navigation menu buttons common to all main layouts."""
        top_background = QWidget()
        top_background.setFixedSize(200 * self.column_width, 5 * self.row_height)
        top_background.setStyleSheet("background-color: #e0e0e0;")
        self.addWidget(top_background, 0, 0, 5, 200)

        status_container = QWidget()
        status_container.setFixedSize(155 * self.column_width, 3 * self.row_height)
        status_container.setStyleSheet("background-color: powderblue;")
        status_hbox = QHBoxLayout(status_container)
        status_hbox.setContentsMargins(10, 0, 10, 0)
        self.status_sub_labels: list[Label] = []
        for i in range(6):
            sub_label = Label("", "black", False, True, "", "")
            if i == 5:  # state name + description, on two lines: center both
                sub_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.status_sub_labels.append(sub_label)
            status_hbox.addWidget(sub_label)
            if i < 5:
                status_hbox.addStretch(1)
        self.addWidget(status_container, 0, 0, 3, 152)

        _nav_items = [
            ("MAIN", "Go to the main menu"),
            ("MONITOR", "Go to the monitor menu"),
            ("SUBJECTS", "Go to the subjects menu"),
            ("TASKS", "Go to the tasks menu"),
            ("DATA", "Go to the data menu"),
            ("CALIBRATION", "Go to the calibration menu"),
            ("SETTINGS", "Go to the settings menu"),
        ]
        self.nav_tab_bar = QTabBar()
        _nav_font = QFont("DejaVu Sans Condensed", 10)
        _nav_font.setBold(True)
        self.nav_tab_bar.setFont(_nav_font)
        self.nav_tab_bar.setExpanding(False)
        self.nav_tab_bar.setStyleSheet(
            "QTabBar::tab { background: lightgray;"
            " padding: 6px 25px;"
            " border: 1px solid #aaaaaa; border-bottom: none;"
            " border-radius: 4px 4px 0 0; margin-right: 2px; }"
            "QTabBar::tab:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QTabBar::tab:selected:disabled { background: steelblue; color: white; }"
            "QTabBar::tab:hover:!selected { background: #b0c4de; }"
            "QTabBar::tab:disabled { background: #cccccc; color: #999999; }"
            "QToolTip { background-color: white; color: black;"
            " font-size: 10pt; padding: 4px }"
        )
        for label, tooltip in _nav_items:
            idx = self.nav_tab_bar.addTab(label)
            self.nav_tab_bar.setTabToolTip(idx, tooltip)
        self.nav_tab_bar.currentChanged.connect(self._on_nav_tab_changed)

        # QTabBar has no built-in way to center its tabs (setExpanding(False)
        # just left-aligns them), so wrap it in a container and use stretches
        # on both sides to center the bar itself within the full row width.
        nav_container = QWidget()
        nav_container.setFixedSize(200 * self.column_width, 2 * self.row_height)
        # A QTabBar on its own has no "pane" to draw a border under, unlike a
        # QTabWidget -- draw one by hand so the nav row gets the same visual
        # separator as the tab groups below.
        nav_container.setStyleSheet("border-bottom: 2px solid #999999;")
        nav_hbox = QHBoxLayout(nav_container)
        nav_hbox.setContentsMargins(0, 0, 0, 0)
        nav_hbox.addStretch(1)
        nav_hbox.addWidget(self.nav_tab_bar)
        nav_hbox.addStretch(1)
        self.addWidget(nav_container, 3, 0, 2, 200)

        self.main_button = NavTabProxy(self.nav_tab_bar, 0)
        self.monitor_button = NavTabProxy(self.nav_tab_bar, 1)
        self.subjects_button = NavTabProxy(self.nav_tab_bar, 2)
        self.tasks_button = NavTabProxy(self.nav_tab_bar, 3)
        self.data_button = NavTabProxy(self.nav_tab_bar, 4)
        self.calibration_button = NavTabProxy(self.nav_tab_bar, 5)
        self.settings_button = NavTabProxy(self.nav_tab_bar, 6)

        self.stop_button = self.create_and_add_button(
            "",
            0,
            155,
            15,
            3,
            self.stop_button_clicked,
            "",
            "lightgray",
        )

        self.online_button = self.create_and_add_button(
            "ONLINE PLOTS",
            0,
            170,
            15,
            3,
            self.online_button_clicked,
            "Show live plots while a task is running",
            "lightgray",
        )

        self.exit_button = self.create_and_add_button(
            "EXIT",
            0,
            185,
            15,
            3,
            self.exit_button_clicked,
            "Exit the application",
            "lightcoral",
        )

        self.update_status_label_buttons()

    def update_status_label_buttons(self) -> None:
        """Updates the status label and button states based on manager state."""
        _tt = (
            "QToolTip {background-color: white; color: black;"
            " font-size: 10pt; padding: 4px}"
        )
        _red = "QPushButton {background-color: lightcoral; font-weight: bold}" + _tt
        _gray = "QPushButton {background-color: lightgray; font-weight: bold}" + _tt
        _off = (
            "QPushButton {background-color: #e0e0e0; font-weight: bold;"
            " color: #999999}" + _tt
        )
        manager.update_text()
        for sub_label, part in zip(self.status_sub_labels, manager.status_parts):
            sub_label.setText(part)

        state = manager.state
        if state == State.RUN_MANUAL:
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop the running task")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(_red)
            self.online_button.setEnabled(True)
            self.online_button.setStyleSheet(_gray)
        elif state.task_is_running():
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop the running task")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(_red)
            self.online_button.setEnabled(True)
            self.online_button.setStyleSheet(_gray)
        elif state == State.WAIT_SUBJECT_EXIT:
            self.stop_button.setText("CHANGE STATE")
            self.stop_button.setToolTip("Open options to change the system state")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(_gray)
            self.online_button.setEnabled(False)
            self.online_button.setStyleSheet(_off)
        elif state.can_stop_syncing():
            self.stop_button.setText("STOP SYNC")
            self.stop_button.setToolTip(
                "Stop synchronization. It will resume automatically"
                " after the next session."
            )
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(_red)
            self.online_button.setEnabled(False)
            self.online_button.setStyleSheet(_off)
        elif state == State.WAIT:
            self.stop_button.setText("CHANGE STATE")
            self.stop_button.setToolTip("Open options to change the system state")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet(_gray)
            self.online_button.setEnabled(False)
            self.online_button.setStyleSheet(_off)
        else:
            self.stop_button.setText("CHANGE STATE")
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet(_off)
            self.online_button.setEnabled(False)
            self.online_button.setStyleSheet(_off)

        self.online_button.setText("ONLINE PLOTS")

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
            manager.state = State.QUIT_APP
            self.update_status_label_buttons()

            if manager.changing_settings:
                reply = QMessageBox.question(
                    self.window,
                    "EXIT",
                    "Do you want to save the settings before exiting?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save,
                )
                if reply == QMessageBox.Save:
                    save_fn = getattr(self, "save_for_exit", None)
                    if save_fn is not None:
                        save_fn()
                    manager.turn_off_all_lights()
                    self.window.exit_app()
                elif reply == QMessageBox.Discard:
                    manager.turn_off_all_lights()
                    self.window.exit_app()
                else:
                    manager.state = old_state
                    self.update_status_label_buttons()
            else:
                reply = QMessageBox.question(
                    self.window,
                    "EXIT",
                    "Are you sure you want to exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    manager.turn_off_all_lights()
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

    def subjects_button_clicked(self) -> None:
        """Handles subjects button click."""
        if self.change_layout():
            if manager.state == State.MANUAL_MODE:
                manager.state = State.WAIT
                manager.reset_subject_task_training()
            self.close_online_plot_window()
            self.window.create_subjects_layout()

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

    def calibration_button_clicked(self) -> None:
        """Handles calibration button click."""
        if self.change_layout():
            if manager.state in [State.WAIT, State.MANUAL_MODE]:
                manager.state = State.MANUAL_MODE
                manager.reset_subject_task_training()
                self.close_online_plot_window()
                self.window.create_calibration_layout()
            else:
                QMessageBox.information(
                    self.window,
                    "CALIBRATION",
                    "Calibration is not available while a subject is in the box, "
                    "a detection is ongoing, or data is syncing.",
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
        """Handles stop button click based on current button text."""
        btn_text = self.stop_button.text()
        if btn_text == "STOP TASK":
            if manager.state == State.RUN_MANUAL:
                log.info("Task manually stopped.", subject=manager.subject.name)
                manager.task.stop_button_pressed = True
                manager.state = State.SAVE_MANUAL
            else:
                log.info(
                    "Task manually stopped. Disconnecting RFID Reader.",
                    subject=manager.subject.name,
                )
                manager.task.stop_button_pressed = True
                manager.state = State.OPEN_DOOR2_STOP
                log.info("Going to OPEN_DOOR2_STOP State")
        elif btn_text == "STOP SYNC":
            manager.after_session.cancel_event.set()
        elif btn_text == "CHANGE STATE":
            self._change_state_dialog()
            return
        self.update_gui()

    def _change_state_dialog(self) -> None:
        """Opens a dialog with state-correction options based on the current state."""
        msg = QMessageBox(self.window)
        msg.setWindowTitle("Change State")

        if manager.state == State.WAIT_SUBJECT_EXIT:
            msg.setText("Select an action:")
            go_wait = msg.addButton(
                "All subjects are back home, go to WAIT state", QMessageBox.AcceptRole
            )
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()
            if msg.clickedButton() == go_wait:
                manager.getting_weights = False
                manager.state = State.WAIT
                log.info("Going to WAIT State")
                self.update_gui()

        elif manager.state == State.WAIT:
            msg.setText("Select an action:")
            force_sync = msg.addButton("Force data sync", QMessageBox.AcceptRole)
            subject_inside = msg.addButton(
                "Subject is inside the box", QMessageBox.AcceptRole
            )
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()
            if msg.clickedButton() == force_sync:
                manager.detection_change = True
                manager.after_session_flag = True
                manager.state = State.SYNC
                log.info("Going to SYNC State")
                self.update_gui()
            elif msg.clickedButton() == subject_inside:
                manager.state = State.WAIT_SUBJECT_EXIT
                log.info("Going to WAIT_SUBJECT_EXIT State")
                self.update_gui()

    def close_online_plot_window(self) -> None:
        """Closes the online plot window if it is open."""
        try:
            self.plot_dialog.close()
        except Exception:
            pass

    def online_button_clicked(self) -> None:
        """Handles the online plots button click to show or update the plot window."""
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
            custom_geom = getattr(manager.online_plot, "window_geometry", None)
            self.plot_dialog: OnlinePlotDialog = OnlinePlotDialog()
            self.plot_dialog.setGeometry(*(custom_geom or geom))
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
            self.subjects_button_clicked,
            self.tasks_button_clicked,
            self.data_button_clicked,
            self.calibration_button_clicked,
            self.settings_button_clicked,
        ]
        if 0 <= index < len(actions):
            actions[index]()
        # If navigation was blocked we are still the active layout; restore the tab.
        if self.window.layout is self and hasattr(self, "_active_nav_index"):
            self.nav_tab_bar.blockSignals(True)
            self.nav_tab_bar.setCurrentIndex(self._active_nav_index)
            self.nav_tab_bar.blockSignals(False)

    def _highlight_nav_button(self, active_button: NavTabProxy) -> None:
        """Selects the active navigation tab."""
        self._active_nav_index = active_button._idx
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
