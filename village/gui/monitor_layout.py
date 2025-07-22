from __future__ import annotations

import traceback
from functools import partial
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from village.classes.enums import Actions, Active, Cycle, Info, ScreenActive
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.scale import scale
from village.devices.temp_sensor import temp_sensor
from village.gui.layout import Label, Layout, PushButton
from village.log import log
from village.manager import manager
from village.plots.corridor_plot import corridor_plot
from village.plots.create_pixmap import create_pixmap
from village.settings import settings

# from devices.bpod import bpod

if TYPE_CHECKING:
    from village.devices.motor import Motor
    from village.gui.gui_window import GuiWindow


class LabelButtons:
    def __init__(
        self,
        name: str,
        direction: str,
        row: int,
        column: int,
        width: int,
        color: str,
        layout: Layout,
    ) -> None:
        self.name = name
        self.direction = direction
        self.short_name = name.split("_")[0]
        self.mapping_dict_index = {
            "left": 0,
            "empty_limit": 0,
            "top": 1,
            "subject_limit": 1,
            "right": 2,
            "bottom": 3,
            "threshold": 4,
            "threshold_day": 4,
            "threshold_night": 5,
            "grams": -1,
        }
        self.mapping_dict_max = {
            "left": 640,
            "empty_limit": 1000000,
            "top": 480,
            "subject_limit": 1000000,
            "right": 640,
            "bottom": 480,
            "threshold": 255,
            "threshold_day": 255,
            "threshold_night": 255,
            "grams": 1000,
        }
        self.mapping_dict_increase = {
            "left": "\u2192",
            "empty_limit": "\u2191",
            "top": "\u2193",
            "subject_limit": "\u2191",
            "right": "\u2192",
            "bottom": "\u2193",
            "threshold": "\u2191",
            "threshold_day": "\u2191",
            "threshold_night": "\u2191",
            "grams": "\u2191",
        }
        self.mapping_dict_decrease = {
            "left": "\u2190",
            "empty_limit": "\u2193",
            "top": "\u2191",
            "subject_limit": "\u2193",
            "right": "\u2190",
            "bottom": "\u2191",
            "threshold": "\u2193",
            "threshold_day": "\u2193",
            "threshold_night": "\u2193",
            "grams": "\u2193",
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
            str(self.label_value), row, column, 4, 2, color, right_aligment=True
        )

        regular_buttons = ["left", "right", "top", "bottom"]

        val = 5 if self.direction in regular_buttons else 7
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

    def increase_value(self) -> None:
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
            else:
                self.label_value += 1
                self.label3.setText(str(self.label_value))

    def decrease_value(self) -> None:
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
            else:
                self.label_value -= 1
                self.label3.setText(str(self.label_value))

    def start_increasing(self) -> None:
        self.increase_value()
        self.timer_increase1.start()

    def start_decreasing(self) -> None:
        self.decrease_value()
        self.timer_decrease1.start()

    def stop_timer(self) -> None:
        self.timer_increase1.stop()
        self.timer_decrease1.stop()
        self.timer_increase2.stop()
        self.timer_decrease2.stop()

        if self.name == "SCALE_WEIGHT_TO_CALIBRATE":
            settings.set(self.name, self.label_value)
        else:
            coords = settings.get(self.name)
            coords = list(coords)
            coords[self.index] = int(self.label_value)
            settings.set(self.name, coords)

            if self.name == "AREA1_CORRIDOR":
                cam_corridor.area1 = coords
            elif self.name == "AREA2_CORRIDOR":
                cam_corridor.area2 = coords
            elif self.name == "AREA3_CORRIDOR":
                cam_corridor.area3 = coords
            elif self.name == "AREA4_CORRIDOR":
                cam_corridor.area4 = coords
            elif self.name == "AREA1_BOX":
                cam_box.area1 = coords
            elif self.name == "AREA2_BOX":
                cam_box.area2 = coords
            elif self.name == "AREA3_BOX":
                cam_box.area3 = coords
            elif self.name == "AREA4_BOX":
                cam_box.area4 = coords

            cam_corridor.change = True
            cam_box.change = True


class MonitorLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        rectangle = QWidget()
        rectangle.setStyleSheet("background-color: lightgray;")
        self.addWidget(rectangle, 5, 0, 30, 200)

        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []

        self.monitor_button.setDisabled(True)

        self.central_widget = QWidget(self.window)
        self.bottom_widget = QWidget(self.window)
        self.central_layout = QStackedLayout()
        self.addLayout(self.central_layout, 12, 83, 19, 34)

        self.page1 = QWidget(self.central_widget)
        self.page1.setStyleSheet("background-color:white")
        self.page1Layout = MotorLayout(self.window, 19, 34)
        self.page1.setLayout(self.page1Layout)

        self.page2 = QWidget(self.central_widget)
        self.page2.setStyleSheet("background-color:white")
        self.page2Layout = PortsLayout(self.window, 19, 34)
        self.page2.setLayout(self.page2Layout)

        self.page3 = QWidget(self.central_widget)
        self.page3.setStyleSheet("background-color:white")
        self.page3_layout = QVBoxLayout(self.page3)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.page3_sub_widget = QWidget()
        self.page3_sub_layout = FunctionsLayout(self.window, 16, 26)
        self.page3_sub_widget.setLayout(self.page3_sub_layout)

        self.scroll_area.setWidget(self.page3_sub_widget)

        self.page3_layout.addWidget(self.scroll_area)
        self.page3.setLayout(self.page3_layout)

        self.page4 = QWidget(self.central_widget)
        self.page4.setStyleSheet("background-color:white")
        self.page4Layout = VirtualMouseLayout(self.window, 19, 34)
        self.page4.setLayout(self.page4Layout)

        self.central_layout.addWidget(self.page1)
        self.central_layout.addWidget(self.page2)
        self.central_layout.addWidget(self.page3)
        self.central_layout.addWidget(self.page4)

        self.bottom_layout = QStackedLayout()
        self.addLayout(self.bottom_layout, 34, 0, 17, 200)

        self.page5 = QWidget(self.bottom_widget)
        self.page5.setStyleSheet("background-color:white")
        self.page5Layout = InfoLayout(self.window, 17, 200)
        self.page5.setLayout(self.page5Layout)

        self.page6 = QWidget(self.bottom_widget)
        self.page6.setStyleSheet("background-color:white")
        self.page6Layout = CorridorLayout(self.window, 17, 200)
        self.page6.setLayout(self.page6Layout)

        self.page7 = QWidget(self.bottom_widget)
        self.page7.setStyleSheet("background-color:white")
        self.page7Layout = CorridorPlotLayout(self.window, 17, 200)
        self.page7.setLayout(self.page7Layout)

        self.bottom_layout.addWidget(self.page5)
        self.bottom_layout.addWidget(self.page6)
        self.bottom_layout.addWidget(self.page7)

        self.rfid_reader_label: Label = self.create_and_add_label(
            "RFID reader: ", 6, 84, 12, 2, "black"
        )
        key = "RFID_READER"
        possible_values = Active.values()
        index = Active.get_index_from_value(manager.rfid_reader)
        self.rfid_reader_button = self.create_and_add_toggle_button(
            key,
            6,
            94,
            20,
            2,
            possible_values,
            index,
            self.toggle_rfid_reader_button,
            "Activation of the RFID reader: ON, OFF",
        )

        self.cycle_label: Label = self.create_and_add_label(
            "Cycle: ", 8, 84, 12, 2, "black"
        )
        key = "CYCLE"
        possible_values = Cycle.values()
        index = Cycle.get_index_from_value(manager.cycle)
        self.cycle_button = self.create_and_add_toggle_button(
            key,
            8,
            94,
            20,
            2,
            possible_values,
            index,
            self.toggle_cycle_button,
            "Cycle of the corridor: AUTO, DAY, NIGHT",
        )

        key = "ACTIONS"
        possible_values = Actions.values()
        index = Actions.get_index_from_value(manager.actions)
        text = (
            "Perform actions on the corridor, in the behavior ports or run "
            + "user-defined python functions."
        )
        self.actions_button = self.create_and_add_toggle_button(
            key,
            11,
            87,
            26,
            2,
            possible_values,
            index,
            self.toggle_actions_button,
            text,
            color="white",
        )

        key = "INFO"
        possible_values = Info.values()
        index = Info.get_index_from_value(manager.info)
        self.info_button = self.create_and_add_toggle_button(
            key,
            33,
            87,
            26,
            2,
            possible_values,
            index,
            self.toggle_info_button,
            "Info and values of the cameras or info about the system",
            color="white",
        )

        index = Info.get_index_from_string(manager.info.value)
        self.bottom_layout.setCurrentIndex(index)

        index = Actions.get_index_from_string(manager.actions.value)
        self.central_layout.setCurrentIndex(index)

        self.qpicamera2_corridor = cam_corridor.start_preview_window()
        self.qpicamera2_box = cam_box.start_preview_window()

        self.qpicamera2_corridor.setFixedSize(640, 480)
        self.qpicamera2_box.setFixedSize(640, 480)

        self.addWidget(self.qpicamera2_corridor, 5, 0, 28, 80)
        self.addWidget(self.qpicamera2_box, 5, 120, 28, 80)

    def toggle_cycle_button(self, value: str, key: str) -> None:
        manager.cycle = Cycle[value]
        settings.set(key, value)
        self.update_status_label_buttons()
        cam_corridor.change = True

    def toggle_rfid_reader_button(self, value: str, key: str) -> None:
        manager.rfid_reader = Active[value]
        settings.set(key, value)
        self.update_status_label_buttons()

    def toggle_actions_button(self, value: str, key: str) -> None:
        manager.actions = Actions[value]
        settings.set(key, value)
        index = Actions.get_index_from_string(value)
        self.central_layout.setCurrentIndex(index)
        self.actions_button.raise_()
        self.update_gui()

    def toggle_info_button(self, value: str, key: str) -> None:
        manager.info = Info[value]
        settings.set(key, value)
        index = Info.get_index_from_string(value)
        self.bottom_layout.setCurrentIndex(index)
        self.info_button.raise_()
        self.update_gui()

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if manager.rfid_changed:
            manager.rfid_changed = False
            self.rfid_reader_button.index = Active.get_index_from_value(
                manager.rfid_reader
            )
            self.rfid_reader_button.value = self.rfid_reader_button.possible_values[
                self.rfid_reader_button.index
            ]
            self.rfid_reader_button.update_style()
        match manager.info:
            case manager.info.SYSTEM_INFO:
                self.page5Layout.update_gui()
            case manager.info.DETECTION_SETTINGS:
                self.page6Layout.update_gui()
            case manager.info.DETECTION_PLOT:
                if manager.detection_change:
                    manager.detection_change = False
                    self.page7Layout.update_gui()

    def change_layout(self, auto: bool = False) -> bool:
        cam_corridor.stop_preview_window()
        cam_box.stop_preview_window()
        return True


class MotorLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        self.draw_motor_buttons("MOTOR1", 2, 2, motor1)
        self.draw_motor_buttons("MOTOR2", 2, 18, motor2)

        self.change_angles: PushButton = self.create_and_add_button(
            "CHANGE MOTOR ANGLES",
            6,
            6,
            22,
            2,
            self.change_angles_clicked,
            "Modify the angle values for the motors.",
        )
        self.calibrate_scale: PushButton = self.create_and_add_button(
            "CALIBRATE SCALE",
            9,
            6,
            22,
            2,
            self.calibrate_scale_clicked,
            "Calibrate the scale using a known weight",
        )
        self.tare_scale: PushButton = self.create_and_add_button(
            "TARE SCALE",
            11,
            6,
            22,
            2,
            self.tare_scale_clicked,
            "Tare the scale to zero",
        )
        self.get_weight: PushButton = self.create_and_add_button(
            "GET WEIGHT",
            13,
            6,
            22,
            2,
            self.get_weight_clicked,
            "Get the weight in grams",
        )
        self.get_temperature: PushButton = self.create_and_add_button(
            "GET TEMPERATURE",
            16,
            6,
            22,
            2,
            self.get_temperature_clicked,
            "Get the temperature and humidity",
        )

    def draw_motor_buttons(
        self, name: str, row: int, column: int, motor: Motor
    ) -> None:
        open_name: str = "OPEN " + name
        open_door: PushButton = self.create_and_add_button(
            open_name, row, column, 14, 2, motor.open, "Open the door"
        )
        close_name: str = "CLOSE " + name
        close_door: PushButton = self.create_and_add_button(
            close_name, row + 2, column, 14, 2, motor.close, "Close the door"
        )

        self.buttons.append(open_door)
        self.buttons.append(close_door)

    def tare_scale_clicked(self) -> None:
        manager.taring_scale = True

    def change_angles_clicked(self) -> None:
        motor1_open_val = settings.get("MOTOR1_VALUES")[0]
        motor1_close_val = settings.get("MOTOR1_VALUES")[1]
        motor2_open_val = settings.get("MOTOR2_VALUES")[0]
        motor2_close_val = settings.get("MOTOR2_VALUES")[1]
        self.reply = QDialog()
        self.reply.setWindowTitle("Motor angles")
        x = self.column_width * 83
        y = self.row_height * 19
        width = self.column_width * 32
        height = self.row_height * 12
        self.reply.setGeometry(x, y, width, height)
        layout = QVBoxLayout()

        label = QLabel("Motor1 open angle:")
        layout.addWidget(label)
        self.lineEdit1 = QLineEdit()
        self.lineEdit1.setPlaceholderText(str(motor1_open_val))
        layout.addWidget(self.lineEdit1)

        label = QLabel("Motor1 close angle:")
        layout.addWidget(label)
        self.lineEdit2 = QLineEdit()
        self.lineEdit2.setPlaceholderText(str(motor1_close_val))
        layout.addWidget(self.lineEdit2)

        label = QLabel("Motor2 open angle:")
        layout.addWidget(label)
        self.lineEdit3 = QLineEdit()
        self.lineEdit3.setPlaceholderText(str(motor2_open_val))
        layout.addWidget(self.lineEdit3)

        label = QLabel("Motor2 close angle:")
        layout.addWidget(label)
        self.lineEdit4 = QLineEdit()
        self.lineEdit4.setPlaceholderText(str(motor2_close_val))
        layout.addWidget(self.lineEdit4)

        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("CHANGE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        layout.addLayout(btns_layout)
        self.reply.setLayout(layout)

        self.btn_ok.clicked.connect(self.reply.accept)
        self.btn_cancel.clicked.connect(self.reply.reject)

        if self.reply.exec_():
            try:
                val1 = int(self.lineEdit1.text())
            except ValueError:
                val1 = int(motor1_open_val)
            try:
                val2 = int(self.lineEdit2.text())
            except ValueError:
                val2 = int(motor1_close_val)
            try:
                val3 = int(self.lineEdit3.text())
            except ValueError:
                val3 = int(motor2_open_val)
            try:
                val4 = int(self.lineEdit4.text())
            except ValueError:
                val4 = int(motor2_close_val)
            settings.set("MOTOR1_VALUES", (val1, val2))
            settings.set("MOTOR2_VALUES", (val3, val4))
            motor1.open_angle = val1
            motor1.close_angle = val2
            motor2.open_angle = val3
            motor2.close_angle = val4

    def calibrate_scale_clicked(self) -> None:
        if not manager.state.can_calibrate_scale():
            text = (
                "Calibration is not available if there is a subject in the box "
                + "or a detection in progress"
            )
            QMessageBox.information(
                self.window,
                "CALIBRATION",
                text,
            )

        scale.tare()
        val = settings.get("SCALE_WEIGHT_TO_CALIBRATE")
        self.reply = QDialog()
        self.reply.setWindowTitle("Calibrate scale")
        x = self.column_width * 65
        y = self.row_height * 22
        width = self.column_width * 32
        height = self.row_height * 8
        self.reply.setGeometry(x, y, width, height)
        layout = QVBoxLayout()
        text = "The scale has been tared. Make sure there was nothing on it, and now "
        text += "place an object of known weight on top.\n"
        text += "Enter the known weight value in grams:"
        label = QLabel(text)
        layout.addWidget(label)
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText(str(val))
        layout.addWidget(self.lineEdit)
        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("CALIBRATE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        layout.addLayout(btns_layout)
        self.reply.setLayout(layout)

        self.btn_ok.clicked.connect(self.reply.accept)
        self.btn_cancel.clicked.connect(self.reply.reject)

        if self.reply.exec_():
            try:
                if self.lineEdit.text() == "":
                    val = float(self.lineEdit.placeholderText())
                else:
                    val = float(self.lineEdit.text())
                if val > 0.1:
                    scale.calibrate(val)
                    log.info("Scale calibrated")
                else:
                    log.error("Invalid value. Scale not calibrated")
            except ValueError:
                log.error("Invalid value. Scale not calibrated")

    def cancel_calibration(self) -> None:
        pass

    def get_weight_clicked(self) -> None:
        if manager.getting_weights:
            manager.log_weight = True
        else:
            weight = scale.get_weight()
            weight_str = "weight: {:.2f} g".format(weight)
            log.info(weight_str)

    def get_temperature_clicked(self) -> None:
        _, _, temp_str = temp_sensor.get_temperature()


class PortsLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        for i in range(8):
            button1 = self.create_and_add_button(
                "LED" + str(i + 1),
                i * 2 + 2,
                2,
                14,
                2,
                partial(self.led_clicked, i + 1),
                "Light the LED" + str(i),
            )
            self.buttons.append(button1)

            button2 = self.create_and_add_button(
                "WATER" + str(i + 1),
                i * 2 + 2,
                18,
                14,
                2,
                partial(self.water_clicked, i + 1),
                "Deliver water for 0.1 seconds" + str(i),
            )
            self.buttons.append(button2)

    def led_clicked(self, i=0) -> None:
        # button.setEnabled(False)
        # QTimer.singleShot(2000, lambda: button.setEnabled(True))

        if not manager.task.bpod.connected:
            manager.task.bpod.connect(manager.functions)
            close = True
        else:
            close = False
        manager.task.bpod.led(i, close)

    def water_clicked(self, i=0) -> None:
        if not manager.task.bpod.connected:
            manager.task.bpod.connect(manager.functions)
            close = True
        else:
            close = False
        manager.task.bpod.water(i, close)


class VirtualMouseLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        for i in range(8):
            button = self.create_and_add_button(
                "POKE" + str(i + 1),
                i * 2 + 2,
                2,
                14,
                2,
                partial(self.poke_clicked, i + 1),
                "Virtual mouse poke in port" + str(i),
            )
            self.buttons.append(button)

        self.x_label = self.create_and_add_label(
            "X coordinate",
            2,
            22,
            12,
            2,
            "black",
            description="X coordinate of the touch screen",
        )

        self.y_label = self.create_and_add_label(
            "Y coordinate",
            6,
            22,
            12,
            2,
            "black",
            description="Y coordinate of the touch screen",
        )

        self.x_line_edit = self.create_and_add_line_edit(
            "0", 4, 21, 8, 2, self.coordinates_changed
        )
        self.y_line_edit = self.create_and_add_line_edit(
            "0", 8, 21, 8, 2, self.coordinates_changed
        )
        self.touch = self.create_and_add_button(
            "TOUCH SCREEN",
            11,
            18,
            14,
            2,
            self.touch_clicked,
            "Deliver water for 0.1 seconds" + str(i),
        )

        if settings.get("USE_SCREEN") != ScreenActive.TOUCHSCREEN:
            self.x_label.hide()
            self.y_label.hide()
            self.x_line_edit.hide()
            self.y_line_edit.hide()
            self.touch.hide()

    def coordinates_changed(self) -> None:
        return

    def poke_clicked(self, i=0) -> None:
        if not manager.task.bpod.connected:
            manager.task.bpod.connect(manager.functions)
            close = True
        else:
            close = False
        manager.task.bpod.poke(i, close)

    def touch_clicked(self) -> None:
        x = self.x_line_edit.text()
        y = self.y_line_edit.text()
        try:
            x = int(x)
            y = int(y)
            if x >= 0 and y >= 0:
                print(x, y)
                # TODO touch screen
        except Exception:
            self.x_line_edit.setText("0")
            self.y_line_edit.setText("0")


class FunctionsLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        for i in range(98):
            row = i // 2 * 2 + 1
            column = 2 if i % 2 == 0 else 14
            button = self.create_and_add_button(
                "FUNCTION" + str(i + 1),
                row,
                column,
                13,
                2,
                partial(self.function_clicked, i + 1),
                "Run the user-function" + str(i),
            )
            self.buttons.append(button)

    def function_clicked(self, i=0) -> None:
        try:
            manager.functions[i]()
        except Exception:
            log.error("Can not run function" + str(i), exception=traceback.format_exc())


class CorridorLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.color_area1_str = "rgb" + str(settings.get("COLOR_AREA1"))
        self.color_area2_str = "rgb" + str(settings.get("COLOR_AREA2"))
        self.color_area3_str = "rgb" + str(settings.get("COLOR_AREA3"))
        self.color_area4_str = "rgb" + str(settings.get("COLOR_AREA4"))
        self.draw()

    def draw(self) -> None:
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []

        self.draw_mice_buttons("DETECTION_OF_MOUSE_CORRIDOR", 0, 2)
        self.draw_mice_buttons("DETECTION_OF_MOUSE_BOX", 0, 121)

        self.draw_area_buttons_corridor("AREA1_CORRIDOR", 2, 2, self.color_area1_str)
        self.draw_area_buttons_corridor("AREA2_CORRIDOR", 2, 22, self.color_area2_str)
        self.draw_area_buttons_corridor("AREA3_CORRIDOR", 2, 42, self.color_area3_str)
        self.draw_area_buttons_corridor("AREA4_CORRIDOR", 2, 62, self.color_area4_str)

        self.draw_area_buttons_box("AREA1_BOX", 2, 121, self.color_area1_str)
        self.draw_area_buttons_box("AREA2_BOX", 2, 141, self.color_area2_str)
        self.draw_area_buttons_box("AREA3_BOX", 2, 161, self.color_area3_str)
        self.draw_area_buttons_box("AREA4_BOX", 2, 181, self.color_area4_str)

        key = "USAGE1_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area1_box_button = self.create_and_add_toggle_button(
            key,
            14,
            120,
            19,
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
            14,
            140,
            19,
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
            14,
            160,
            19,
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
            14,
            180,
            19,
            2,
            possible_values,
            index,
            self.toggle_area4_box,
            "If animals are allowed to be in this area",
        )

        key = "VIEW_DETECTION_CORRIDOR"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.button_corridor = self.create_and_add_toggle_button(
            key,
            0,
            55,
            25,
            2,
            possible_values,
            index,
            self.toggle_corridor,
            "View the detection in the corridor",
            complete_name=True,
        )

        key = "VIEW_DETECTION_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.button_box = self.create_and_add_toggle_button(
            key,
            0,
            175,
            25,
            2,
            possible_values,
            index,
            self.toggle_box,
            "View the detection in the box",
            complete_name=True,
        )

    def close(self) -> None:
        return

    def draw_mice_buttons(self, name: str, row: int, column: int) -> None:
        width = 9
        for direction in ("empty_limit", "subject_limit"):
            lb = LabelButtons(name, direction, row, column, width, "black", self)
            self.lbs.append(lb)
            column += 26

    def draw_area_buttons_corridor(
        self, name: str, row: int, column: int, color: str
    ) -> None:
        self.label1: Label = self.create_and_add_label(name, row, column, 16, 2, color)
        row += 2
        for direction in (
            "left",
            "right",
            "top",
            "bottom",
            "threshold_day",
            "threshold_night",
        ):
            lb = LabelButtons(name, direction, row, column, 9, color, self)
            self.lbs.append(lb)
            row += 2

    def draw_area_buttons_box(
        self, name: str, row: int, column: int, color: str
    ) -> None:
        self.label2: Label = self.create_and_add_label(name, row, column, 16, 2, color)
        row += 2
        for direction in (
            "left",
            "right",
            "top",
            "bottom",
            "threshold",
        ):
            lb = LabelButtons(name, direction, row, column, 9, color, self)
            self.lbs.append(lb)
            row += 2

    def toggle_area1_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_box.change = True

    def toggle_area2_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_box.change = True

    def toggle_area3_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_box.change = True

    def toggle_area4_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_box.change = True

    def toggle_corridor(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_corridor.change = True

    def toggle_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        cam_box.change = True


class InfoLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.draw()

    def draw(self) -> None:
        text = manager.events.df.tail(16).to_csv(sep="\t", index=False, header=False)
        self.events_text = self.create_and_add_label(text, 0, 2, 198, 17, "black")

    def update_gui(self) -> None:
        text = manager.events.df.tail(16).to_csv(sep="\t", index=False, header=False)
        self.events_text.setText(text)


class CorridorPlotLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.draw()

    def draw(self) -> None:
        self.plot_label = QLabel()
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.addWidget(self.plot_label, 0, 0, self.rows, self.columns)

        self.pixmap = QPixmap()

        self.subjects = manager.subjects.df["name"].tolist()
        self.plot_width = (self.columns * self.column_width) / dpi
        self.plot_height = (self.rows * self.row_height) / dpi

    def update_gui(self) -> None:
        pixmap = QPixmap()
        try:
            figure = corridor_plot(
                manager.events.df.copy(),
                self.subjects,
                self.plot_width,
                self.plot_height,
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
