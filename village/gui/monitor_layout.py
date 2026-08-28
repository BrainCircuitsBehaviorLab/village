from __future__ import annotations

import traceback
from functools import partial
from typing import TYPE_CHECKING, Any

import pandas as pd
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from village.classes.enums import (
    Actions,
    Active,
    AreaActive,
    ControllerEnum,
    Cycle,
    CycleDay,
    Info,
    ScreenActive,
)
from village.classes.null_classes import NullScale
from village.custom_classes.auto_no_mouse_base import AutoNoMouseBase
from village.devices.camera import cam_box, cam_corridor
from village.devices.chip import (
    Motor,
    ir_light_box,
    motor_box1,
    motor_box2,
    motor_box3,
    motor_box4,
    motor_box5,
    motor_box6,
    motor_box7,
    motor_corridor1,
    motor_corridor2,
    motor_corridor3,
    motor_corridor4,
    parse_motor_values,
    visible_light_box,
)
from village.devices.scale import Scale, scale, scale_box
from village.devices.temp_sensor import temp_sensor
from village.gui.layout import Label, Layout, PushButton
from village.manager import manager
from village.plots.corridor_plot import corridor_plot
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.scripts.utils import create_pixmap
from village.settings import settings

if TYPE_CHECKING:
    from village.classes.null_classes import NullMotor
    from village.devices.motor_old import MotorOld
    from village.gui.gui_window import GuiWindow


def show_motor_edit_dialog(
    parent: Layout, name: str, motor: Any, values_key: str
) -> None:
    """Opens a dialog to edit one motor's open/close angles and times.

    OPEN/CLOSE apply the fields currently typed (falling back to the current
    value on bad input) to the motor and move it there immediately, so changes
    can be tested before committing. SAVE persists the tested/typed values to
    values_key and the motor; DISCARD restores the motor's original values
    (undoing anything OPEN/CLOSE tested) and leaves the setting untouched.

    Works for both Motor (ramped, supports timing) and MotorOld (instant,
    ignores timing) since it only calls the .open()/.close() interface both
    implement, never .move() directly (MotorOld has no .move()).
    """
    open_a, close_a, time_o, time_c = parse_motor_values(settings.get(values_key))
    # MotorOld has no time_open/time_close (it moves instantly, no ramping) --
    # read those defensively so this dialog works for it too.
    orig = (
        motor.open_angle,
        motor.close_angle,
        getattr(motor, "time_open", 0),
        getattr(motor, "time_close", 0),
    )

    dialog = QDialog()
    dialog.setWindowTitle(f"{name} angles and times")
    x = parent.column_width * 74
    y = parent.row_height * 21
    width = parent.column_width * 60
    height = parent.row_height * 8
    dialog.setGeometry(x, y, width, height)

    main_layout = QVBoxLayout()
    grid = QGridLayout()

    open_angle_edit = QLineEdit()
    open_angle_edit.setPlaceholderText(str(open_a))
    open_time_edit = QLineEdit()
    open_time_edit.setPlaceholderText(str(time_o))
    close_angle_edit = QLineEdit()
    close_angle_edit.setPlaceholderText(str(close_a))
    close_time_edit = QLineEdit()
    close_time_edit.setPlaceholderText(str(time_c))
    edits = [open_angle_edit, close_angle_edit, open_time_edit, close_time_edit]

    btn_open = QPushButton("OPEN")
    btn_close = QPushButton("CLOSE")

    grid.addWidget(QLabel("Open angle:"), 0, 0)
    grid.addWidget(open_angle_edit, 0, 1)
    grid.addWidget(QLabel("Open time (ms):"), 0, 2)
    grid.addWidget(open_time_edit, 0, 3)
    grid.addWidget(btn_open, 0, 4)

    grid.addWidget(QLabel("Close angle:"), 1, 0)
    grid.addWidget(close_angle_edit, 1, 1)
    grid.addWidget(QLabel("Close time (ms):"), 1, 2)
    grid.addWidget(close_time_edit, 1, 3)
    grid.addWidget(btn_close, 1, 4)

    main_layout.addLayout(grid)

    def field(i: int, current: int) -> int:
        try:
            return int(edits[i].text())
        except ValueError:
            return current

    def apply_fields_to_motor() -> None:
        motor.open_angle = field(0, open_a)
        motor.close_angle = field(1, close_a)
        motor.time_open = field(2, time_o)
        motor.time_close = field(3, time_c)

    def open_clicked() -> None:
        apply_fields_to_motor()
        motor.open()

    def close_clicked() -> None:
        apply_fields_to_motor()
        motor.close()

    btn_open.clicked.connect(open_clicked)
    btn_close.clicked.connect(close_clicked)

    btns_layout = QHBoxLayout()
    btn_save = QPushButton("SAVE")
    btn_discard = QPushButton("DISCARD")
    btns_layout.addWidget(btn_save)
    btns_layout.addWidget(btn_discard)
    main_layout.addLayout(btns_layout)
    dialog.setLayout(main_layout)

    btn_save.clicked.connect(dialog.accept)
    btn_discard.clicked.connect(dialog.reject)

    if dialog.exec_():
        apply_fields_to_motor()
        settings.set(
            values_key,
            (motor.open_angle, motor.close_angle, motor.time_open, motor.time_close),
        )
    else:
        motor.open_angle, motor.close_angle, motor.time_open, motor.time_close = orig


def show_motor_move_dialog(parent: Layout, name: str, motor: Any) -> None:
    """Opens a dialog to move a motor to a chosen angle over a chosen duration.

    Bad input for a field falls back to the placeholder shown in that field.
    """
    dialog = QDialog()
    dialog.setWindowTitle(f"Move {name}")
    x = parent.column_width * 74
    y = parent.row_height * 21
    width = parent.column_width * 40
    height = parent.row_height * 8
    dialog.setGeometry(x, y, width, height)

    main_layout = QVBoxLayout()
    grid = QGridLayout()
    grid.addWidget(QLabel("Angle (0-180):"), 0, 0)
    angle_edit = QLineEdit()
    angle_edit.setPlaceholderText(str(motor.current_angle))
    grid.addWidget(angle_edit, 0, 1)
    grid.addWidget(QLabel("Time (ms):"), 1, 0)
    time_edit = QLineEdit()
    time_edit.setPlaceholderText("0")
    grid.addWidget(time_edit, 1, 1)
    main_layout.addLayout(grid)

    btns_layout = QHBoxLayout()
    btn_move = QPushButton("MOVE")
    btn_cancel = QPushButton("CANCEL")
    btns_layout.addWidget(btn_move)
    btns_layout.addWidget(btn_cancel)
    main_layout.addLayout(btns_layout)
    dialog.setLayout(main_layout)

    btn_move.clicked.connect(dialog.accept)
    btn_cancel.clicked.connect(dialog.reject)

    if dialog.exec_():
        try:
            angle = int(angle_edit.text())
        except ValueError:
            angle = motor.current_angle
        try:
            total_ms = int(time_edit.text())
        except ValueError:
            total_ms = 0
        motor.move(angle, total_ms)


class LabelButtons:
    """Class to manage labels with increase/decrease buttons for settings."""

    def __init__(
        self,
        name: str,
        direction: str,
        row: int,
        column: int,
        width: int,
        color: str,
        layout: Layout,
        width2: int = 4,
        width_res: int = 640,
        height_res: int = 480,
    ) -> None:
        """Initializes the LabelButtons instance.

        Args:
            name (str): The name of the setting.
            direction (str): The specific attribute (e.g., 'left', 'top', 'threshold').
            row (int): The row position in the layout.
            column (int): The column position in the layout.
            width (int): The width of the label.
            color (str): The color of the text.
            layout (Layout): The parent layout.
            width_res (int, optional): Width resolution. Defaults to 640.
            height_res (int, optional): Height resolution. Defaults to 480.
        """
        self.name = name
        self.direction = direction
        self.base_color = color

        self.mapping_dict_index = {
            "left": 0,
            "top": 1,
            "right": 2,
            "bottom": 3,
            "threshold": 4,
            "thr_day": 4,
            "thr_night": 5,
            "empty_limit": 0,
            "subject_limit": 1,
            "lens_position": -1,
            "sharpness": -1,
            "exposure_day": -1,
            "exposure_night": -1,
            "exposure": -1,
        }
        self.mapping_dict_max = {
            "left": width_res,
            "top": height_res,
            "right": width_res,
            "bottom": height_res,
            "threshold": 255,
            "thr_day": 255,
            "thr_night": 255,
            "empty_limit": 1000000,
            "subject_limit": 1000000,
            "lens_position": 10,
            "sharpness": 16,
            "exposure_day": 2,
            "exposure_night": 2,
            "exposure": 2,
        }
        self.mapping_dict_increase = {
            "left": "\u2192",
            "top": "\u2193",
            "right": "\u2192",
            "bottom": "\u2193",
            "threshold": "\u2191",
            "thr_day": "\u2191",
            "thr_night": "\u2191",
            "empty_limit": "\u2191",
            "subject_limit": "\u2191",
            "lens_position": "\u2191",
            "sharpness": "\u2191",
            "exposure_day": "\u2191",
            "exposure_night": "\u2191",
            "exposure": "\u2191",
        }
        self.mapping_dict_decrease = {
            "left": "\u2190",
            "top": "\u2191",
            "right": "\u2190",
            "bottom": "\u2191",
            "threshold": "\u2193",
            "thr_day": "\u2193",
            "thr_night": "\u2193",
            "empty_limit": "\u2193",
            "subject_limit": "\u2193",
            "lens_position": "\u2193",
            "sharpness": "\u2193",
            "exposure_day": "\u2193",
            "exposure_night": "\u2193",
            "exposure": "\u2193",
        }

        self.index: int = self.mapping_dict_index[direction]
        self.max: int = self.mapping_dict_max[direction]
        self.increase: str = self.mapping_dict_increase[direction]
        self.decrease: str = self.mapping_dict_decrease[direction]
        if self.index == -1:
            self.label_value = settings.get(name)
        else:
            self.label_value = settings.get(name)[self.index]
        self.description = settings.get_description(name)

        self.label2: Label = layout.create_and_add_label(
            direction, row, column, width, 2, color, description=self.description
        )
        column += width
        self.label3 = layout.create_and_add_label(
            str(self.label_value), row, column, width2, 2, color, right_aligment=True
        )

        regular_buttons = ["left", "right", "top", "bottom"]

        val = width2 + 1 if self.direction in regular_buttons else width2 + 3
        column += val
        self.btn_decrease = layout.create_and_add_button(
            self.decrease, row, column, 2, 2, self.start_decreasing, ""
        )
        val = 2 if self.direction in regular_buttons else -2
        column += val
        self.btn_increase = layout.create_and_add_button(
            self.increase, row, column, 2, 2, self.start_increasing, ""
        )

        self.btn_increase.released.connect(self.stop_timer)
        self.btn_decrease.released.connect(self.stop_timer)

        self.timer_increase1 = QTimer()
        self.timer_increase1.setInterval(200)
        self.timer_increase1.setSingleShot(True)
        self.timer_increase2 = QTimer()
        self.timer_increase2.setInterval(10)

        self.timer_decrease1 = QTimer()
        self.timer_decrease1.setInterval(200)
        self.timer_decrease1.setSingleShot(True)
        self.timer_decrease2 = QTimer()
        self.timer_decrease2.setInterval(10)

        self.timer_increase1.timeout.connect(self.timer_increase2.start)
        self.timer_increase2.timeout.connect(self.increase_value)
        self.timer_decrease1.timeout.connect(self.timer_decrease2.start)
        self.timer_decrease2.timeout.connect(self.decrease_value)

    def set_dimmed(self, dimmed: bool) -> None:
        """Dims the control's labels (light gray) or restores their color."""
        color = "lightgray" if dimmed else self.base_color
        self.label2.set_color(color)
        self.label3.set_color(color)

    def set_visible(self, visible: bool) -> None:
        """Shows or hides all the control's widgets (labels and buttons)."""
        self.label2.setVisible(visible)
        self.label3.setVisible(visible)
        self.btn_increase.setVisible(visible)
        self.btn_decrease.setVisible(visible)

    def increase_value(self) -> None:
        """Increases the value of the setting safely."""
        if self.label_value < self.max:
            if (
                self.direction == "left"
                and self.label_value
                >= settings.get(self.name)[self.mapping_dict_index["right"]]
            ) or (
                self.direction == "top"
                and self.label_value
                >= settings.get(self.name)[self.mapping_dict_index["bottom"]]
            ):
                return
            elif self.direction in [
                "left",
                "top",
                "right",
                "bottom",
                "threshold",
                "thr_day",
                "thr_night",
                "empty_limit",
                "subject_limit",
                "exposure_day",
                "exposure_night",
                "exposure",
            ]:
                self.label_value += 1
            else:
                self.label_value += 0.1
                self.label_value = round(self.label_value, 1)
            self.label3.setText(str(self.label_value))

    def decrease_value(self) -> None:
        """Decreases the value of the setting safely."""
        if self.label_value > 0:
            if (
                self.direction == "right"
                and self.label_value
                <= settings.get(self.name)[self.mapping_dict_index["left"]]
            ) or (
                self.direction == "bottom"
                and self.label_value
                <= settings.get(self.name)[self.mapping_dict_index["top"]]
            ):
                return
            elif self.direction in [
                "left",
                "top",
                "right",
                "bottom",
                "threshold",
                "thr_day",
                "thr_night",
                "empty_limit",
                "subject_limit",
                "exposure_day",
                "exposure_night",
                "exposure",
            ]:
                self.label_value -= 1
            else:
                self.label_value -= 0.1
                self.label_value = round(self.label_value, 1)
            self.label3.setText(str(self.label_value))

    def start_increasing(self) -> None:
        """Starts the timer to increase the value continuously."""
        self.increase_value()
        self.timer_increase1.start()

    def start_decreasing(self) -> None:
        """Starts the timer to decrease the value continuously."""
        self.decrease_value()
        self.timer_decrease1.start()

    def stop_timer(self) -> None:
        """Stops the timers and saves the new value."""
        self.timer_increase1.stop()
        self.timer_decrease1.stop()
        self.timer_increase2.stop()
        self.timer_decrease2.stop()

        if self.name in [
            "LENS_POSITION_BOX",
            "SHARPNESS_BOX",
            "EXPOSURE_BOX",
            "LENS_POSITION_CORRIDOR",
            "SHARPNESS_CORRIDOR",
            "EXPOSURE_DAY_CORRIDOR",
            "EXPOSURE_NIGHT_CORRIDOR",
        ]:
            settings.set(self.name, self.label_value)
        else:
            coords = settings.get(self.name)
            coords = list(coords)
            coords[self.index] = int(self.label_value)
            if self.direction in ["empty_limit", "subject_limit"]:
                if coords[0] >= coords[1]:
                    self.label_value = settings.get(self.name)[self.index]
                    self.label3.setText(str(self.label_value))
                    return
            else:
                left, top, right, bottom = coords[0], coords[1], coords[2], coords[3]
                if right <= left or bottom <= top:
                    self.label_value = settings.get(self.name)[self.index]
                    self.label3.setText(str(self.label_value))
                    return
            settings.set(self.name, coords)

        cam_corridor.change = True
        cam_box.change = True


class MonitorLayout(Layout):
    """Layout for monitoring system status, devices, and camera feeds."""

    def __init__(self, window: GuiWindow) -> None:
        """Initializes the MonitorLayout.

        Args:
            window (GuiWindow): The parent window.
        """
        super().__init__(window)
        self._highlight_nav_button(self.monitor_button)
        self.draw()

    def draw(self) -> None:
        """Draws the monitor layout elements."""

        self.buttons: list[QPushButton] = []

        self.monitor_button.setDisabled(True)

        self.central_widget = QWidget(self.window)
        self.bottom_widget = QWidget(self.window)

        self.page1 = QWidget(self.central_widget)
        self.page1.setStyleSheet("background-color:white")
        self.page1Layout = CorridorLayout(self.window, 22, 36)
        self.page1.setLayout(self.page1Layout)

        self.page2 = QWidget(self.central_widget)
        self.page2.setStyleSheet("background-color:white")
        self.page2Layout = BoxLayout(self.window, 22, 36)
        self.page2.setLayout(self.page2Layout)

        self.page3 = QWidget(self.central_widget)
        self.page3.setStyleSheet("background-color:white")
        self.page3_layout = QVBoxLayout(self.page3)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.page3_sub_widget = QWidget()
        self.page3_sub_layout = FunctionsLayout(self.window, 22, 28)
        self.page3_sub_widget.setLayout(self.page3_sub_layout)

        self.scroll_area.setWidget(self.page3_sub_widget)

        self.page3_layout.addWidget(self.scroll_area)
        self.page3.setLayout(self.page3_layout)

        self.page4 = QWidget(self.central_widget)
        self.page4.setStyleSheet("background-color:white")
        self.page4Layout = VirtualMouseLayout(self.window, 22, 36)
        self.page4.setLayout(self.page4Layout)

        _tab_style = (
            "QTabWidget::tab-bar { alignment: center; }"
            # Native pane border is content-dependent (only shows where a
            # page's own layout doesn't fill the pane exactly) -- hide it, a
            # manually drawn widget below takes its place instead. A
            # border-bottom on QTabWidget itself doesn't work here: the pane
            # (filled white by each page) expands into that pixel and paints
            # over it.
            "QTabWidget::pane { border: none; }"
            "QTabBar::tab { background: #d0d0d0;"
            " padding: 6px 4px;"
            " border: 1px solid #aaaaaa; border-bottom: none;"
            " border-radius: 4px 4px 0 0; margin-right: 2px; }"
            "QTabBar::tab:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QTabBar::tab:hover { background: #b0c4de; }"
        )
        _tab_font = QFont("DejaVu Sans Condensed", 9)
        _tab_font.setBold(True)
        self.actions_tab_widget = QTabWidget()
        self.actions_tab_widget.setStyleSheet(_tab_style)
        self.actions_tab_widget.tabBar().setExpanding(False)
        self.actions_tab_widget.tabBar().setFont(_tab_font)

        self._actions_tab_map: list[str] = []
        self._tab_map: list[str] = []
        if manager.use_of_corridor:
            self.actions_tab_widget.addTab(self.page1, "CORRIDOR")
            self._actions_tab_map.append("CORRIDOR")
        if manager.use_of_box_chip or manager.controller_type == ControllerEnum.BPOD:
            self.actions_tab_widget.addTab(self.page2, "BOX")
            self._actions_tab_map.append("BOX")
        self.actions_tab_widget.addTab(self.page3, "FUNCTIONS")
        self._actions_tab_map.append("FUNCTIONS")
        if (
            manager.controller_type == ControllerEnum.BPOD
            or settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON
            or settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN
        ):
            self.actions_tab_widget.addTab(self.page4, "VIRTUAL MOUSE")
            self._actions_tab_map.append("VIRTUAL_MOUSE")

        self.actions_tab_widget.currentChanged.connect(self.on_actions_tab_changed)
        self.addWidget(self.actions_tab_widget, 7, 80, 24, 40)

        self.page5 = QWidget(self.bottom_widget)
        self.page5.setStyleSheet("background-color:white")
        self.page5Layout = InfoLayout(self.window, 16, 200)
        self.page5.setLayout(self.page5Layout)

        self.page7 = QWidget(self.bottom_widget)
        self.page7.setStyleSheet("background-color:white")
        self.page7Layout = DetectionLayout(self.window, 16, 200)
        self.page7.setLayout(self.page7Layout)

        self.page6 = QWidget(self.bottom_widget)
        self.page6.setStyleSheet("background-color:white")
        self.page6Layout = CorridorPlotLayout(self.window, 16, 200)
        self.page6.setLayout(self.page6Layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(_tab_style)
        self.tab_widget.tabBar().setExpanding(False)
        self.tab_widget.tabBar().setFont(_tab_font)
        self.tab_widget.addTab(self.page5, "INFO")
        self._tab_map.append("INFO")
        if manager.use_of_corridor:
            self.tab_widget.addTab(self.page6, "PLOT")
            self._tab_map.append("PLOT")
        self.tab_widget.addTab(self.page7, "DETECTION SETTINGS")
        self._tab_map.append("DETECTION_SETTINGS")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        value_key = manager.info.value
        if value_key in self._tab_map:
            self.tab_widget.setCurrentIndex(self._tab_map.index(value_key))

        actions_key = manager.actions.name
        if actions_key in self._actions_tab_map:
            self.actions_tab_widget.setCurrentIndex(
                self._actions_tab_map.index(actions_key)
            )

        self.qpicamera2_corridor = cam_corridor.start_preview_window()
        self.qpicamera2_box = cam_box.start_preview_window()

        self.qpicamera2_corridor.setFixedSize(640, 480)
        self.qpicamera2_box.setFixedSize(640, 480)

        self.addWidget(self.qpicamera2_corridor, 5, 0, 28, 80)
        self.addWidget(self.qpicamera2_box, 5, 120, 28, 80)
        self.addWidget(self.tab_widget, 33, 0, 18, 200)
        self.tab_widget.raise_()

    def on_actions_tab_changed(self, index: int) -> None:
        """Handles tab selection for the central actions panel."""
        if index < len(self._actions_tab_map):
            value = self._actions_tab_map[index]
            manager.actions = Actions[value]
            settings.set("ACTIONS", value)
        self.update_gui()

    def on_tab_changed(self, index: int) -> None:
        """Handles tab selection for the bottom info panel."""
        if index < len(self._tab_map):
            value = self._tab_map[index]
            manager.info = Info[value]
            settings.set("INFO", value)
        self.update_gui()

    def update_gui(self) -> None:
        """Updates the GUI and its components."""
        self.update_status_label_buttons()
        self.page4Layout.update_gui()
        if manager.actions == Actions.CORRIDOR:
            self.page1Layout.update_gui()
        match manager.info:
            case manager.info.INFO:
                self.page5Layout.update_gui()
            case manager.info.DETECTION_SETTINGS:
                self.page7Layout.update_gui()
            case manager.info.PLOT:
                if manager.detection_change:
                    manager.detection_change = False
                    self.page6Layout.update_gui()

    def change_layout(self) -> bool:
        """Handles layout changes, stopping camera previews.

        Returns:
            bool: Always True.
        """
        cam_corridor.stop_preview_window()
        cam_box.stop_preview_window()
        return True


class CorridorLayout(Layout):
    """Layout for controlling lights, motors, and scale in the corridor."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the CorridorLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        """Draws the motor, scale and LEDs controls."""
        self.draw_motor_buttons("MOTOR1", 4, 2, motor_corridor1)
        self.draw_motor_buttons("MOTOR2", 9, 2, motor_corridor2)
        self.draw_motor_edit_buttons(14, 2)

        self.rfid_reader_label: Label = self.create_and_add_label(
            "RFID\nReader: ", 1, 3, 9, 2, "black"
        )
        key = "RFID_READER"
        possible_values = Active.values()
        index = Active.get_index_from_value(manager.rfid_reader)
        self.rfid_reader_button = self.create_and_add_toggle_button(
            key,
            1,
            11,
            7,
            2,
            possible_values,
            index,
            self.toggle_rfid_reader_button,
            "Activation of the RFID reader: ON, OFF",
        )

        self.thresholds_label: Label = self.create_and_add_label(
            "Corridor\nCycle: ", 1, 23, 9, 2, "black"
        )
        key = "CORRIDOR_CYCLE_MODE"
        possible_values = CycleDay.values()
        index = CycleDay.get_index_from_value(settings.get("CORRIDOR_CYCLE_MODE"))
        self.thresholds_button = self.create_and_add_toggle_button(
            key,
            1,
            31,
            7,
            2,
            possible_values,
            index,
            self.toggle_corridor_cycle_button,
            "Corridor cycle mode (thresholds, exposure and lights): "
            "AUTO (day/night), DAY, NIGHT",
        )

        self.calibrate_scale: PushButton = self.create_and_add_button(
            "CALIBRATE SCALE",
            4,
            22,
            16,
            2,
            self.calibrate_scale_clicked,
            "Calibrate the scale using a known weight",
        )
        self.tare_scale: PushButton = self.create_and_add_button(
            "TARE SCALE",
            6,
            22,
            16,
            2,
            self.tare_scale_clicked,
            "Tare the scale to zero",
        )
        self.get_weight: PushButton = self.create_and_add_button(
            "GET WEIGHT",
            9,
            22,
            16,
            2,
            self.get_weight_clicked,
            "Get the weight in grams",
        )
        self.get_temperature: PushButton = self.create_and_add_button(
            "GET TEMPERATURE",
            11,
            22,
            16,
            2,
            self.get_temperature_clicked,
            "Get the temperature and humidity",
        )

    def draw_motor_buttons(
        self, name: str, row: int, column: int, motor: Motor | MotorOld | NullMotor
    ) -> None:
        """Draws buttons for a specific motor.

        Args:
            name (str): The motor name.
            row (int): The row position.
            column (int): The column position.
            motor (Motor | MotorOld | NullMotor): The motor object.
        """
        open_name: str = "OPEN " + name
        open_door: PushButton = self.create_and_add_button(
            open_name, row, column, 16, 2, motor.open, "Open the door"
        )
        close_name: str = "CLOSE " + name
        close_door: PushButton = self.create_and_add_button(
            close_name, row + 2, column, 16, 2, motor.close, "Close the door"
        )

        self.buttons.append(open_door)
        self.buttons.append(close_door)

    def draw_motor_edit_buttons(self, row: int, column: int) -> None:
        """Draws one button per corridor motor to edit its angles/times and
        test OPEN/CLOSE. Motors 1 and 2 always show; motors 3 and 4 only show
        if active (MOTOR3_CORRIDOR / MOTOR4_CORRIDOR) and actually wired up as
        a real Motor -- on old-HAT hardware motor_corridor3/4 are always
        NullMotor regardless of that setting. An inactive motor's row is
        skipped entirely rather than left blank, so motors compact upward.
        """
        entries = [
            (None, "MOTOR1 VALUES", motor_corridor1, "MOTOR1_VALUES"),
            (None, "MOTOR2 VALUES", motor_corridor2, "MOTOR2_VALUES"),
            ("MOTOR3_CORRIDOR", "MOTOR3 VALUES", motor_corridor3, "MOTOR3_VALUES"),
            ("MOTOR4_CORRIDOR", "MOTOR4 VALUES", motor_corridor4, "MOTOR4_VALUES"),
        ]
        row_offset = 0
        for active_key, name, motor, values_key in entries:
            if active_key is not None and (
                settings.get(active_key) != Active.ON or not isinstance(motor, Motor)
            ):
                continue
            edit_button: PushButton = self.create_and_add_button(
                name,
                row + row_offset * 2,
                column,
                16,
                2,
                partial(show_motor_edit_dialog, self, name, motor, values_key),
                f"Edit {name}'s open/close angles and times, and test OPEN/CLOSE",
            )
            self.buttons.append(edit_button)
            row_offset += 1

    def toggle_rfid_reader_button(self, value: str, key: str) -> None:
        """Toggles the RFID reader setting.

        Args:
            value (str): The new RFID reader value.
            key (str): The setting key.
        """
        manager.rfid_reader = Active[value]
        settings.set(key, value)
        self.window.layout.update_status_label_buttons()

    def toggle_corridor_cycle_button(self, value: str, key: str) -> None:
        """Sets the corridor day/night mode for thresholds, exposure and lights."""
        settings.set(key, value)
        cam_corridor.change = True
        manager.check_corridor_lights()

    def tare_scale_clicked(self) -> None:
        """Initiates scale taring."""
        manager.taring_scale = True

    def calibrate_scale_clicked(self) -> None:
        """Opens the scale calibration wizard."""
        # Block calibration if the system is busy
        if not manager.state.can_calibrate_scale():
            QMessageBox.information(
                self.window,
                "CALIBRATION",
                (
                    "Calibration is not available while a subject is in the box "
                    "or a detection is in progress."
                ),
            )
            return

        wiz = ScaleCalibrationWizard(scale, self.window)
        wiz.exec_()

    def cancel_calibration(self) -> None:
        """Cancels scale calibration (placeholder)."""
        pass

    def get_weight_clicked(self) -> None:
        """Gets the current weight from the scale."""
        if manager.getting_weights:
            manager.log_weight = True
        else:
            weight = scale.get_weight()
            weight_str = f"weight: {weight:.2f} g"
            log.info(weight_str)

    def get_temperature_clicked(self) -> None:
        """Gets the current temperature and humidity."""
        _, _, temp_str = temp_sensor.get_temperature()

    def update_gui(self) -> None:
        if manager.rfid_changed:
            manager.rfid_changed = False
            self.rfid_reader_button.index = Active.get_index_from_value(
                manager.rfid_reader
            )
            self.rfid_reader_button.value = self.rfid_reader_button.possible_values[
                self.rfid_reader_button.index
            ]
            self.rfid_reader_button.update_style()


class BoxLayout(Layout):
    """Layout for controlling the box."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the BoxLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        """Draws the motor, scale, LEDs and ports controls.

        Content is organized into up to two columns, compacted left with no
        gap: column 1 is the box scale controls (if SCALE_BOX is active) plus
        the motor buttons (if any box motor is active); column 2 is the
        visible/IR light controls (if either is active) plus the LED/WATER
        BPOD port buttons (if any port is active). If column 1 has nothing to
        show, column 2 takes its slot instead of leaving a blank column.
        """
        motor_active_keys = (
            "MOTOR1_BOX",
            "MOTOR2_BOX",
            "MOTOR3_BOX",
            "MOTOR4_BOX",
            "MOTOR5_BOX",
            "MOTOR6_BOX",
            "MOTOR7_BOX",
        )
        any_motor_active = any(settings.get(k) == Active.ON for k in motor_active_keys)
        has_column1 = manager.use_of_box_chip and (
            settings.get("SCALE_BOX") == Active.ON or any_motor_active
        )

        is_bpod = manager.controller_type == ControllerEnum.BPOD
        any_port_active = is_bpod and any(
            v == Active.ON for v in settings.get("BPOD_BEHAVIOR_PORTS")
        )
        any_light_active = manager.use_of_box_chip and (
            settings.get("VISIBLE_LIGHT_BOX") == Active.ON
            or settings.get("IR_LIGHT_BOX") == Active.ON
        )
        has_column2 = any_light_active or any_port_active

        n_columns = int(has_column1) + int(has_column2)

        # Column slots: column 1 always at the first slot; column 2 takes the
        # second slot if column 1 is present, otherwise takes the first.
        first_col, second_col = 2, 20
        row = 1
        column1_col = first_col
        column2_col = first_col if not has_column1 else second_col

        if has_column1:
            left_row = row
            if settings.get("SCALE_BOX") == Active.ON:
                self.calibrate_scale_box: PushButton = self.create_and_add_button(
                    "CALIBRATE SCALE",
                    left_row,
                    column1_col,
                    16,
                    2,
                    self.calibrate_scale_box_clicked,
                    "Calibrate the box scale using a known weight",
                )
                self.tare_scale_box: PushButton = self.create_and_add_button(
                    "TARE SCALE",
                    left_row + 2,
                    column1_col,
                    16,
                    2,
                    self.tare_scale_box_clicked,
                    "Tare the box scale to zero",
                )
                self.get_weight_box: PushButton = self.create_and_add_button(
                    "GET WEIGHT",
                    left_row + 4,
                    column1_col,
                    16,
                    2,
                    self.get_weight_box_clicked,
                    "Get the box weight in grams",
                )
                left_row += 7
            self.draw_box_motor_edit_buttons(left_row, column1_col)

        if has_column2:
            right_row = row
            if any_light_active:
                if settings.get("VISIBLE_LIGHT_BOX") == Active.ON:
                    self.visible_label: Label = self.create_and_add_label(
                        "Visible\nLight: ", right_row, column2_col + 1, 9, 2, "black"
                    )
                    key = "VISIBLE_BOX"
                    possible_values = Cycle.values()
                    index = Cycle.get_index_from_value(manager.visible_box_cycle)
                    self.visible_button = self.create_and_add_toggle_button(
                        key,
                        right_row,
                        column2_col + 9,
                        7,
                        2,
                        possible_values,
                        index,
                        self.toggle_visible_button,
                        "Visible light in the box: ON, OFF, AUTO",
                    )
                    right_row += 2

                if settings.get("IR_LIGHT_BOX") == Active.ON:
                    self.ir_label: Label = self.create_and_add_label(
                        "IR\nLight: ", right_row, column2_col + 1, 9, 2, "black"
                    )
                    key = "IR_BOX"
                    possible_values = Cycle.values()
                    index = Cycle.get_index_from_value(manager.ir_box_cycle)
                    self.ir_button = self.create_and_add_toggle_button(
                        key,
                        right_row,
                        column2_col + 9,
                        7,
                        2,
                        possible_values,
                        index,
                        self.toggle_ir_button,
                        "Infrared light in the box: ON, OFF, AUTO",
                    )
                    right_row += 2

                right_row += 1

            if any_port_active:
                behavior_ports = settings.get("BPOD_BEHAVIOR_PORTS")
                row_offset = 0
                for i in range(8):
                    if behavior_ports[i] != Active.ON:
                        continue

                    button1 = self.create_and_add_button(
                        "LED" + str(i + 1),
                        row_offset * 2 + right_row,
                        column2_col,
                        8,
                        2,
                        partial(self.led_clicked, i + 1),
                        "Light the LED" + str(i),
                    )
                    self.buttons.append(button1)

                    button2 = self.create_and_add_button(
                        "WATER" + str(i + 1),
                        row_offset * 2 + right_row,
                        column2_col + 8,
                        8,
                        2,
                        partial(self.water_clicked, i + 1),
                        "Deliver water for 0.1 seconds" + str(i),
                    )
                    self.buttons.append(button2)
                    row_offset += 1

        if n_columns == 0:
            log.info("BoxLayout: nothing to draw (no active box hardware)")

    def draw_box_motor_edit_buttons(self, row: int, column: int) -> None:
        """Draws one button per active box motor (1 through 7) to edit its
        angles/times and test OPEN/CLOSE (same dialog as the corridor motors).

        Each button only appears if its motor is active (MOTOR1_BOX .. MOTOR7_BOX)
        and actually wired up as a real Motor. An inactive motor's row is
        skipped entirely rather than left blank, so e.g. a lone active motor 4
        takes motor 1's position.
        """
        entries = [
            ("MOTOR1_BOX", "MOTOR1 VALUES", motor_box1, "MOTOR1_BOX_VALUES"),
            ("MOTOR2_BOX", "MOTOR2 VALUES", motor_box2, "MOTOR2_BOX_VALUES"),
            ("MOTOR3_BOX", "MOTOR3 VALUES", motor_box3, "MOTOR3_BOX_VALUES"),
            ("MOTOR4_BOX", "MOTOR4 VALUES", motor_box4, "MOTOR4_BOX_VALUES"),
            ("MOTOR5_BOX", "MOTOR5 VALUES", motor_box5, "MOTOR5_BOX_VALUES"),
            ("MOTOR6_BOX", "MOTOR6 VALUES", motor_box6, "MOTOR6_BOX_VALUES"),
            ("MOTOR7_BOX", "MOTOR7 VALUES", motor_box7, "MOTOR7_BOX_VALUES"),
        ]
        row_offset = 0
        for active_key, name, motor, values_key in entries:
            if settings.get(active_key) != Active.ON or not isinstance(motor, Motor):
                continue
            edit_button: PushButton = self.create_and_add_button(
                name,
                row + row_offset * 2,
                column,
                16,
                2,
                partial(show_motor_edit_dialog, self, name, motor, values_key),
                f"Edit {name}'s open/close angles and times, and test OPEN/CLOSE",
            )
            self.buttons.append(edit_button)
            row_offset += 1

    def toggle_visible_button(self, value: str, key: str) -> None:
        manager.visible_box_cycle = Cycle[value]
        settings.set(key, value)
        match value:
            case "OFF":
                visible_light_box.off()
            case "ON":
                visible_light_box.on()
            case "AUTO":
                manager.check_box_lights()

    def toggle_ir_button(self, value: str, key: str) -> None:
        manager.ir_box_cycle = Cycle[value]
        settings.set(key, value)
        match value:
            case "OFF":
                ir_light_box.off()
            case "ON":
                ir_light_box.on()
            case "AUTO":
                manager.check_box_lights()

    def tare_scale_box_clicked(self) -> None:
        """Initiates box scale taring (deferred to the background loop, same
        as the corridor scale, to avoid concurrent I2C access)."""
        manager.taring_scale_box = True

    def calibrate_scale_box_clicked(self) -> None:
        """Opens the scale calibration wizard for the box scale."""
        # Block calibration if the system is busy (same guard as corridor,
        # since a subject mid-transit can also disturb a box weight reading)
        if not manager.state.can_calibrate_scale():
            QMessageBox.information(
                self.window,
                "CALIBRATION",
                (
                    "Calibration is not available while a subject is in the box "
                    "or a detection is in progress."
                ),
            )
            return

        wiz = ScaleCalibrationWizard(scale_box, self.window)
        wiz.exec_()

    def get_weight_box_clicked(self) -> None:
        """Gets and logs the current weight from the box scale.

        Unlike the corridor's GET WEIGHT, this doesn't defer through
        manager.getting_weights/log_weight -- those are coupled to the
        corridor's automatic subject-tracking state machine, which the box
        scale has no equivalent of.
        """
        weight = scale_box.get_weight()
        log.info(f"box weight: {weight:.2f} g")

    def disable_all(self) -> None:
        """Disables all port buttons."""
        for b in self.buttons:
            b.setEnabled(False)

    def enable_all(self) -> None:
        """Enables all port buttons."""
        for b in self.buttons:
            b.setEnabled(True)

    def led_clicked(self, i=0) -> None:
        """Toggles the LED for a specific port.

        Args:
            i (int): Port index (1-based).
        """
        self.disable_all()
        QTimer.singleShot(1500, self.enable_all)

        if not manager.task.bpod.connected:
            manager.task.functions = manager.functions
            manager.task.bpod.connect(manager.task.execute_function)
            close = True
        else:
            close = False
        manager.task.bpod.led(i, close)

    def water_clicked(self, i=0) -> None:
        """Delivers water for a specific port.

        Args:
            i (int): Port index (1-based).
        """
        self.disable_all()
        QTimer.singleShot(1500, self.enable_all)

        if not manager.task.bpod.connected:
            manager.task.functions = manager.functions
            manager.task.bpod.connect(manager.task.execute_function)
            close = True
        else:
            close = False
        manager.task.bpod.water(i, close)


class VirtualMouseLayout(Layout):
    """Layout for simulating mouse actions on the touchscreen."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the VirtualMouseLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        """Draws the virtual mouse controls."""

        if manager.controller_type == ControllerEnum.BPOD:
            row_bpod = 2
            if (
                settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON
                or settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN
            ):
                col_bpod = 3
                col_auto = 21
                col_touch = 21
                if settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON:
                    row_auto = 2
                    row_touch = 14
                else:
                    row_touch = 2
            else:
                row_bpod = 2
                col_bpod = 12
        else:
            if settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON:
                col_auto = 12
                row_auto = 2
                col_touch = 12
                row_touch = 14
            else:
                row_touch = 2
                col_touch = 12

        if manager.controller_type == ControllerEnum.BPOD:
            for i in range(8):
                button = self.create_and_add_button(
                    "POKE" + str(i + 1),
                    i * 2 + row_bpod,
                    col_bpod,
                    14,
                    2,
                    partial(self.poke_clicked, i + 1),
                    "Virtual mouse poke in port" + str(i),
                )
                self.buttons.append(button)

        self._anm: AutoNoMouseBase | None = None

        if settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON:
            self.auto_no_mouse_button = self.create_and_add_button(
                "▶  AutoNoMouse",
                row_auto,
                col_auto,
                15,
                2,
                self.auto_no_mouse_clicked,
                "Start/stop the automated virtual-mouse agent",
                color="lightblue",
            )

            # Build custom autonomouse parameters automatically
            # based on the PARAMS list.
            self._col_auto = col_auto
            self._inject_param_widgets: dict = {}
            self._inject_param_row_start = row_auto + 2
            row_after = self._build_inject_param_widgets()

            # Inject button first, then N / Interval below it.
            self.inject_button = self.create_and_add_button(
                "Inject Trials",
                row_after + 2,
                col_auto,
                15,
                2,
                self._inject_trials,
                "Inject N mock trials",
                "lightgreen",
            )

            self.create_and_add_label(
                "N inject",
                row_after + 4,
                col_auto,
                10,
                2,
                "black",
                description="Number of mock trials to inject",
            )

            self.n_inject_edit = self.create_and_add_line_edit(
                "300", row_after + 4, col_auto + 10, 4, 2, lambda: None
            )

            self.create_and_add_label(
                "Interval (s)",
                row_after + 6,
                col_auto,
                10,
                2,
                "black",
                description="Interval (in s) between trial injections",
            )

            self.interval_inject_edit = self.create_and_add_line_edit(
                "0.1", row_after + 6, col_auto + 10, 4, 2, lambda: None
            )
        else:
            row_touch = 4

        if settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN:
            self.x_label = self.create_and_add_label(
                "X coordinate",
                row_touch,
                col_touch,
                10,
                2,
                "black",
                description="X coordinate of the touch screen",
            )

            self.y_label = self.create_and_add_label(
                "Y coordinate",
                row_touch + 2,
                col_touch,
                10,
                2,
                "black",
                description="Y coordinate of the touch screen",
            )

            self.x_line_edit = self.create_and_add_line_edit(
                "0", row_touch, col_touch + 10, 4, 2, self.coordinates_changed
            )
            self.y_line_edit = self.create_and_add_line_edit(
                "0", row_touch + 2, col_touch + 10, 4, 2, self.coordinates_changed
            )
            self.touch = self.create_and_add_button(
                "Touch the screen",
                row_touch + 4,
                col_touch,
                15,
                2,
                self.touch_clicked,
                "Touching the screen at the specified coordinates",
                color="lightgreen",
            )

    def coordinates_changed(self) -> None:
        """Handles changes in the coordinate fields."""
        return

    def poke_clicked(self, i=0) -> None:
        """Simulates a poke action.

        Args:
            i (int): Port index (1-based).
        """
        if not manager.task.bpod.connected:
            manager.task.functions = manager.functions
            manager.task.bpod.connect(manager.task.execute_function)
            close = True
        else:
            close = False
        manager.task.bpod.poke(i, close)

    def touch_clicked(self) -> None:
        """Simulates a touch action at the specified coordinates."""
        try:
            timestamp = time_utils.now_timestamp()
            x = int(self.x_line_edit.text())
            y = int(self.y_line_edit.text())
            if x >= 0 and y >= 0:
                manager.touch_trigger.trigger(x, y, timestamp)
        except Exception:
            self.x_line_edit.setText("0")
            self.y_line_edit.setText("0")

    def _build_inject_param_widgets(self) -> int:
        """Create one label and line_edit per PARAMS entry
        and then returns next free row for next labels."""
        col_auto = self._col_auto
        self._inject_param_widgets.clear()
        row = self._inject_param_row_start
        for param in manager.auto_no_mouse.PARAMS:
            self.create_and_add_label(
                param.label, row, col_auto, 10, 2, "black", description=param.tooltip
            )
            if param.type_ is bool:
                widget = QCheckBox()
                widget.setChecked(bool(param.default))
                widget.setToolTip(param.tooltip)
                self.addWidget(widget, row, col_auto + 10, 2, 4)
                widget.stateChanged.connect(self._on_param_changed)
            else:
                widget = self.create_and_add_line_edit(
                    str(param.default), row, col_auto + 10, 4, 2, lambda: None
                )
                widget.editingFinished.connect(self._on_param_changed)
            self._inject_param_widgets[param.name] = widget
            row += 2
        return row

    def _get_inject_kwargs(self) -> dict:
        result = {}
        for param in manager.auto_no_mouse.PARAMS:
            widget = self._inject_param_widgets.get(param.name)
            if widget is None:
                result[param.name] = param.default
                continue
            if isinstance(widget, QCheckBox):
                result[param.name] = widget.isChecked()
            else:
                try:
                    result[param.name] = param.clamp(widget.text())
                except (ValueError, TypeError):
                    widget.setText(str(param.default))
                    result[param.name] = param.default
        return result

    def _get_n_inject(self) -> int:
        try:
            v = int(self.n_inject_edit.text())
            return max(1, v)
        except ValueError:
            self.n_inject_edit.setText("10")
            return 10

    def _get_interval_inject(self) -> float:
        try:
            v = float(self.interval_inject_edit.text())
            return max(0.0, v)
        except ValueError:
            self.interval_inject_edit.setText("1.0")
            return 1.0

    def auto_no_mouse_clicked(self) -> None:
        """Toggle AutoNoMouse on/off."""
        if self._anm is not None and self._anm.running:
            self._anm.stop()
            self._anm = None
            self.auto_no_mouse_button.setText("▶  AutoNoMouse")
            self.auto_no_mouse_button.setStyleSheet("background-color: lightblue;")
            return

        self._anm = manager.auto_no_mouse
        self._anm.task = manager.task
        # Update autonomouse parameters based on the current values in the GUI.
        kwargs = self._get_inject_kwargs()
        for param in self._anm.PARAMS:
            if param.name in kwargs:
                setattr(self._anm, param.name, kwargs[param.name])
        self._anm.start()
        self.auto_no_mouse_button.setText("■  AutoNoMouse")
        self.auto_no_mouse_button.setStyleSheet("background-color: salmon;")

    def update_gui(self) -> None:
        if self._anm is not None and not self._anm.running:
            self._anm = None
            self.auto_no_mouse_button.setText("▶  AutoNoMouse")
            self.auto_no_mouse_button.setStyleSheet("background-color: lightblue;")
        injector = manager.auto_no_mouse
        if (
            hasattr(self, "inject_button")
            and not injector.injecting
            and self.inject_button.text() == "■  Stop Inject"
        ):
            self.inject_button.setText("Inject Trials")
            self.inject_button.setStyleSheet("background-color: lightgreen;")

    def _on_param_changed(self) -> None:
        if self._anm is not None and self._anm.running:
            self._anm.update_params(**self._get_inject_kwargs())

    def _inject_trials(self) -> None:
        injector = manager.auto_no_mouse
        if injector.injecting:
            injector.stop_inject()
            self.inject_button.setText("Inject Trials")
            self.inject_button.setStyleSheet("background-color: lightgreen;")
            return
        # Stop autonomouse if running so run_trial doesn't conflict
        if self._anm is not None and self._anm.running:
            self._anm.stop()
            self._anm = None
            self.auto_no_mouse_button.setText("▶  AutoNoMouse")
            self.auto_no_mouse_button.setStyleSheet("background-color: lightblue;")
        kwargs = self._get_inject_kwargs()
        injector.task = manager.task
        injector.inject_trials(
            self._get_n_inject(), interval=self._get_interval_inject(), **kwargs
        )
        self.inject_button.setText("■  Stop Inject")
        self.inject_button.setStyleSheet("background-color: salmon;")


class FunctionsLayout(Layout):
    """Layout for executing user-defined functions."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the FunctionsLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        """Draws the function buttons."""
        for i in range(98):
            row = 1 + i // 2 * 2
            column = 0 if i % 2 == 0 else 18
            function_name = manager.functions[i + 1].__doc__
            if function_name is None:
                text = "FUNCTION" + str(i + 1)
            else:
                text = str(i + 1) + "." + function_name
            button = self.create_and_add_button(
                text,
                row,
                column,
                18,
                2,
                partial(self.function_clicked, i + 1),
                "Execute user-defined function" + str(i + 1),
            )
            fm = QFontMetrics(button.font())
            text = fm.elidedText(text, Qt.ElideRight, 14 * self.column_width)
            button.setText(text)
            self.buttons.append(button)

    def function_clicked(self, i=0) -> None:
        """Executes the selected user function.

        Args:
            i (int): Function index.
        """
        try:
            manager.functions[i]()
        except Exception:
            log.error(
                "Error running function" + str(i), exception=traceback.format_exc()
            )


class DetectionLayout(Layout):
    """Layout for configuring corridor settings."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the DetectionLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.color_area1_str = "rgb" + str(tuple(settings.get("COLOR_AREA1")))
        self.color_area2_str = "rgb" + str(tuple(settings.get("COLOR_AREA2")))
        self.color_area3_str = "rgb" + str(tuple(settings.get("COLOR_AREA3")))
        self.color_area4_str = "rgb" + str(tuple(settings.get("COLOR_AREA4")))
        self.draw()

    def draw(self) -> None:
        """Draws the corridor configuration options."""
        self.lbs: list[LabelButtons] = []
        # box area index (1-4) -> its "defined with code" label
        self.custom_area_code_labels: dict[int, Label] = {}
        # is_day last applied; None forces the first apply
        self._dim_is_day: bool | None = None

        if manager.use_of_corridor:
            # Ensure corridor areas carry a night threshold (index 5); older
            # saved settings only have 5 elements. Defaults to the day value.
            for i in range(1, 5):
                key = "AREA" + str(i) + "_CORRIDOR"
                v = list(settings.get(key))
                if len(v) == 5:
                    v.append(v[4])
                    settings.set(key, v)

            self.draw_area_buttons_corridor(
                "AREA1_CORRIDOR", 2, 2, self.color_area1_str
            )
            self.draw_area_buttons_corridor(
                "AREA2_CORRIDOR", 2, 22, self.color_area2_str
            )
            self.draw_area_buttons_corridor(
                "AREA3_CORRIDOR", 2, 42, self.color_area3_str
            )
            self.draw_area_buttons_corridor(
                "AREA4_CORRIDOR", 2, 62, self.color_area4_str
            )
            self.draw_mice_buttons("DETECTION_OF_MOUSE_CORRIDOR", 0, 2)

            self.detection_corridor_label: Label = self.create_and_add_label(
                "View detection corridor: ", 0, 55, 20, 2, "black"
            )
            key = "VIEW_DETECTION_CORRIDOR"
            possible_values = settings.get_values(key)
            index = settings.get_index(key)
            self.button_corridor = self.create_and_add_toggle_button(
                key,
                0,
                75,
                5,
                2,
                possible_values,
                index,
                self.toggle_corridor,
                "View the detection in the corridor",
            )

        self.draw_area_buttons_box("AREA1_BOX", 2, 123, self.color_area1_str)
        self.draw_area_buttons_box("AREA2_BOX", 2, 143, self.color_area2_str)
        self.draw_area_buttons_box("AREA3_BOX", 2, 163, self.color_area3_str)
        self.draw_area_buttons_box("AREA4_BOX", 2, 183, self.color_area4_str)
        self.draw_camera_options()
        self.draw_mice_buttons("DETECTION_OF_MOUSE_BOX", 0, 123)

        key = "USAGE1_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area1_box_button = self.create_and_add_toggle_button(
            key,
            4,
            123,
            17,
            2,
            possible_values,
            index,
            self.toggle_area1_box,
            "If animals are allowed to be in this area",
        )

        key = "USAGE2_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area2_box_button = self.create_and_add_toggle_button(
            key,
            4,
            143,
            17,
            2,
            possible_values,
            index,
            self.toggle_area2_box,
            "If animals are allowed to be in this area",
        )

        key = "USAGE3_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area3_box_button = self.create_and_add_toggle_button(
            key,
            4,
            163,
            17,
            2,
            possible_values,
            index,
            self.toggle_area3_box,
            "If animals are allowed to be in this area",
        )

        key = "USAGE4_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area4_box_button = self.create_and_add_toggle_button(
            key,
            4,
            183,
            17,
            2,
            possible_values,
            index,
            self.toggle_area4_box,
            "If animals are allowed to be in this area",
        )

        self.detection_box_label: Label = self.create_and_add_label(
            "View detection box: ", 0, 179, 20, 2, "black"
        )
        key = "VIEW_DETECTION_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.button_box = self.create_and_add_toggle_button(
            key,
            0,
            195,
            5,
            2,
            possible_values,
            index,
            self.toggle_box,
            "View the detection in the box",
        )

    def close(self) -> None:
        """Closes the layout (no-op)."""
        return

    def update_gui(self) -> None:
        """Dims the controls that are inactive.

        Box areas whose USAGE is OFF have all their controls (labels and
        buttons) hidden. An area overridden by a CustomAreaBase (its shape is
        defined in code, see manager.custom_areas) hides only its position
        controls (left/right/top/bottom) and shows a "defined with code"
        label instead — its threshold stays editable, since that part of the
        area is still GUI-driven. For the corridor, the day/night controls
        that are not the effective ones are greyed. The effective day/night
        follows CORRIDOR_CYCLE_MODE: DAY/NIGHT force it, AUTO follows the
        cycle.
        """
        # box areas: hide every control of an area whose USAGE is OFF, or
        # just the position controls of an area overridden by code
        for lb in self.lbs:
            if lb.name.startswith("AREA") and lb.name.endswith("_BOX"):
                area_index = int(lb.name[4])
                usage_key = lb.name.replace("AREA", "USAGE")
                active = settings.get(usage_key) != AreaActive.OFF
                overridden = area_index in manager.custom_areas
                if lb.direction == "threshold":
                    lb.set_visible(active)
                else:
                    lb.set_visible(active and not overridden)

        for area_index, label in self.custom_area_code_labels.items():
            usage_key = "USAGE" + str(area_index) + "_BOX"
            active = settings.get(usage_key) != AreaActive.OFF
            label.setVisible(active and area_index in manager.custom_areas)

        # corridor day/night: re-apply only when the effective day/night changes
        is_day = manager.corridor_cycle_is_day
        if is_day == self._dim_is_day:
            return
        self._dim_is_day = is_day
        for lb in self.lbs:
            direction = lb.direction
            if direction in ("thr_night", "exposure_night"):
                lb.set_dimmed(is_day)  # night controls: dim when effectively day
            elif direction == "exposure_day":
                lb.set_dimmed(not is_day)  # day control: dim when effectively night
            elif direction == "thr_day" and "CORRIDOR" in lb.name:
                lb.set_dimmed(not is_day)  # corridor day threshold: dim at night

    def draw_mice_buttons(self, name: str, row: int, column: int) -> None:
        """Draws detection limit buttons.

        Args:
            name (str): The name of the setting.
            row (int): The row position.
            column (int): The column position.
        """
        width = 10
        for direction in ("empty_limit", "subject_limit"):
            lb = LabelButtons(name, direction, row, column, width, "black", self)
            self.lbs.append(lb)
            column += 26

    def draw_area_buttons_corridor(
        self, name: str, row: int, column: int, color: str
    ) -> None:
        """Draws area buttons for the corridor.

        Args:
            name (str): The name of the area.
            row (int): The row position.
            column (int): The column position.
            color (str): The color of the label.
        """
        self.label1: Label = self.create_and_add_label(name, row, column, 16, 2, color)
        row += 2
        for direction in (
            "left",
            "right",
            "top",
            "bottom",
            "thr_day",
            "thr_night",
        ):
            lb = LabelButtons(name, direction, row, column, 8, color, self)
            self.lbs.append(lb)
            row += 2

    def draw_area_buttons_box(
        self, name: str, row: int, column: int, color: str
    ) -> None:
        """Draws area buttons for the box.

        Args:
            name (str): The name of the area.
            row (int): The row position.
            column (int): The column position.
            color (str): The color of the label.
        """
        width_res = settings.get("CAM_BOX_RESOLUTION")[0]
        height_res = settings.get("CAM_BOX_RESOLUTION")[1]
        self.label2: Label = self.create_and_add_label(name, row, column, 16, 2, color)
        row += 4
        position_row = row
        for direction in (
            "left",
            "right",
            "top",
            "bottom",
            "threshold",
        ):
            lb = LabelButtons(
                name,
                direction,
                row,
                column,
                8,
                color,
                self,
                width_res=width_res,
                height_res=height_res,
            )
            self.lbs.append(lb)
            row += 2

        # Shown instead of the position controls (left/right/top/bottom)
        # when this area is overridden by a project CustomAreaBase: its
        # polygons/circles, so the shape stays visible even though there's
        # no draggable position control for it.
        area_index = int(name[4])  # "AREA2_BOX" -> 2
        override = manager.custom_areas.get(area_index)
        lines = ["defined with code"]
        if override is not None:
            for poly in override.polygons:
                lines.append("poly: " + str(poly))
            for circle in override.circles:
                lines.append("circle: " + str(list(circle)))
        code_label = self.create_and_add_label(
            "\n".join(lines), position_row, column, 16, 8, color
        )
        code_label.setWordWrap(True)
        code_label.setVisible(False)
        self.custom_area_code_labels[area_index] = code_label

    def draw_camera_options(self) -> None:
        """Draws camera adjustment options."""
        row = 2
        column = 81
        width = 10
        color = "black"

        if manager.use_of_corridor:
            self.label_corridor: Label = self.create_and_add_label(
                "CORRIDOR ADJUSTMENTS", row, column, 20, 2, color
            )
            row += 2

            lb = LabelButtons(
                "LENS_POSITION_CORRIDOR",
                "lens_position",
                row,
                column,
                width,
                color,
                self,
            )
            self.lbs.append(lb)
            row += 2
            lb = LabelButtons(
                "SHARPNESS_CORRIDOR",
                "sharpness",
                row,
                column,
                width,
                color,
                self,
            )
            self.lbs.append(lb)
            row += 2
            lb = LabelButtons(
                "EXPOSURE_DAY_CORRIDOR",
                "exposure_day",
                row,
                column,
                width + 2,
                color,
                self,
                width2=2,
            )
            self.lbs.append(lb)
            row += 2
            lb = LabelButtons(
                "EXPOSURE_NIGHT_CORRIDOR",
                "exposure_night",
                row,
                column,
                width + 2,
                color,
                self,
                width2=2,
            )
            self.lbs.append(lb)
            row += 2

        row = 2
        column = 102
        width = 10

        self.label_box: Label = self.create_and_add_label(
            "BOX ADJUSTMENTS", row, column, 18, 2, color
        )
        row += 2

        lb = LabelButtons(
            "LENS_POSITION_BOX",
            "lens_position",
            row,
            column,
            width,
            color,
            self,
        )
        self.lbs.append(lb)
        row += 2

        lb = LabelButtons(
            "SHARPNESS_BOX",
            "sharpness",
            row,
            column,
            width,
            color,
            self,
        )
        self.lbs.append(lb)
        row += 2

        lb = LabelButtons(
            "EXPOSURE_BOX",
            "exposure",
            row,
            column,
            width,
            color,
            self,
        )
        self.lbs.append(lb)
        row += 2

    def _camera_changed(self, box: bool = True, corridor: bool = False) -> None:
        if box:
            cam_box.change = True
        if corridor:
            cam_corridor.change = True

    def toggle_area1_box(self, value: str, key: str) -> None:
        """Toggles area 1 box usage.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(box=True)

    def toggle_area2_box(self, value: str, key: str) -> None:
        """Toggles area 2 box usage.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(box=True)

    def toggle_area3_box(self, value: str, key: str) -> None:
        """Toggles area 3 box usage.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(box=True)

    def toggle_area4_box(self, value: str, key: str) -> None:
        """Toggles area 4 box usage.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(box=True)

    def toggle_corridor(self, value: str, key: str) -> None:
        """Toggles corridor detection view.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(corridor=True)

    def toggle_box(self, value: str, key: str) -> None:
        """Toggles box detection view.

        Args:
            value (str): The new value.
            key (str): The setting key.
        """
        settings.set(key, value)
        self._camera_changed(box=True)


class InfoLayout(Layout):
    """Layout for displaying system information logs."""

    ROW_COLORS = {
        "START": QColor("#e6f2ff"),
        "END": QColor("#e6f2ff"),
        "ERROR": QColor("#ffe6e6"),
        "ALARM": QColor("#ffe6e6"),
    }

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the InfoLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self._events_df: pd.DataFrame = pd.DataFrame()
        self.draw()

    def draw(self) -> None:
        """Draws the events table."""
        self.events_table = QTableWidget()
        self.events_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.events_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.events_table.setSelectionMode(QTableWidget.SingleSelection)
        self.events_table.setWordWrap(False)
        self.events_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.verticalHeader().setMinimumSectionSize(1)
        self.events_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.events_table.verticalHeader().setDefaultSectionSize(26)
        self.events_table.horizontalHeader().setVisible(False)
        self.events_table.horizontalHeader().setStretchLastSection(True)
        self.events_table.horizontalHeader().setDefaultSectionSize(26)
        self.events_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.events_table.setMinimumWidth(198 * self.column_width)
        f = QFont("Monospace")
        f.setStyleHint(QFont.TypeWriter)
        f.setPointSize(11)
        self.events_table.setFont(f)
        self.events_table.cellDoubleClicked.connect(
            lambda row, _: self.on_row_double_clicked(row)
        )
        self.addWidget(self.events_table, 1, 2, 16, 198)
        self.update_gui()

    def update_gui(self) -> None:
        """Updates the displayed events logs."""
        self._events_df = manager.events.df.tail(10).reset_index(drop=True)
        df = self._events_df

        if df.empty:
            self.events_table.setRowCount(0)
            return

        columns = list(df.columns)
        self.events_table.setColumnCount(len(columns))
        self.events_table.setHorizontalHeaderLabels(columns)
        self.events_table.setRowCount(len(df))

        for i, (_, row) in enumerate(df.iterrows()):
            t = str(row.get("type", "")).upper()
            color = self.ROW_COLORS.get(t)
            for j, col in enumerate(columns):
                item = QTableWidgetItem(str(row.get(col, "")))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if color:
                    item.setBackground(color)
                self.events_table.setItem(i, j, item)

        for i in range(len(df)):
            self.events_table.setRowHeight(i, 26)

        col_widths = {"date": 130, "type": 60, "subject": 80}
        for j, col in enumerate(columns):
            if col in col_widths:
                self.events_table.setColumnWidth(j, col_widths[col])

    def on_row_double_clicked(self, row: int) -> None:
        """Shows full row data in a dialog on double-click."""
        df = self._events_df
        if df.empty or row >= len(df):
            return
        row_data = df.iloc[row]
        text = "\n".join(f"{k}: {v}" for k, v in row_data.items())
        text = text.replace("  |  ", "\n")
        self.show_text_dialog(text)
        self.events_table.clearSelection()

    def show_text_dialog(self, text: str) -> None:
        """Shows a read-only dialog with the given text."""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("")
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        layout.addWidget(text_edit)
        btn = QPushButton("OK")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.resize(500, 400)
        dialog.exec_()


class CorridorPlotLayout(Layout):
    """Layout for displaying the corridor plot."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        """Initializes the CorridorPlotLayout.

        Args:
            window (GuiWindow): The parent window.
            rows (int): Number of rows.
            columns (int): Number of columns.
        """
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.draw()

    def draw(self) -> None:
        """Draws the plot area."""
        self.plot_label = QLabel()
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.addWidget(self.plot_label, 0, 0, self.rows, self.columns)

        self.pixmap = QPixmap()

        self.subjects = manager.subjects.df["name"].tolist()
        self.plot_width = (self.columns * self.column_width) / dpi
        self.plot_height = (self.rows * self.row_height) / dpi

    def update_gui(self) -> None:
        """Updates the plot with the latest data."""
        pixmap = QPixmap()
        try:
            subjects_df = manager.subjects.df
            active_states = dict(
                zip(subjects_df["name"], subjects_df["active"], strict=False)
            )
            figure = corridor_plot(
                manager.events.df.copy(),
                self.subjects,
                self.plot_width,
                self.plot_height,
                active_states=active_states,
            )
            pixmap = create_pixmap(figure)
        except Exception:
            log.error(
                "Can not create corridor plot",
                exception=traceback.format_exc(),
            )

        if not pixmap.isNull():
            self.plot_label.setPixmap(pixmap)
        else:
            self.plot_label.setText("Plot could not be generated")


class ScaleCalibrationWizard(QWizard):
    """
    4-step wizard to calibrate the scale:
      1) Tare with empty platform
      2) Place a known weight and enter grams
      3) Verify reading with the weight on
      4) Remove weight and verify near-zero reading
    """

    def __init__(self, scale_obj: Scale | NullScale, parent=None) -> None:
        """Initializes the ScaleCalibrationWizard.

        Args:
            scale_obj (Scale | NullScale): The scale device to calibrate (the
                corridor `scale` or the `scale_box`).
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.scale = scale_obj
        self.setWindowTitle("Scale Calibration")
        self.resize(560, 300)

        # Shared state
        self.known_weight_g: float | None = None
        weight_key = getattr(
            scale_obj, "weight_to_calibrate_key", "SCALE_WEIGHT_TO_CALIBRATE"
        )
        self.default_weight = float(settings.get(weight_key) or 0.0)

        # Pages
        self.page1 = Step1TarePage()
        self.page2 = Step2KnownWeightPage(self.default_weight)
        self.page3 = Step3VerifyWithWeightPage()
        self.page4 = Step4VerifyNoWeightPage()

        self.addPage(self.page1)
        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)

        # Optional: classic wizard look
        self.setOption(QWizard.NoBackButtonOnStartPage, True)

    # Expose helpers so pages can reuse them
    def read_scale_grams(self) -> float:
        """Read weight from your device API.

        Returns:
            float: The current weight in grams.
        """
        return float(self.scale.get_weight())


class Step1TarePage(QWizardPage):
    """Step 1: Tare the scale with an empty platform."""

    def __init__(self) -> None:
        """Initializes Step1TarePage."""
        super().__init__()
        self.setTitle("Step 1/4 — Tare")
        lay = QVBoxLayout(self)

        lbl = QLabel(
            "We are going to calibrate the scale.\n\n"
            "1) Make sure there is nothing on the platform.\n"
            "2) Click Next to tare the scale."
        )
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        self.status = QLabel("")
        lay.addWidget(self.status)
        lay.addStretch(1)

    def validatePage(self) -> bool:
        """Called when Next is pressed. Perform Tare here.

        Returns:
            bool: True if tare is successful, False otherwise.
        """
        wiz: ScaleCalibrationWizard = self.wizard()  # type: ignore
        try:
            wiz.scale.tare()
            self.status.setText("Tare completed successfully.")
            return True
        except Exception:
            self.status.setText("Tare failed. Please try again.")
            QMessageBox.warning(self, "Calibration", "Tare failed. Try again.")
            return False


class Step2KnownWeightPage(QWizardPage):
    """Step 2: Place a known weight and enter its value (grams)."""

    def __init__(self, default_weight: float) -> None:
        """Initializes Step2KnownWeightPage.

        Args:
            default_weight (float): The default weight to show in the input.
        """
        super().__init__()
        self.setTitle("Step 2/4 — Known Weight")
        lay = QVBoxLayout(self)

        lbl = QLabel(
            "Place a known weight on the platform now.\n"
            "Enter its value in grams and click Next.\n\n"
            "Tip: For better accuracy, use a calibration weight close to your "
            "animals' body weight."
        )
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        row = QHBoxLayout()
        row.addWidget(QLabel("Known weight (g):"))
        self.edit = QLineEdit()
        if default_weight > 0:
            self.edit.setPlaceholderText(str(default_weight))
        row.addWidget(self.edit)
        lay.addLayout(row)

        self.status = QLabel("")
        lay.addWidget(self.status)
        lay.addStretch(1)

    def _parse_weight(self) -> float | None:
        """Parses the weight from the input field.

        Returns:
            float | None: The parsed weight or None if invalid.
        """
        text = self.edit.text().strip()
        if not text and self.edit.placeholderText():
            text = self.edit.placeholderText()
        try:
            val = float(text)
            return val
        except Exception:
            return None

    def validatePage(self) -> bool:
        """When Next is pressed: validate, store, and calibrate.

        Returns:
            bool: True if calibration is successful, False otherwise.
        """
        wiz: ScaleCalibrationWizard = self.wizard()  # type: ignore
        val = self._parse_weight()
        if val is None:
            self.status.setText("Invalid value. Please enter a number.")
            QMessageBox.warning(self, "Calibration", "Enter a numeric value in grams.")
            return False
        if val <= 0.1:
            self.status.setText("Invalid value. It must be > 0.1 g.")
            QMessageBox.warning(
                self, "Calibration", "Known weight must be greater than 0.1 g."
            )
            return False

        try:
            wiz.scale.calibrate(val)
        except Exception:
            self.status.setText("Calibration failed. Please try again.")
            QMessageBox.critical(self, "Calibration", "Calibration failed.")
            return False

        wiz.known_weight_g = val
        self.status.setText(f"Calibration factor applied for {val:.2f} g.")
        return True


class Step3VerifyWithWeightPage(QWizardPage):
    """Step 3: Verify reading with the known weight on the platform."""

    def __init__(self) -> None:
        """Initializes Step3VerifyWithWeightPage."""
        super().__init__()
        self.setTitle("Step 3/4 — Verify with Weight")
        lay = QVBoxLayout(self)

        lbl = QLabel(
            "The scale has been calibrated.\n"
            "Click 'Get weight' to verify the reading with the weight on."
        )
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        btns = QHBoxLayout()
        self.btn_get = QPushButton("Get weight")
        self.btn_get.clicked.connect(self._on_get)
        btns.addWidget(self.btn_get)
        btns.addStretch(1)
        lay.addLayout(btns)

        self.status = QLabel("")
        lay.addWidget(self.status)
        lay.addStretch(1)

    def _on_get(self) -> None:
        """Handles the 'Get weight' button click."""
        wiz: ScaleCalibrationWizard = self.wizard()  # type: ignore
        try:
            grams = wiz.read_scale_grams()
            kw = wiz.known_weight_g
            if kw is not None:
                diff = grams - kw
                self.status.setText(
                    f"Reading: {grams:.2f} g  (Δ={diff:+.2f} g vs {kw:.2f} g)."
                )
            else:
                self.status.setText(f"Reading: {grams:.2f} g.")
        except Exception:
            self.status.setText("Failed to read the scale. Try again.")


class Step4VerifyNoWeightPage(QWizardPage):
    """Step 4: Remove the weight and verify near-zero reading."""

    def __init__(self) -> None:
        """Initializes Step4VerifyNoWeightPage."""
        super().__init__()
        self.setTitle("Step 4/4 — Final Check (No Weight)")
        lay = QVBoxLayout(self)

        lbl = QLabel(
            "Remove the weight from the platform.\n"
            "Click 'Get weight' and check the reading is close to zero.\n\n"
            "If results are not as expected, restart the calibration process."
        )
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        btns = QHBoxLayout()
        self.btn_get = QPushButton("Get weight")
        self.btn_get.clicked.connect(self._on_get)
        btns.addWidget(self.btn_get)
        btns.addStretch(1)
        lay.addLayout(btns)

        self.status = QLabel("")
        lay.addWidget(self.status)
        lay.addStretch(1)

    def _on_get(self) -> None:
        """Handles the 'Get weight' button click."""
        wiz: ScaleCalibrationWizard = self.wizard()  # type: ignore
        try:
            grams = wiz.read_scale_grams()
            self.status.setText(f"Reading: {grams:.2f} g.")
        except Exception:
            self.status.setText("Failed to read the scale. Try again.")
