from __future__ import annotations

from typing import TYPE_CHECKING, List

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton

from village.app_state import app
from village.camera import cam_box, cam_corridor
from village.motor import motor
from village.settings import settings
from village.window.layout import Layout

if TYPE_CHECKING:
    from village.window.gui_window import GuiWindow


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
            "no_mouse": 0,
            "top": 1,
            "close_angle": 1,
            "one_mouse": 1,
            "right": 2,
            "open_time": 2,
            "bottom": 3,
            "close_time": 3,
            "threshold": 4,
        }
        self.mapping_dict_max = {
            "left": 640,
            "open_angle": 360,
            "no_mouse": 1000000,
            "top": 480,
            "close_angle": 360,
            "one_mouse": 1000000,
            "right": 640,
            "open_time": 2000,
            "bottom": 480,
            "close_time": 2000,
            "threshold": 255,
        }
        self.mapping_dict_increase = {
            "left": "\u2192",
            "open_angle": "\u2191",
            "no_mouse": "\u2191",
            "top": "\u2193",
            "close_angle": "\u2191",
            "one_mouse": "\u2191",
            "right": "\u2192",
            "open_time": "\u2191",
            "bottom": "\u2193",
            "close_time": "\u2191",
            "threshold": "\u2191",
        }
        self.mapping_dict_decrease = {
            "left": "\u2190",
            "open_angle": "\u2193",
            "no_mouse": "\u2193",
            "top": "\u2191",
            "close_angle": "\u2193",
            "one_mouse": "\u2193",
            "right": "\u2190",
            "open_time": "\u2193",
            "bottom": "\u2191",
            "close_time": "\u2193",
            "threshold": "\u2193",
        }

        self.index = self.mapping_dict_index[direction]
        self.max = self.mapping_dict_max[direction]
        self.increase = self.mapping_dict_increase[direction]
        self.decrease = self.mapping_dict_decrease[direction]
        self.label_value = settings.get(name)[self.index]

        self.label2 = layout.create_and_add_label(
            direction, row, column, width, 2, color
        )
        column += width
        self.label3 = layout.create_and_add_label(
            str(self.label_value), row, column, 6, 2, color, right_aligment=True
        )

        regular_buttons = ["lef", "top", "right", "bottom"]

        val = 8 if self.direction in regular_buttons else 10
        column += val
        self.btn_decrease = layout.create_and_add_button(
            self.decrease, row, column, 2, 2, "white", self.start_decreasing
        )
        val = 2 if self.direction in regular_buttons else -2
        column += val
        self.btn_increase = layout.create_and_add_button(
            self.increase, row, column, 2, 2, "white", self.start_increasing
        )

        self.btn_increase.released.connect(self.stop_timer)
        self.btn_decrease.released.connect(self.stop_timer)

        self.timer_increase1 = QTimer()
        self.timer_increase1.setInterval(200)
        self.timer_increase1.setSingleShot(True)
        self.timer_increase2 = QTimer()
        self.timer_increase2.setInterval(25)

        self.timer_decrease1 = QTimer()
        self.timer_decrease1.setInterval(200)
        self.timer_decrease1.setSingleShot(True)
        self.timer_decrease2 = QTimer()
        self.timer_decrease2.setInterval(25)

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
        coords = settings.get(self.name)
        coords = list(coords)
        coords[self.index] = int(self.label_value)
        coords = tuple(coords)
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


class MonitorLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        self.disable(self.monitor_button)

        self.qpicamera2_corridor = cam_corridor.start_preview_window()
        self.qpicamera2_box = cam_box.start_preview_window()

        self.addWidget(self.qpicamera2_corridor, 5, 0, 31, 90)
        self.addWidget(self.qpicamera2_box, 5, 122, 31, 90)

        self.button_corridor = self.create_and_add_button_toggle(
            "DETECTION VIEW", 36, 0, 30, 2, True, self.toggle_corridor
        )

        self.button_box = self.create_and_add_button_toggle(
            "DETECTION VIEW", 36, 122, 30, 2, True, self.toggle_box
        )

        self.lbs: List[LabelButtons] = []
        self.buttons: List[QPushButton] = []

        self.draw_area_buttons("AREA1_CORRIDOR", 38, 0, app.color_area1_str)
        self.draw_area_buttons("AREA2_CORRIDOR", 38, 25, app.color_area2_str)
        self.draw_area_buttons("AREA3_CORRIDOR", 38, 50, app.color_area3_str)

        self.draw_area_buttons("AREA1_BOX", 38, 120, app.color_area1_str)
        self.draw_area_buttons("AREA2_BOX", 38, 145, app.color_area2_str)
        self.draw_area_buttons("AREA3_BOX", 38, 170, app.color_area3_str)
        self.draw_area_buttons("AREA4_BOX", 38, 195, app.color_area4_str)

        self.draw_motor_buttons("MOTOR1", 5, 91)
        self.draw_motor_buttons("MOTOR2", 17, 91)

        self.draw_mice_buttons("DETECTION_OF_MOUSE_CORRIDOR", 38, 75)
        self.draw_mice_buttons("DETECTION_OF_MOUSE_BOX", 46, 91)

    def draw_area_buttons(self, name: str, row: int, column: int, color: str) -> None:
        self.label1 = self.create_and_add_label(name, row, column, 16, 2, color)
        row += 2
        for direction in ("left", "right", "top", "bottom", "threshold"):
            lb = LabelButtons(name, direction, row, column, 8, color, self)
            self.lbs.append(lb)
            row += 2

    def draw_motor_buttons(self, name: str, row: int, column: int) -> None:
        open_name = "OPEN " + name
        open_door = self.create_and_add_button(
            open_name, row, column, 15, 2, "lightgreen", motor.open_door1
        )
        close_name = "CLOSE " + name
        close_door = self.create_and_add_button(
            close_name, row, column + 15, 15, 2, "lightcoral", motor.close_door1
        )

        self.buttons.append(open_door)
        self.buttons.append(close_door)

        row += 2
        for direction in ("open_angle", "close_angle", "open_time", "close_time"):
            lb = LabelButtons(
                name + "_VALUES", direction, row, column + 2, 12, "black", self
            )
            self.lbs.append(lb)
            row += 2

    def draw_mice_buttons(self, name: str, row: int, column: int) -> None:
        for direction in ("no_mouse", "one_mouse"):
            lb = LabelButtons(name, direction, row, column, 12, "black", self)
            self.lbs.append(lb)
            row += 2

    def toggle_corridor(self) -> None:
        print("TOGGLE CORRIDOR")

    def toggle_box(self) -> None:
        print("TOGGLE BOX")

    def change_layout(self) -> bool:
        cam_corridor.stop_window_preview()
        cam_box.stop_window_preview()
        return True
