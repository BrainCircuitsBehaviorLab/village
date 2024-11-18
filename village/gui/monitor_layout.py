from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from village.classes.enums import Actions, Active, Cycle, Info, State
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.scale import scale
from village.devices.temp_sensor import temp_sensor
from village.gui.layout import Label, Layout, PushButton
from village.log import log
from village.manager import manager
from village.settings import settings

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

        val = 6 if self.direction in regular_buttons else 8
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

        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []

        self.monitor_button.setDisabled(True)

        self.qpicamera2_corridor = cam_corridor.start_preview_window()
        self.qpicamera2_box = cam_box.start_preview_window()

        self.addWidget(self.qpicamera2_corridor, 4, 0, 30, 88)
        self.addWidget(self.qpicamera2_box, 4, 124, 30, 88)

        self.central_layout = QStackedLayout()
        self.addLayout(self.central_layout, 12, 88, 18, 36)

        self.page1 = QWidget()
        self.page1.setStyleSheet("background-color:white")
        self.page1Layout = MotorLayout(self.window, 20, 36)
        self.page1.setLayout(self.page1Layout)

        self.page2 = QWidget()
        self.page2.setStyleSheet("background-color:white")
        self.page2Layout = PortsLayout(self.window, 20, 36)
        self.page2.setLayout(self.page2Layout)

        self.page3 = QWidget()
        self.page3.setStyleSheet("background-color:white")
        self.page3_layout = QVBoxLayout(self.page3)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.page3_sub_widget = QWidget()
        self.page3_sub_layout = FunctionsLayout(self.window, 15, 26)
        self.page3_sub_widget.setLayout(self.page3_sub_layout)

        self.scroll_area.setWidget(self.page3_sub_widget)

        self.page3_layout.addWidget(self.scroll_area)
        self.page3.setLayout(self.page3_layout)

        self.central_layout.addWidget(self.page1)
        self.central_layout.addWidget(self.page2)
        self.central_layout.addWidget(self.page3)

        self.bottom_layout = QStackedLayout()
        self.addLayout(self.bottom_layout, 34, 0, 16, 212)
        self.page4 = QWidget()
        self.page4.setStyleSheet("background-color:white")
        self.page4Layout = InfoLayout(self.window, 16, 212)
        self.page4.setLayout(self.page4Layout)
        self.page5 = QWidget()
        self.page5.setStyleSheet("background-color:white")
        self.page5Layout = CorridorLayout(self.window, 16, 212)
        self.page5.setLayout(self.page5Layout)
        self.bottom_layout.addWidget(self.page4)
        self.bottom_layout.addWidget(self.page5)

        self.stop_button: PushButton = self.create_and_add_button(
            "",
            0,
            170,
            20,
            2,
            self.stop,
            "",
            "lightcoral",
        )

        self.tag_reader_label: Label = self.create_and_add_label(
            "Tag reader: ", 4, 90, 12, 2, "black"
        )
        key = "TAG_READER"
        possible_values = Active.values()
        index = Active.get_index_from_value(manager.tag_reader)
        self.cycle_button = self.create_and_add_toggle_button(
            key,
            4,
            100,
            20,
            2,
            possible_values,
            index,
            self.toggle_tag_reader_button,
            "Activation of the tag reader: ON, OFF",
        )

        self.cycle_label: Label = self.create_and_add_label(
            "Cycle: ", 6, 90, 12, 2, "black"
        )
        key = "CYCLE"
        possible_values = Cycle.values()
        index = Cycle.get_index_from_value(manager.cycle)
        self.cycle_button = self.create_and_add_toggle_button(
            key,
            6,
            100,
            20,
            2,
            possible_values,
            index,
            self.toggle_cycle_button,
            "Cycle of the corridor: AUTO, DAY, NIGHT",
        )

        self.info_label: Label = self.create_and_add_label(
            "Info: ", 32, 90, 33, 2, "black"
        )

        key = "INFO"
        possible_values = Info.values()
        index = Info.get_index_from_value(manager.info)
        self.info_button = self.create_and_add_toggle_button(
            key,
            32,
            100,
            20,
            2,
            possible_values,
            index,
            self.toggle_info_button,
            "Info and values of the cameras or info about the system",
        )

        self.actions_label: Label = self.create_and_add_label(
            "Actions: ", 10, 90, 33, 2, "black"
        )
        key = "ACTIONS"
        possible_values = Actions.values()
        index = Actions.get_index_from_value(manager.actions)
        self.actions_button = self.create_and_add_toggle_button(
            key,
            10,
            100,
            20,
            2,
            possible_values,
            index,
            self.toggle_actions_button,
            """
            Perform actions on the corridor, light the behavioral ports or run
            user-defined python functions
            """,
        )

        index = Info.get_index_from_string(manager.info.value)
        self.bottom_layout.setCurrentIndex(index)

        index = Actions.get_index_from_string(manager.actions.value)
        self.central_layout.setCurrentIndex(index)

        self.update_buttons()

    def stop(self) -> None:
        if manager.state.can_stop_task():
            manager.state = State.SAVE_MANUAL
            self.update_gui()
        elif manager.state.can_go_to_wait():
            manager.state = State.WAIT
            self.update_gui()

    def toggle_cycle_button(self, value: str, key: str) -> None:
        manager.cycle = Cycle[value]
        settings.set(key, value)
        self.update_status_label()

    def toggle_tag_reader_button(self, value: str, key: str) -> None:
        manager.tag_reader = Active[value]
        settings.set(key, value)
        self.update_status_label()

    def toggle_actions_button(self, value: str, key: str) -> None:
        manager.actions = Actions[value]
        settings.set(key, value)
        index = Actions.get_index_from_string(value)
        self.central_layout.setCurrentIndex(index)

    def toggle_info_button(self, value: str, key: str) -> None:
        manager.info = Info[value]
        settings.set(key, value)
        index = Info.get_index_from_string(value)
        self.bottom_layout.setCurrentIndex(index)

    def update_gui(self) -> None:
        self.update_status_label()
        self.update_buttons()
        match manager.info:
            case manager.info.SYSTEM_INFO:
                self.page4Layout.update_gui()
            case manager.info.DETECTION_SETTINGS:
                self.page5Layout.update_gui()

    def update_buttons(self) -> None:
        if manager.state.can_stop_task():
            self.stop_button.setText("STOP TASK")
            self.stop_button.setToolTip("Stop a running task")
            self.stop_button.show()
        elif manager.state.can_go_to_wait():
            self.stop_button.setText("GO TO WAIT STATE")
            self.stop_button.setToolTip(
                """
                If the systems thinks there is a subject in the corridor or the box,
                but there isn't, you can force going to the WAIT state.
                """
            )
            self.stop_button.show()
        else:
            self.stop_button.hide()

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
        self.draw_motor_buttons("MOTOR1", 0, 0, motor1)
        self.draw_motor_buttons("MOTOR2", 2, 0, motor2)

        self.change_angles: PushButton = self.create_and_add_button(
            "CHANGE MOTOR ANGLES",
            5,
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
            17,
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
            open_name, row, column, 16, 2, motor.open, "Open the door"
        )
        close_name: str = "CLOSE " + name
        close_door: PushButton = self.create_and_add_button(
            close_name, row, column + 18, 16, 2, motor.close, "Close the door"
        )

        self.buttons.append(open_door)
        self.buttons.append(close_door)

    def tare_scale_clicked(self) -> None:
        scale.tare()

    def change_angles_clicked(self) -> None:
        motor1_open_val = settings.get("MOTOR1_VALUES")[0]
        motor1_close_val = settings.get("MOTOR1_VALUES")[1]
        motor2_open_val = settings.get("MOTOR2_VALUES")[0]
        motor2_close_val = settings.get("MOTOR2_VALUES")[1]
        self.reply = QDialog()
        self.reply.setWindowTitle("Motor angles")
        x = self.column_width * 90
        y = self.row_height * 20
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
        val = settings.get("SCALE_CALIBRATION_VALUE")
        self.reply = QDialog()
        self.reply.setWindowTitle("Calibrate scale")
        x = self.column_width * 90
        y = self.row_height * 25
        width = self.column_width * 32
        height = self.row_height * 8
        self.reply.setGeometry(x, y, width, height)
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
        weight = scale.get_weight_string()
        log.info("weight: " + weight)

    def get_temperature_clicked(self) -> None:
        temp = temp_sensor.get_temperature_string()
        log.info("temperature and humidity: " + temp)


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
                i * 2 + 1,
                0,
                16,
                2,
                self.led_clicked,
                "Light the LED" + str(i),
            )
            self.buttons.append(button1)

            button2 = self.create_and_add_button(
                "WATER" + str(i + 1),
                i * 2 + 1,
                18,
                16,
                2,
                self.water_clicked,
                "Deliver water for 0.1 seconds" + str(i),
            )
            self.buttons.append(button2)

    def led_clicked(self) -> None:
        print("LED clicked")

    def water_clicked(self) -> None:
        print("water clicked")


class FunctionsLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.lbs: list[LabelButtons] = []
        self.buttons: list[QPushButton] = []
        self.draw()

    def draw(self) -> None:
        for i in range(98):
            row = i // 2 * 2
            column = 0 if i % 2 == 0 else 13
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
        print("function clicked " + str(i))


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

        self.draw_mice_buttons("DETECTION_OF_MOUSE_CORRIDOR", 0, 0)
        self.draw_mice_buttons("DETECTION_OF_MOUSE_BOX", 0, 124)

        self.draw_area_buttons_corridor("AREA1_CORRIDOR", 2, 0, self.color_area1_str)
        self.draw_area_buttons_corridor("AREA2_CORRIDOR", 2, 26, self.color_area2_str)
        self.draw_area_buttons_corridor("AREA3_CORRIDOR", 2, 52, self.color_area3_str)
        self.draw_area_buttons_corridor("AREA4_CORRIDOR", 2, 78, self.color_area4_str)

        self.draw_area_buttons_box("AREA1_BOX", 2, 126, self.color_area1_str)
        self.draw_area_buttons_box("AREA2_BOX", 2, 149, self.color_area2_str)
        self.draw_area_buttons_box("AREA3_BOX", 2, 172, self.color_area3_str)
        self.draw_area_buttons_box("AREA4_BOX", 2, 195, self.color_area4_str)

        key = "USAGE1_BOX"
        possible_values = settings.get_values(key)
        index = settings.get_index(key)
        self.area1_box_button = self.create_and_add_toggle_button(
            key,
            14,
            125,
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
            14,
            148,
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
            14,
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
            14,
            194,
            20,
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
            58,
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
            0,
            184,
            30,
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
        width = 14
        for direction in ("empty_limit", "subject_limit"):
            lb = LabelButtons(name, direction, row, column, width, "black", self)
            self.lbs.append(lb)
            column += 26
            width += 5

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
            lb = LabelButtons(name, direction, row, column, 14, color, self)
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
        text = manager.events.df.tail(12).to_csv(sep="\t", index=False, header=False)
        self.events_text = self.create_and_add_label(text, 0, 0, 210, 16, "black")

    def update_gui(self) -> None:
        text = manager.events.df.tail(12).to_csv(sep="\t", index=False, header=False)
        self.events_text.setText(text)
