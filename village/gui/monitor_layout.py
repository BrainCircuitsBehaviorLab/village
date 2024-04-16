from picamera2.previews.qt import QGlPicamera2
from PyQt5.QtWidgets import QPushButton, QWidget

from village.camera import cam_box, cam_corridor
from village.gui.layout import Layout


class MonitorLayout(Layout):
    def __init__(self, window):
        super().__init__(window)
        self.draw()

    def draw(self):
        self.cam_row = 3
        self.cam_corridor_column = 0
        self.cam_box_column = 100
        self.cam_rows = 30
        self.cam_columns = 90
        self.widget_width = 16
        self.first_column = 0

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
            self.qpicamera2_box = QGlPicamera2(cam_box.cam, width=400, height=300)
        else:
            self.qpicamera2_box = QWidget()

        self.button1 = QPushButton("Preview")
        self.button1.setCheckable(True)
        self.button1.setFixedSize(
            self.widget_width * self.column_width, self.widget_height * self.row_height
        )

        self.button2 = QPushButton("Stop Preview")
        self.button2.setCheckable(True)
        self.button2.setFixedSize(
            self.widget_width * self.column_width, self.widget_height * self.row_height
        )

        self.button3 = QPushButton("Record")
        self.button3.setCheckable(True)
        self.button3.setFixedSize(
            self.widget_width * self.column_width, self.widget_height * self.row_height
        )

        self.button4 = QPushButton("Stop Record")
        self.button4.setCheckable(True)
        self.button4.setFixedSize(
            self.widget_width * self.column_width, self.widget_height * self.row_height
        )

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

        row += self.cam_rows + self.widget_height
        self.addWidget(
            self.button1, row, self.first_column, self.widget_width, self.widget_height
        )
        row += 2 * self.widget_height
        self.addWidget(
            self.button2, row, self.first_column, self.widget_width, self.widget_height
        )
        row += 2 * self.widget_height
        self.addWidget(
            self.button3, row, self.first_column, self.widget_width, self.widget_height
        )
        row += 2 * self.widget_height
        self.addWidget(
            self.button4, row, self.first_column, self.widget_width, self.widget_height
        )
        row += 2 * self.widget_height

    def change_layout(self):
        if isinstance(self.qpicamera2_corridor, QGlPicamera2):
            self.qpicamera2_corridor.cleanup()
            cam_corridor.reset_preview()
        if isinstance(self.qpicamera2_box, QGlPicamera2):
            self.qpicamera2_box.cleanup()
            cam_box.reset_preview()
        return True
