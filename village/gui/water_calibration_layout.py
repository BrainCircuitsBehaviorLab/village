from __future__ import annotations  # noqa: I001
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QMessageBox
from village.classes.enums import State
from village.gui.layout import Layout, Label, LineEdit
from village.manager import manager
from village.settings import settings
from village.calibration.water_calibration import WaterCalibration
import traceback
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QTextEdit
from PyQt5.QtCore import Qt
from village.log import log
from village.plots.water_calibration_plot import water_calibration_plot
from village.plots.create_pixmap import create_pixmap
from village.scripts import time_utils

import pandas as pd
import numpy as np

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class WaterCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.df = pd.DataFrame()
        self.date = ""
        self.calibration_number = 0
        self.regression_text = ""
        self.calibration_initiated = False
        self.time_line_edits: list[LineEdit] = []
        self.total_weight_line_edits: list[LineEdit] = []
        self.water_delivered_labels: list[Label] = []

        self.water_line_edits2: list[LineEdit] = []
        self.total_weight_line_edits2: list[LineEdit] = []
        self.water_delivered_labels2: list[Label] = []
        self.error_labels2: list[Label] = []

        self.indices: list[int] = []
        self.times = [0.0 for _ in range(8)]
        self.water_delivered = [0.0 for _ in range(8)]
        self.water2 = [0.0 for _ in range(8)]

        self.calibration_input_label = self.create_and_add_label(
            "CALIBRATION INPUT",
            4,
            10,
            20,
            2,
            "black",
        )

        self.calibration_output_label = self.create_and_add_label(
            "CALIBRATION OUTPUT",
            4,
            65,
            20,
            2,
            "black",
        )

        self.calibration_input_label = self.create_and_add_label(
            "TEST INPUT",
            28,
            10,
            20,
            2,
            "black",
        )

        self.calibration_output_label = self.create_and_add_label(
            "TEST OUTPUT",
            28,
            65,
            20,
            2,
            "black",
        )

        for i in range(8):
            self.create_and_add_label(
                "port" + str(i + 1), 8 + 2 * i, 2, 8, 2, "black", bold=False
            )

        self.time_label = self.create_and_add_label(
            "TIME (s)", 6, 10, 15, 2, "black", bold=False
        )

        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 8 + 2 * i, 10, 13, 2, self.calibration_changed
            )
            self.time_line_edits.append(line_edit)

        self.iterations_label = self.create_and_add_label(
            "ITERATIONS", 12, 25, 15, 2, "black", bold=False
        )

        self.iterations_line_edit = self.create_and_add_line_edit(
            "100", 14, 25, 13, 2, self.calibration_changed
        )

        self.total_weight_label = self.create_and_add_label(
            "TOTAL WEIGHT (g)", 6, 65, 20, 2, "black", bold=False
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 8 + 2 * i, 65, 13, 2, self.calibration_weighted
            )
            line_edit.setDisabled(True)
            self.total_weight_line_edits.append(line_edit)

        self.water_delivered_label = self.create_and_add_label(
            "WATER DELIVERED (ul)", 6, 85, 20, 2, "black", bold=False
        )
        for i in range(8):
            label = self.create_and_add_label(
                "0", 8 + 2 * i, 90, 13, 2, "black", bold=False
            )
            self.water_delivered_labels.append(label)

        for i in range(8):
            self.create_and_add_label(
                "port" + str(i + 1), 32 + 2 * i, 2, 8, 2, "black", bold=False
            )

        self.water_label2 = self.create_and_add_label(
            "WATER (ul)", 30, 10, 15, 2, "black", bold=False
        )

        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 32 + 2 * i, 10, 13, 2, self.test_changed
            )
            self.water_line_edits2.append(line_edit)

        self.iterations_label2 = self.create_and_add_label(
            "ITERATIONS", 36, 25, 15, 2, "black", bold=False
        )
        self.iterations_line_edit2 = self.create_and_add_line_edit(
            "100", 38, 25, 13, 2, self.test_changed
        )

        self.total_weight_label2 = self.create_and_add_label(
            "TOTAL WEIGHT (g)", 30, 65, 20, 2, "black", bold=False
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 32 + 2 * i, 65, 13, 2, self.test_weighted
            )
            line_edit.setDisabled(True)
            self.total_weight_line_edits2.append(line_edit)

        self.water_delivered_label2 = self.create_and_add_label(
            "WATER DELIVERED (ul)", 30, 85, 20, 2, "black", bold=False
        )
        for i in range(8):
            label = self.create_and_add_label(
                "0", 32 + 2 * i, 90, 13, 2, "black", bold=False
            )
            self.water_delivered_labels2.append(label)

        self.error_label2 = self.create_and_add_label(
            "ERROR (%)", 30, 108, 15, 2, "black", bold=False
        )
        for i in range(8):
            label = self.create_and_add_label(
                "0", 32 + 2 * i, 113, 13, 2, "black", bold=False
            )
            self.error_labels2.append(label)

        self.calibrate_button = self.create_and_add_button(
            "CALIBRATE -->",
            14,
            41,
            20,
            2,
            self.calibrate_button_clicked,
            "Calibrate the ports with the values set in the input fields",
            "powderblue",
        )
        self.calibrate_button.setDisabled(True)

        self.add_button = self.create_and_add_button(
            "ADD -->",
            14,
            105,
            20,
            2,
            self.add_button_clicked,
            "Add the values of the calibration points",
            "powderblue",
        )
        self.add_button.setDisabled(True)

        self.test_button = self.create_and_add_button(
            "TEST -->",
            38,
            41,
            20,
            2,
            self.test_button_clicked,
            "Test the calibration of the ports",
            "powderblue",
        )
        self.test_button.setDisabled(True)

        self.save_button = self.create_and_add_button(
            "SAVE CALIBRATION",
            44,
            186,
            26,
            2,
            self.delete_button_clicked,
            "Save the calibration",
            "powderblue",
        )
        self.save_button.clicked.connect(self.save_button_clicked)

        self.delete_button = self.create_and_add_button(
            "DELETE THE CALIBRATION",
            48,
            186,
            26,
            2,
            self.delete_button_clicked,
            "Delete the calibration",
            "lightcoral",
        )
        self.delete_button.clicked.connect(self.delete_button_clicked)

        self.plot_layout = CalibrationPlotLayout(self.window, 24, 82)
        self.addLayout(self.plot_layout, 4, 130, 24, 82)

        self.title = self.create_and_add_label(
            "port_number;time(s);water_delivered(ul)",
            28,
            130,
            42,
            2,
            "black",
            bold=False,
        )

        self.info_layout = InfoLayout(self.window, 20, 40)
        self.addLayout(self.info_layout, 30, 130, 20, 40)

        self.title2 = self.create_and_add_label(
            "port_number;a;b;c", 28, 172, 40, 2, "black", bold=False
        )
        self.regression_label = self.create_and_add_label(
            "", 30, 172, 40, 16, "black", bold=False
        )
        self.regression_label.setAlignment(Qt.AlignTop)

    def change_layout(self, auto: bool = False) -> bool:
        if auto:
            return True
        elif self.save_button.isEnabled():

            reply = QMessageBox.question(
                self.window,
                "Save calibration",
                "Do you want to save the calibration?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.save_button.setDisabled(True)
                self.save_button_clicked()
                return True
            elif reply == QMessageBox.Discard:
                self.save_button.setDisabled(True)
                return True
            else:
                return False
        else:
            return True

    def calibration_changed(self, value: str = "", key: str = "") -> None:
        self.calibrate_button.setEnabled(False)
        self.times = [0.0 for _ in range(8)]
        try:
            self.iterations = abs(int(self.iterations_line_edit.text()))
            if self.iterations > 0:
                self.iterations_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.iterations_line_edit.setStyleSheet("")
        except Exception:
            self.iterations = 0
            self.iterations_line_edit.setStyleSheet("")

        for i in range(8):
            time = self.time_line_edits[i].text()
            try:
                time_float = float(time)
                self.times[i] = time_float
                if time_float > 0:
                    self.time_line_edits[i].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.time_line_edits[i].setStyleSheet("")
            except Exception:
                self.time_line_edits[i].setStyleSheet("")
                time = "0"

            if time != "0" and self.iterations != 0:
                self.calibrate_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setEnabled(False)
        self.water2 = [0.0 for _ in range(8)]

        try:
            self.iterations2 = abs(int(self.iterations_line_edit2.text()))
        except Exception:
            self.iterations2 = 0

        for i in range(8):
            water = self.water_line_edits2[i].text()
            try:
                water_float = abs(float(water))
                self.water2[i] = water_float
            except Exception:
                water = "0"

            if water != "0" and self.iterations2 != 0:
                self.test_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def calibrate_button_clicked(self) -> None:
        self.calibrate_button.setDisabled(True)
        manager.task = WaterCalibration()
        self.indices = [i for i, val in enumerate(self.times) if val != 0]
        manager.task.indices = self.indices
        manager.task.times = [self.times[i] for i in self.indices]
        manager.task.maximum_number_of_trials = self.iterations
        manager.task.settings.maximum_duration = 1000
        manager.state = State.RUN_MANUAL
        self.calibration_initiated = True
        manager.run_task_in_thread()

    def test_button_clicked(self) -> None:
        pass

    def save_button_clicked(self) -> None:
        manager.water_calibration.df = pd.concat(
            [manager.water_calibration.df, self.df]
        )
        manager.water_calibration.save_from_df()

    def delete_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Delete calibration",
            "Are you sure you want to delete the calibration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.window.create_calibration_layout()

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if manager.state == State.WAIT and self.calibration_initiated:
            self.calibration_initiated = False
            self.calibrate_button.setDisabled(True)
            for index in range(len(self.total_weight_line_edits)):
                if index in self.indices:
                    self.total_weight_line_edits[index].setEnabled(True)
                    self.total_weight_line_edits[index].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.total_weight_line_edits[index].setStyleSheet("")

        self.add_button.setDisabled(True)
        for line_edit in self.water_delivered_labels:
            if line_edit.text() != "0":
                self.add_button.setEnabled(True)
        self.regression_label.setText(self.regression_text)

    def select_port(self, value: str, index: int) -> None:
        pass

    def calibration_weighted(self, value: str = "", key: str = "") -> None:
        self.water_delivered = [0.0 for _ in range(8)]
        for line_edit in self.water_delivered_labels:
            line_edit.setText("0")
        try:
            for index in self.indices:
                line_edit = self.total_weight_line_edits[index]
                result = float(line_edit.text()) / self.iterations * 1000
                if result > 0:
                    self.water_delivered[index] = result
                    self.water_delivered_labels[index].setText(str(result))
        except Exception:
            pass

    def test_weighted(self, value: str = "", key: str = "") -> None:
        for index in self.indices:
            self.error_labels2[index].setText("0")

    def add_button_clicked(self) -> None:
        if self.date == "":
            self.date = time_utils.now_string()
        if self.calibration_number == 0:
            try:
                self.calibration_number = (
                    manager.water_calibration.df["calibration_number"].max() + 1
                )
            except Exception:
                self.calibration_number = 1
        for i in self.indices:
            row_dict = {
                "date": self.date,
                "port_number": i + 1,
                "time(s)": self.times[i],
                "water_delivered(ul)": self.water_delivered[i],
                "calibration_number": self.calibration_number,
                "water_expected(ul)": np.nan,
                "error(%)": np.nan,
            }

            df = pd.DataFrame([row_dict])
            self.df = pd.concat([self.df, df])

        for line_edit in self.total_weight_line_edits:
            line_edit.setText("0")
            line_edit.setDisabled(True)
            line_edit.setStyleSheet("")
        self.add_button.setDisabled(True)
        self.calibrate_button.setEnabled(True)
        self.plot()
        self.info_layout.update(self.df)

    def plot(self) -> None:
        self.plot_layout.update(self.df)


class CalibrationPlotLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.draw()

    def draw(self) -> None:
        self.plot_label = QLabel()
        self.plot_label.setStyleSheet(
            "QLabel {border: 1px solid gray; background-color: white;}"
        )
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.addWidget(self.plot_label, 0, 0, self.rows, self.columns)

        self.pixmap = QPixmap()

        self.plot_width = (self.columns * self.column_width - 10) / dpi
        self.plot_height = (self.rows * self.row_height - 5) / dpi

    def update(self, df: pd.DataFrame) -> None:
        pixmap = QPixmap()
        try:
            figure, text = water_calibration_plot(
                df.copy(),
                self.plot_width,
                self.plot_height,
            )
            pixmap = create_pixmap(figure)
            self.parent().regression_text = text
        except Exception:
            log.error(
                "Can not create corridor plot",
                exception=traceback.format_exc(),
            )

        if not pixmap.isNull():
            self.plot_label.setPixmap(pixmap)
        else:
            self.plot_label.setText("Plot could not be generated")


class InfoLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.draw()

    def draw(self) -> None:
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: white;
                color: black;
                border: 1px solid gray;
                font-size: 12px;
            }
        """
        )
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.addWidget(self.text_edit, 0, 0, self.rows, self.columns)

        self.text_edit.textChanged.connect(self.handle_text_change)

    def update(self, df: pd.DataFrame) -> None:
        self.text_edit.blockSignals(True)
        columns_to_include = ["port_number", "time(s)", "water_delivered(ul)"]
        text = df[columns_to_include].to_csv(sep=";", index=False, header=False)
        self.text_edit.setText(text)
        self.text_edit.blockSignals(False)

    def handle_text_change(self) -> None:
        pass
