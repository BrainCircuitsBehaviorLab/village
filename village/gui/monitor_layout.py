from picamera2.previews.qt import QGlPicamera2  # type: ignore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QPushButton, QWidget

from village.app_state import app
from village.camera import cam_box, cam_corridor
from village.gui.layout import Layout
from village.motor import motor
from village.settings import settings


class LabelButtons:
    def __init__(self, name, direction, row, column, color, monitor_layout: Layout):
        self.name = name
        self.direction = direction
        self.short_name = name.split("_")[0]
        self.mapping_dict_index = {
            "left": 0,
            "top": 1,
            "right": 2,
            "bottom": 3,
            "threshold": 4,
        }
        self.mapping_dict_max = {
            "left": 640,
            "top": 480,
            "right": 640,
            "bottom": 480,
            "threshold": 255,
        }
        self.mapping_dict_increase = {
            "left": "\u2192",
            "top": "\u2193",
            "right": "\u2192",
            "bottom": "\u2193",
            "threshold": "\u2191",
        }
        self.mapping_dict_decrease = {
            "left": "\u2190",
            "top": "\u2191",
            "right": "\u2190",
            "bottom": "\u2191",
            "threshold": "\u2193",
        }

        self.index = self.mapping_dict_index[direction]
        self.max = self.mapping_dict_max[direction]
        self.label_value = settings.get(name)[self.index]
        self.label_width = 8
        self.number_width = 5
        self.arrow_width = 2
        self.widget_height = monitor_layout.widget_height
        self.row_height = monitor_layout.row_height
        self.column_width = monitor_layout.column_width

        self.label2 = QLabel(direction)
        self.label2.setStyleSheet(color)
        self.label2.setAlignment(Qt.AlignTop)
        self.label2.setFixedWidth(self.label_width * self.column_width)
        self.label3 = QLabel(str(self.label_value))
        self.label3.setStyleSheet(color)
        self.label3.setAlignment(Qt.AlignTop)
        self.label3.setAlignment(Qt.AlignRight)
        self.label3.setFixedWidth(self.number_width * self.column_width)

        # Botones para incrementar y decrementar
        self.btn_increase = QPushButton(self.mapping_dict_increase[direction])
        self.btn_increase.setStyleSheet(color)
        self.btn_increase.setFixedWidth(self.arrow_width * self.column_width)
        self.btn_decrease = QPushButton(self.mapping_dict_decrease[direction])
        self.btn_decrease.setStyleSheet(color)
        self.btn_decrease.setFixedWidth(self.arrow_width * self.column_width)

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
        self.btn_increase.pressed.connect(self.start_increasing)
        self.btn_increase.released.connect(self.stop_timer)
        self.btn_decrease.pressed.connect(self.start_decreasing)
        self.btn_decrease.released.connect(self.stop_timer)

        monitor_layout.addWidget(
            self.label2, row, column, self.label_width, self.widget_height
        )
        column += self.label_width
        monitor_layout.addWidget(
            self.label3, row, column, self.number_width, self.widget_height
        )
        if direction == "threshold":
            column += self.number_width + 1
            monitor_layout.addWidget(
                self.btn_increase,
                row,
                column,
                self.arrow_width,
                self.widget_height,
            )
            column += self.arrow_width
            monitor_layout.addWidget(
                self.btn_decrease,
                row,
                column,
                self.arrow_width,
                self.widget_height,
            )
        else:
            column += self.number_width + 1
            monitor_layout.addWidget(
                self.btn_decrease,
                row,
                column,
                self.arrow_width,
                self.widget_height,
            )
            column += self.arrow_width
            monitor_layout.addWidget(
                self.btn_increase,
                row,
                column,
                self.arrow_width,
                self.widget_height,
            )

    def increase_value(self):
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

    def decrease_value(self):
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

    def start_increasing(self):
        self.increase_value()
        self.timer_increase1.start()

    def start_decreasing(self):
        self.decrease_value()
        self.timer_decrease1.start()

    def stop_timer(self):
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
    def __init__(self, window):
        super().__init__(window)
        self.draw()

    def draw(self):
        self.cam_row = 5
        self.cam_corridor_column = 0
        self.cam_box_column = 122
        self.cam_rows = 31
        self.cam_columns = 90
        self.widget_width = 16
        self.first_column = 0
        self.second_column = 25
        self.third_column = 50
        self.fourth_column = 75
        self.fifth_column = 120
        self.sixth_column = 145
        self.seventh_column = 170
        self.eight_column = 195
        self.button1_row = 5
        self.button1_column = 91
        self.button2_row = 7
        self.button2_column = 101

        self.title_width = 16

        self.monitor_button.setDisabled(True)
        self.monitor_button.setStyleSheet("QPushButton {background-color: lightblue}")

        cam_corridor.stop_preview()
        if cam_corridor.cam is not None:
            self.qpicamera2_corridor = QGlPicamera2(
                cam_corridor.cam, width=400, height=300
            )
        else:
            self.qpicamera2_corridor = QWidget()

        cam_box.stop_preview()
        if cam_box.cam is not None:
            self.qpicamera2_box = QGlPicamera2(cam_box.cam)
        else:
            self.qpicamera2_box = QWidget()

        row = self.cam_row
        self.addWidget(
            self.qpicamera2_box,
            row,
            self.cam_box_column,
            self.cam_rows,
            self.cam_columns,
        )
        self.addWidget(
            self.qpicamera2_corridor,
            row,
            self.cam_corridor_column,
            self.cam_rows,
            self.cam_columns,
        )

        self.lbs = []
        row = self.cam_row + self.cam_rows + self.widget_height

        color = app.color_area1_label
        column = self.first_column
        name = "AREA1_CORRIDOR"
        self.draw_area_buttons(name, row, column, color)
        column = self.fifth_column
        name = "AREA1_BOX"
        self.draw_area_buttons(name, row, column, color)

        color = app.color_area2_label
        column = self.second_column
        name = "AREA2_CORRIDOR"
        self.draw_area_buttons(name, row, column, color)
        column = self.sixth_column
        name = "AREA2_BOX"
        self.draw_area_buttons(name, row, column, color)

        color = app.color_area3_label
        column = self.third_column
        name = "AREA3_CORRIDOR"
        self.draw_area_buttons(name, row, column, color)
        column = self.seventh_column
        name = "AREA3_BOX"
        self.draw_area_buttons(name, row, column, color)
        self.draw_area_buttons(name, row, column, color)

        color = app.color_area4_label
        column = self.eight_column
        name = "AREA4_BOX"
        self.draw_area_buttons(name, row, column, color)

        self.open_door1 = QPushButton("OPEN DOOR 1")
        self.open_door1.setStyleSheet(
            "QPushButton {background-color: lightcoral; font-size: 10px}"
        )
        self.open_door1.clicked.connect(motor.open_door1)
        self.addWidget(
            self.open_door1,
            self.button1_row,
            self.button1_column,
            self.widget_height,
            self.button_width,
        )

        self.close_door1 = QPushButton("CLOSE DOOR 1")
        self.close_door1.setStyleSheet(
            "QPushButton {background-color: lightcoral; font-size: 10px}"
        )
        self.close_door1.clicked.connect(motor.close_door1)
        self.addWidget(
            self.close_door1,
            self.button1_row,
            self.button2_column,
            self.widget_height,
            self.button_width,
        )

        self.open_door2 = QPushButton("OPEN DOOR 2")
        self.open_door2.setStyleSheet(
            "QPushButton {background-color: lightcoral; font-size: 10px}"
        )
        self.open_door2.clicked.connect(motor.open_door2)
        self.addWidget(
            self.open_door2,
            self.button2_row,
            self.button1_column,
            self.widget_height,
            self.button_width,
        )

        self.close_door2 = QPushButton("CLOSE DOOR 2")
        self.close_door2.setStyleSheet(
            "QPushButton {background-color: lightcoral; font-size: 10px}"
        )
        self.close_door2.clicked.connect(motor.close_door2)
        self.addWidget(
            self.close_door2,
            self.button2_row,
            self.button2_column,
            self.widget_height,
            self.button_width,
        )

    def draw_area_buttons(self, name, row, column, color):
        self.label1 = QLabel(name)
        self.label1.setStyleSheet(color)
        self.label1.setAlignment(Qt.AlignTop)
        self.label1.setFixedWidth(self.title_width * self.column_width)
        self.addWidget(self.label1, row, column, self.label_width, self.widget_height)
        row += self.widget_height
        for direction in ("left", "right", "top", "bottom", "threshold"):
            lb = LabelButtons(name, direction, row, column, color, self)
            self.lbs.append(lb)
            row += self.widget_height

    def change_layout(self):
        if isinstance(self.qpicamera2_corridor, QGlPicamera2):
            self.qpicamera2_corridor.cleanup()
            cam_corridor.reset_preview()
        if isinstance(self.qpicamera2_box, QGlPicamera2):
            self.qpicamera2_box.cleanup()
            cam_box.reset_preview()
        return True
