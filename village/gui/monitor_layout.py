from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from village.app.dev import dev
from village.app.settings import settings
from village.app.status import status
from village.app.utils import utils
from village.classes.enums import Cycle
from village.gui.layout import Label, Layout, PushButton

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
            "open_angle": 0,
            "Max area empty": 0,
            "top": 1,
            "close_angle": 1,
            "Max area one mouse": 1,
            "right": 2,
            "bottom": 3,
            "threshold": 4,
            "threshold_day": 4,
            "threshold_night": 4,
            "grams": -1,
        }
        self.mapping_dict_max = {
            "left": 640,
            "open_angle": 360,
            "Max area empty": 1000000,
            "top": 480,
            "close_angle": 360,
            "Max area one mouse": 1000000,
            "right": 640,
            "bottom": 480,
            "threshold": 255,
            "threshold_day": 255,
            "threshold_night": 255,
            "grams": 1000,
        }
        self.mapping_dict_increase = {
            "left": "\u2192",
            "open_angle": "\u2191",
            "Max area empty": "\u2191",
            "top": "\u2193",
            "close_angle": "\u2191",
            "Max area one mouse": "\u2191",
            "right": "\u2192",
            "bottom": "\u2193",
            "threshold": "\u2191",
            "threshold_day": "\u2191",
            "threshold_night": "\u2191",
            "grams": "\u2191",
        }
        self.mapping_dict_decrease = {
            "left": "\u2190",
            "open_angle": "\u2193",
            "Max area empty": "\u2193",
            "top": "\u2191",
            "close_angle": "\u2193",
            "Max area one mouse": "\u2193",
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
            str(self.label_value), row, column, 6, 2, color, right_aligment=True
        )

        regular_buttons = ["left", "right", "top", "bottom"]

        val = 8 if self.direction in regular_buttons else 10
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

        if self.name == "SCALE_CALIBRATION_VALUE":
            settings.set(self.name, self.label_value)
        else:
            coords = settings.get(self.name)
            coords = list(coords)
            coords[self.index] = int(self.label_value)
            settings.set(self.name, coords)

            if self.name == "AREA1_CORRIDOR":
                dev.cam_corridor.area1 = coords
            elif self.name == "AREA2_CORRIDOR":
                dev.cam_corridor.area2 = coords
            elif self.name == "AREA3_CORRIDOR":
                dev.cam_corridor.area3 = coords
            elif self.name == "AREA4_CORRIDOR":
                dev.cam_corridor.area4 = coords
            elif self.name == "AREA1_BOX":
                dev.cam_box.area1 = coords
            elif self.name == "AREA2_BOX":
                dev.cam_box.area2 = coords
            elif self.name == "AREA3_BOX":
                dev.cam_box.area3 = coords
            elif self.name == "AREA4_BOX":
                dev.cam_box.area4 = coords

            dev.cam_corridor.change = True
            dev.cam_box.change = True


class MonitorLayout(Layout):
    def __init__(self, window: GuiWindow, df: DataFrame) -> None:
        super().__init__(window)
        self.color_area1_str = "rgb" + str(settings.get("COLOR_AREA1"))
        self.color_area2_str = "rgb" + str(settings.get("COLOR_AREA2"))
        self.color_area3_str = "rgb" + str(settings.get("COLOR_AREA3"))
        self.color_area4_str = "rgb" + str(settings.get("COLOR_AREA4"))
        self.draw(df)

    def draw(self, df: DataFrame) -> None:
        self.monitor_button.setDisabled(True)

        self.qpicamera2_corridor = dev.cam_corridor.start_preview_window()
        self.qpicamera2_box = dev.cam_box.start_preview_window()

        self.addWidget(self.qpicamera2_corridor, 5, 0, 29, 90)
        self.addWidget(self.qpicamera2_box, 5, 122, 29, 90)

        key = "VIEW_DETECTION_CORRIDOR"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.button_corridor = self.create_and_add_toggle_button(
            key,
            34,
            0,
            30,
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
            34,
            122,
            30,
            2,
            possible_values,
            index,
            self.toggle_box,
            "View the detection in the box",
            complete_name=True,
        )

        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []

        self.draw_area_buttons_corridor("AREA1_CORRIDOR", 36, 1, self.color_area1_str)
        self.draw_area_buttons_corridor("AREA2_CORRIDOR", 36, 33, self.color_area2_str)
        self.draw_area_buttons_corridor("AREA3_CORRIDOR", 36, 65, self.color_area3_str)

        self.draw_area_buttons_box("AREA1_BOX", 36, 123, self.color_area1_str)
        self.draw_area_buttons_box("AREA2_BOX", 36, 147, self.color_area2_str)
        self.draw_area_buttons_box("AREA3_BOX", 36, 171, self.color_area3_str)
        self.draw_area_buttons_box("AREA4_BOX", 36, 195, self.color_area4_str)

        key = "USAGE1_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area1_box_button = self.create_and_add_toggle_button(
            key,
            48,
            123,
            20,
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
            48,
            147,
            20,
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
            48,
            171,
            20,
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
            48,
            195,
            20,
            2,
            possible_values,
            index,
            self.toggle_area4_box,
            "If animals are allowed to be in this area",
        )

        self.cycle_label: Label = self.create_and_add_label(
            "Cycle: ", 5, 91, 12, 2, "black"
        )

        possible_values = Cycle.values()
        index = Cycle.get_index_from_value(status.cycle)
        self.cycle_button = self.create_and_add_toggle_button(
            key,
            5,
            100,
            20,
            2,
            possible_values,
            index,
            self.toggle_cycle_button,
            "Cycle of the corridor: AUTO, DAY, NIGHT, OFF",
        )

        self.draw_motor_buttons("MOTOR1", 9, 91, dev.motor1)
        self.draw_motor_buttons("MOTOR2", 15, 91, dev.motor2)

        self.calibrate_scale: PushButton = self.create_and_add_button(
            "CALIBRATE SCALE",
            23,
            95,
            20,
            2,
            self.calibrate_scale_clicked,
            "Calibrate the scale using a known weight",
        )
        self.tare_scale: PushButton = self.create_and_add_button(
            "TARE SCALE",
            25,
            95,
            20,
            2,
            self.tare_scale_clicked,
            "Tare the scale to zero",
        )
        self.get_weight: PushButton = self.create_and_add_button(
            "GET WEIGHT",
            27,
            95,
            20,
            2,
            self.get_weight_clicked,
            "Get the weight in grams",
        )
        # self.weight_result_label: Label = self.create_and_add_label(
        #    "", 32, 96, 20, 2, "black"
        # )
        self.get_temperature: PushButton = self.create_and_add_button(
            "GET TEMPERATURE",
            29,
            95,
            20,
            2,
            self.get_temperature_clicked,
            "Get the temperature and humidity",
        )
        # self.temp_result_label: Label = self.create_and_add_label(
        #    "", 36, 96, 20, 2, "black"
        # )

        self.events_table = self.create_and_add_table(df, 36, 96, 30, 20)

        self.draw_mice_buttons("DETECTION_OF_MOUSE_CORRIDOR", 34, 32)
        self.draw_mice_buttons("DETECTION_OF_MOUSE_BOX", 34, 154)

        self.get_temperature_clicked()
        self.get_weight_clicked()

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
            lb = LabelButtons(name, direction, row, column, 12, color, self)
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
            lb = LabelButtons(name, direction, row, column, 8, color, self)
            self.lbs.append(lb)
            row += 2

    def draw_motor_buttons(
        self, name: str, row: int, column: int, motor: Motor
    ) -> None:
        open_name: str = "OPEN " + name
        open_door: PushButton = self.create_and_add_button(
            open_name, row, column, 15, 2, motor.open, "Open the door"
        )
        close_name: str = "CLOSE " + name
        close_door: PushButton = self.create_and_add_button(
            close_name, row, column + 15, 15, 2, motor.close, "Close the door"
        )

        self.buttons.append(open_door)
        self.buttons.append(close_door)

        row += 2
        for direction in ("open_angle", "close_angle"):
            lb = LabelButtons(
                name + "_VALUES", direction, row, column + 3, 12, "black", self
            )
            self.lbs.append(lb)
            row += 2

    def draw_mice_buttons(self, name: str, row: int, column: int) -> None:
        width = 13
        for direction in ("Max area empty", "Max area one mouse"):
            lb = LabelButtons(name, direction, row, column, width, "black", self)
            self.lbs.append(lb)
            column += 29
            width += 4

    def toggle_corridor(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_corridor.change = True

    def toggle_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_box.change = True

    def toggle_area1_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_box.change = True

    def toggle_area2_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_box.change = True

    def toggle_area3_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_box.change = True

    def toggle_area4_box(self, value: str, key: str) -> None:
        settings.set(key, value)
        dev.cam_box.change = True

    def toggle_cycle_button(self, value: str, key: str) -> None:
        status.cycle = Cycle[value]
        self.update_status_label(
            status.state.name,
            status.state.description,
            status.subject.name,
            status.task.name,
            status.cycle.value,
        )

    def tare_scale_clicked(self) -> None:
        print("Taring the scale")

    def calibrate_scale_clicked(self) -> None:
        val = settings.get("SCALE_CALIBRATION_VALUE")
        self.reply = QDialog()
        self.reply.setWindowTitle("Calibrate scale")
        self.reply.setGeometry(531, 266, 190, 110)
        layout = QVBoxLayout()
        label = QLabel("Enter the known weight in grams:")
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
                val = int(self.lineEdit.text())
                settings.set("SCALE_CALIBRATION_VALUE", val)
            except ValueError:
                pass

    def cancel_calibration(self) -> None:
        pass

    def get_weight_clicked(self) -> None:
        weight_result_value = "100g"
        utils.log("weight: " + weight_result_value)

    def get_temperature_clicked(self) -> None:
        temp_result_value = "23ºC / 30%"
        utils.log("temp: " + temp_result_value)

    def change_layout(self) -> bool:
        dev.cam_corridor.stop_window_preview()
        dev.cam_box.stop_window_preview()
        return True
