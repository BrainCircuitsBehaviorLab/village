from __future__ import annotations

import traceback
from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMessageBox, QPushButton, QScrollArea, QWidget

from village.calibration.water_calibration import WaterCalibration
from village.classes.enums import State
from village.gui.layout import Label, Layout, LineEdit
from village.manager import manager
from village.plots.water_calibration_plot import water_calibration_plot
from village.scripts import utils
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.scripts.utils import create_pixmap
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class WaterCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.water_calibration_button.setDisabled(True)
        self.df = pd.DataFrame()
        self.date = ""
        self.calibration_number = -1
        self.delete_rows: list[int] = []
        self.calibration_points: list[dict] = []
        self.allow_test = False
        self.calibration_denied = False
        self.test_denied = False
        self.calibration_initiated = False
        self.test_initiated = False
        self.update_plot = False
        self.time_line_edits: list[LineEdit] = []
        self.total_weight_line_edits: list[LineEdit] = []
        self.water_delivered_labels: list[Label] = []

        self.water_expected_line_edits2: list[LineEdit] = []
        self.total_weight_line_edits2: list[LineEdit] = []
        self.water_delivered_labels2: list[Label] = []
        self.error_labels2: list[Label] = []

        self.ok_buttons2: list[QPushButton] = []
        self.add_buttons2: list[QPushButton] = []

        self.indices: list[int] = []
        self.times = [0.0 for _ in range(8)]
        self.water_delivered = [0.0 for _ in range(8)]
        self.indices2: list[int] = []
        self.indices2_cleared: list[int] = []
        self.water_expected2 = [0.0 for _ in range(8)]
        self.times2 = [0.0 for _ in range(8)]
        self.errors2 = [0.0 for _ in range(8)]
        self.water_delivered2 = [0.0 for _ in range(8)]

        self.test_point: tuple[float, float] | None = None
        self.test_index: int = 0
        self.test_row_dicts: list[dict] = []

        # ports
        for i in range(8):
            self.create_and_add_label(
                "port" + str(i + 1), 10 + 2 * i, 2, 8, 2, "black", bold=False
            )

        for i in range(8):
            self.create_and_add_label(
                "port" + str(i + 1), 33 + 2 * i, 2, 8, 2, "black", bold=False
            )

        # input
        self.calibration_input_label = self.create_and_add_label(
            "CALIBRATION INPUT",
            6,
            5,
            20,
            2,
            "black",
            description=(
                "Enter a valve opening time and a number of iterations "
                + "to calibrate the ports."
            ),
        )

        self.calibration_input_label = self.create_and_add_label(
            "TEST INPUT",
            29,
            5,
            20,
            2,
            "black",
            description=(
                "Enter the expected water you want to get and a number of iterations "
                + "to test the port calibration."
            ),
        )

        # first input variable
        self.time_label = self.create_and_add_label(
            "TIME(s)",
            8,
            8,
            12,
            2,
            "black",
            bold=False,
            description="Valve opening time in seconds.",
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 10 + 2 * i, 7, 8, 2, self.calibration_changed
            )
            self.time_line_edits.append(line_edit)

        self.water_label2 = self.create_and_add_label(
            "WATER EXPECTED(ul)",
            31,
            5,
            20,
            2,
            "black",
            bold=False,
            description="The expected water in microliters.",
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 33 + 2 * i, 7, 8, 2, self.test_changed
            )
            self.water_expected_line_edits2.append(line_edit)

        # iterations
        self.iterations_label = self.create_and_add_label(
            "ITERATIONS",
            13,
            19,
            12,
            2,
            "black",
            bold=False,
            description="Number of iterations.",
        )
        self.iterations_line_edit = self.create_and_add_line_edit(
            "100", 15, 19, 8, 2, self.calibration_changed
        )

        self.iterations_label2 = self.create_and_add_label(
            "ITERATIONS",
            36,
            19,
            12,
            2,
            "black",
            bold=False,
            description="Number of iterations.",
        )
        self.iterations_line_edit2 = self.create_and_add_line_edit(
            "100", 38, 19, 8, 2, self.test_changed
        )

        # first button
        self.calibrate_button = self.create_and_add_button(
            "CALIBRATE ->",
            17,
            17,
            12,
            2,
            self.calibrate_button_clicked,
            "Calibrate the ports with the values set in the input fields",
            "powderblue",
        )
        self.calibrate_button.setDisabled(True)

        self.test_button = self.create_and_add_button(
            "TEST ->",
            40,
            17,
            12,
            2,
            self.test_button_clicked,
            "Test the calibration of the ports",
            "powderblue",
        )
        self.test_button.setDisabled(True)

        # output
        self.calibration_output_label = self.create_and_add_label(
            "CALIBRATION OUTPUT",
            6,
            28,
            20,
            2,
            "black",
            description=(
                "Enter the total weight in grams to obtain "
                + "the water delivered in microliters for each iteration."
            ),
        )

        self.calibration_output_label = self.create_and_add_label(
            "TEST OUTPUT",
            29,
            28,
            20,
            2,
            "black",
            description=(
                "Enter the total weight in grams to obtain "
                + "the water delivered in microliters for each iteration."
            ),
        )

        # output total weight
        self.total_weight_label = self.create_and_add_label(
            "TOTAL WEIGHT(g)",
            8,
            29,
            17,
            2,
            "black",
            bold=False,
            description="Total weight in grams.",
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 10 + 2 * i, 31, 8, 2, self.calibration_weighted
            )
            line_edit.setDisabled(True)
            self.total_weight_line_edits.append(line_edit)

        self.total_weight_label2 = self.create_and_add_label(
            "TOTAL WEIGHT(g)",
            31,
            29,
            17,
            2,
            "black",
            bold=False,
            description="Total weight in grams.",
        )
        for i in range(8):
            line_edit = self.create_and_add_line_edit(
                "0", 33 + 2 * i, 31, 8, 2, partial(self.test_weighted, i)
            )
            line_edit.setDisabled(True)
            self.total_weight_line_edits2.append(line_edit)

        # output water delivered
        self.water_delivered_label = self.create_and_add_label(
            "WATER DELIVERED(ul)",
            8,
            46,
            20,
            2,
            "black",
            bold=False,
            description="Water delivered in microliters for each of the iterations.",
        )
        for i in range(8):
            label = self.create_and_add_label(
                "0", 10 + 2 * i, 45, 18, 2, "black", bold=False
            )
            label.setAlignment(Qt.AlignCenter)
            self.water_delivered_labels.append(label)

        self.water_delivered_label2 = self.create_and_add_label(
            "WATER DELIVERED(ul)",
            31,
            46,
            20,
            2,
            "black",
            bold=False,
            description="Water delivered in microliters for each of the iterations.",
        )
        for i in range(8):
            label = self.create_and_add_label(
                "0", 33 + 2 * i, 45, 18, 2, "black", bold=False
            )
            label.setAlignment(Qt.AlignCenter)
            self.water_delivered_labels2.append(label)

        # button or third output variable
        self.add_button = self.create_and_add_button(
            "ADD ->",
            17,
            66,
            15,
            2,
            self.add_button_clicked,
            "Add this point to the list of calibration points",
            "powderblue",
        )
        self.add_button.setDisabled(True)

        # ok and add buttons
        for i in range(8):
            text = (
                "The value of this test is correct. "
                + "The error is within the acceptable limit. "
                + "Save the test result in water_calibration.csv."
            )
            button = self.create_and_add_button(
                "OK",
                33 + 2 * i,
                66,
                7,
                2,
                partial(self.ok_button2_clicked, i),
                text,
                "powderblue",
            )
            button.setDisabled(True)
            self.ok_buttons2.append(button)

        for i in range(8):
            text = (
                "The value of this test is not correct. "
                + "The error too large. "
                + "Use the test result as a new calibration point."
            )
            button = self.create_and_add_button(
                "FAIL ->",
                33 + 2 * i,
                73,
                8,
                2,
                partial(self.add_button2_clicked, i),
                text,
                "lightcoral",
            )
            button.setDisabled(True)
            self.add_buttons2.append(button)

        # extra buttons
        save_text = "Save the calibration. At least two points are "
        save_text += "needed to build the calibration curve for each port."
        self.save_button = self.create_and_add_button(
            "SAVE CALIBRATION",
            45,
            177,
            20,
            2,
            self.save_button_clicked,
            save_text,
            "powderblue",
        )
        self.save_button.setDisabled(True)

        self.delete_button = self.create_and_add_button(
            "DELETE CALIBRATION",
            48,
            177,
            20,
            2,
            self.delete_button_clicked,
            "Delete the calibration",
            "lightcoral",
        )

        # info layout
        widget = QWidget()
        widget.setStyleSheet("background-color: #E0E0E0;")
        self.info_layout = InfoLayout(self.window, 40, 32, self)
        widget.setLayout(self.info_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.addWidget(self.scroll_area, 5, 85, 46, 36)

        # plot layout
        self.plot_layout = CalibrationPlotLayout(self.window, 38, 79, self)
        self.addLayout(self.plot_layout, 5, 121, 38, 79)

    def change_layout(self, auto: bool = False) -> bool:
        if auto:
            return False
        elif manager.state in [State.RUN_MANUAL, State.SAVE_MANUAL]:
            QMessageBox.information(
                self.window, "WARNING", "Wait until the task finishes."
            )
            return False
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
                manager.changing_settings = False
                return True
            elif reply == QMessageBox.Discard:
                self.save_button.setDisabled(True)
                manager.changing_settings = False
                return True
            else:
                return False
        else:
            manager.changing_settings = False
            return True

    def calibration_changed(self, value: str = "", key: str = "") -> None:
        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.times = [0.0 for _ in range(8)]
        self.iterations = 0
        try:
            iterations = int(self.iterations_line_edit.text())
            if iterations > 0:
                self.iterations = iterations
                self.iterations_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.iterations_line_edit.setStyleSheet("")
        except Exception:
            self.iterations_line_edit.setStyleSheet("")

        for i in range(8):
            try:
                time = float(self.time_line_edits[i].text())
                if time > 0:
                    self.times[i] = time
                    self.time_line_edits[i].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.time_line_edits[i].setStyleSheet("")
            except Exception:
                self.time_line_edits[i].setStyleSheet("")

            if self.times[i] > 0 and self.iterations > 0:
                self.calibrate_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setDisabled(True)
        self.calibrate_button.setDisabled(True)
        self.water_expected2 = [0.0 for _ in range(8)]
        self.iterations2 = 0

        try:
            iterations2 = int(self.iterations_line_edit2.text())
            if iterations2 > 0:
                self.iterations2 = iterations2
                self.iterations_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.iterations_line_edit2.setStyleSheet("")
        except Exception:
            self.iterations_line_edit2.setStyleSheet("")

        for i in range(8):
            try:
                water = float(self.water_expected_line_edits2[i].text())
                if water > 0:
                    self.water_expected2[i] = water
                    self.water_expected_line_edits2[i].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.water_expected_line_edits2[i].setStyleSheet("")
            except Exception:
                self.water_expected_line_edits2[i].setStyleSheet("")

            if self.water_expected2[i] > 0 and self.iterations2 > 0:
                self.test_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def calibrate_button_clicked(self) -> None:
        if self.calibration_denied:
            QMessageBox.information(
                self.window,
                "Warning",
                "Finish the current test first.",
            )
            return
        self.test_denied = True

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.indices = [i for i, val in enumerate(self.times) if val != 0]
        manager.task = WaterCalibration()
        manager.task.indices = self.indices
        manager.task.times = [self.times[i] for i in self.indices]
        manager.task.maximum_number_of_trials = self.iterations
        manager.task.settings.maximum_duration = 1000
        manager.state = State.RUN_MANUAL
        manager.calibrating = True

        for line_edit in self.time_line_edits:
            line_edit.setDisabled(True)
        self.iterations_line_edit.setDisabled(True)
        for line_edit in self.water_expected_line_edits2:
            line_edit.setDisabled(True)
        self.iterations_line_edit2.setDisabled(True)
        self.calibration_initiated = True
        log.start(task=manager.task.name, subject="None")
        manager.run_task_in_thread()

    def test_button_clicked(self) -> None:
        if self.test_denied:
            QMessageBox.information(
                self.window,
                "Warning",
                "Save or delete the current calibration first.",
            )
            return
        self.calibration_denied = True

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.indices2 = [i for i, val in enumerate(self.water_expected2) if val != 0]
        self.indices2_cleared = []
        errors: list[int] = []
        ok = 0
        for i in range(len(self.water_expected2)):
            if i not in self.indices2:
                self.times2[i] = 0
            else:
                try:
                    self.times2[i] = manager.water_calibration.get_valve_time(
                        i + 1, self.water_expected2[i]
                    )
                    ok += 1
                except Exception:
                    self.water_expected2[i] = 0
                    self.water_expected_line_edits2[i].setText("0")
                    self.water_expected_line_edits2[i].setStyleSheet("")
                    errors.append(i + 1)
                    self.indices2.remove(i)

        if errors:
            text = "The following ports can not be tested: "
            text += ", ".join([str(error) for error in errors])
            text += ". \nYou need to calibrate them first and make sure the value"
            text += " you entered is within the calibrated range."
            QMessageBox.information(
                self.window,
                "Warning",
                text,
            )

        if ok > 0:
            manager.task = WaterCalibration()
            manager.task.indices = self.indices2
            manager.task.times = [self.times2[i] for i in self.indices2]
            manager.task.maximum_number_of_trials = self.iterations2
            manager.task.settings.maximum_duration = 1000
            manager.state = State.RUN_MANUAL
            manager.calibrating = True
            for line_edit in self.time_line_edits:
                line_edit.setDisabled(True)
            self.iterations_line_edit.setDisabled(True)
            for line_edit in self.water_expected_line_edits2:
                line_edit.setDisabled(True)
            self.iterations_line_edit2.setDisabled(True)

            self.calibration_initiated = True
            log.start(task=manager.task.name, subject="None")
            manager.run_task_in_thread()
            self.test_initiated = True
        else:
            self.iterations_line_edit2.setStyleSheet("")

    def save_button_clicked(self) -> None:
        counts = self.df["port_number"].value_counts()
        valid_ports = counts[counts >= 2].index
        removed_ports = counts[counts < 2].index.tolist()
        filtered_df = self.df[self.df["port_number"].isin(valid_ports)]

        manager.water_calibration.df = pd.concat(
            [manager.water_calibration.df, filtered_df], ignore_index=True
        )
        manager.water_calibration.save_from_df()

        if len(removed_ports) > 0:
            text = "The following ports had only one calibration point and were"
            text += "therefore removed from the calibration: "
            text += ", ".join([str(port) for port in removed_ports])
            QMessageBox.information(
                self.window,
                "Warning",
                text,
            )
        else:
            text = "The calibration was saved successfully."
            QMessageBox.information(
                self.window,
                "Success",
                text,
            )
        log.info("Water calibration saved.")
        self.window.create_water_calibration_layout()

    def delete_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Delete calibration",
            "Are you sure you want to delete the calibration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.window.create_water_calibration_layout()

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if manager.state == State.WAIT and self.calibration_initiated:
            self.calibration_initiated = False
            self.calibrate_button.setDisabled(True)
            self.test_button.setDisabled(True)
            for index in range(len(self.total_weight_line_edits)):
                if index in self.indices:
                    self.total_weight_line_edits[index].setEnabled(True)
                    self.total_weight_line_edits[index].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.total_weight_line_edits[index].setStyleSheet("")

        if manager.state == State.WAIT and self.test_initiated:
            self.test_initiated = False
            self.calibrate_button.setDisabled(True)
            self.test_button.setDisabled(True)
            for index in range(len(self.total_weight_line_edits2)):
                if index in self.indices2:
                    self.total_weight_line_edits2[index].setEnabled(True)
                    self.total_weight_line_edits2[index].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.total_weight_line_edits2[index].setStyleSheet("")

        for line_edit in self.water_delivered_labels:
            if line_edit.text() != "0":
                self.add_button.setEnabled(True)

        if self.update_plot:
            if self.delete_rows:
                for row in self.delete_rows:
                    self.df = self.df.drop(index=row)
                    self.df = self.df.reset_index(drop=True)
                self.delete_rows = []
            self.plot_layout.update(self.df, self.test_point)
            self.update_plot = False

        def some_port_has_two_values() -> bool:
            port_counts = []
            for point in self.calibration_points:
                port = point.get("port_number")
                if port in port_counts:
                    return True
                else:
                    port_counts.append(port)
            return False

        if len(self.calibration_points) == 0:
            if self.allow_test and self.water_expected_line_edits2[0].isEnabled():
                self.allow_test = False
                self.test_denied = False
        if some_port_has_two_values():
            self.save_button.setEnabled(True)
        else:
            self.save_button.setDisabled(True)

        if len(self.indices2) == len(self.indices2_cleared) and len(self.indices2) > 0:
            self.all_tests_done()

    def all_tests_done(self) -> None:
        self.indices2 = []
        self.indices2_cleared = []

        for line_edit in self.time_line_edits:
            line_edit.setEnabled(True)

        for line_edit in self.water_expected_line_edits2:
            line_edit.setStyleSheet("")
            line_edit.setEnabled(True)

        self.iterations_line_edit.setEnabled(True)
        self.iterations_line_edit2.setEnabled(True)

        self.test_button.setDisabled(True)
        self.iterations_line_edit2.setStyleSheet("")

        self.calibration_denied = False
        self.info_layout.update()

        self.df = pd.DataFrame(self.test_row_dicts)
        self.calibration_points = self.test_row_dicts
        self.test_row_dicts = []
        self.update_plot = True
        self.info_layout.update()
        manager.changing_settings = False

    def select_port(self, value: str, index: int) -> None:
        pass

    def calibration_weighted(self, value: str = "", key: str = "") -> None:
        self.water_delivered = [0.0 for _ in range(8)]
        for line_edit in self.water_delivered_labels:
            line_edit.setText("0")
        try:
            for index in self.indices:
                line_edit = self.total_weight_line_edits[index]
                result = round((float(line_edit.text()) / self.iterations * 1000), 5)
                if result > 0:
                    self.water_delivered[index] = result

                    self.water_delivered_labels[index].setText(str(result))
        except Exception:
            pass

    def test_weighted(self, i: int) -> None:
        self.water_delivered2 = [0.0 for _ in range(8)]
        for line_edit in self.water_delivered_labels2:
            line_edit.setText("0")

        df = manager.water_calibration.df.copy()
        for index in self.indices2:
            line_edit = self.total_weight_line_edits2[index]
            try:
                result = round((float(line_edit.text()) / self.iterations2 * 1000), 5)
            except Exception:
                result = 0
            if result > 0:
                self.water_delivered2[index] = result
                error = (
                    abs(result - self.water_expected2[index])
                    / self.water_expected2[index]
                    * 100
                )
                error = round(error, 5)
                self.errors2[index] = error
                text = str(result) + " (" + str(error) + "% error)"
                self.water_delivered_labels2[index].setText(text)
                self.ok_buttons2[index].setEnabled(True)
                self.add_buttons2[index].setEnabled(True)

            if index == i:
                df = df[df["port_number"] == index + 1]
                max_calibration = df["calibration_number"].max()
                self.df = df[df["calibration_number"] == max_calibration]
                self.test_point = (self.times2[index], result)
                self.test_index = index
                self.update_plot = True

    def add_button_clicked(self) -> None:
        if self.date == "":
            self.date = time_utils.now_string()
        if self.calibration_number < 0:
            try:
                max_value = manager.water_calibration.df["calibration_number"].max()
                if pd.notna(max_value):
                    self.calibration_number = max_value + 1
                else:
                    self.calibration_number = 1
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
            self.df = pd.concat([self.df, df], ignore_index=True)
            self.calibration_points.append(row_dict)

        for line_edit in self.time_line_edits:
            line_edit.setEnabled(True)
            self.iterations_line_edit.setEnabled(True)

        for line_edit in self.water_expected_line_edits2:
            line_edit.setEnabled(True)
            self.iterations_line_edit2.setEnabled(True)

        for line_edit in self.total_weight_line_edits:
            line_edit.setText("0")
            line_edit.setDisabled(True)
            line_edit.setStyleSheet("")
        self.add_button.setDisabled(True)
        self.plot_layout.update(self.df, self.test_point)
        self.info_layout.update()

    def ok_button2_clicked(self, index: int) -> None:
        self.ok_buttons2[index].setDisabled(True)
        self.add_buttons2[index].setDisabled(True)

        if self.date == "":
            self.date = time_utils.now_string()
        row_dict = {
            "date": self.date,
            "port_number": index + 1,
            "time(s)": self.times2[index],
            "water_delivered(ul)": self.water_delivered2[index],
            "calibration_number": -1,
            "water_expected(ul)": self.water_expected2[index],
            "error(%)": self.errors2[index],
        }

        self.indices2_cleared.append(index)

        df = pd.DataFrame([row_dict])
        manager.water_calibration.df = pd.concat(
            [manager.water_calibration.df, df], ignore_index=True
        )
        manager.water_calibration.save_from_df()

        if self.test_index == index:
            self.df = pd.DataFrame()
            self.test_point = None
            self.test_index = 0

        self.water_expected_line_edits2[index].blockSignals(True)
        self.water_expected_line_edits2[index].setText("0")
        self.water_expected_line_edits2[index].blockSignals(False)
        self.water_delivered_labels2[index].setText("0")
        self.total_weight_line_edits2[index].blockSignals(True)
        self.total_weight_line_edits2[index].setText("0")
        self.total_weight_line_edits2[index].blockSignals(False)
        self.total_weight_line_edits2[index].setDisabled(True)
        self.total_weight_line_edits2[index].setStyleSheet("")

    def add_button2_clicked(self, index: int) -> None:
        self.ok_button2_clicked(index)
        self.test_denied = True

        if self.calibration_number < 0:
            try:
                max_value = manager.water_calibration.df["calibration_number"].max()
                if pd.notna(max_value):
                    self.calibration_number = max_value + 1
                else:
                    self.calibration_number = 1
            except Exception:
                self.calibration_number = 1

        row_dict = {
            "date": self.date,
            "port_number": index + 1,
            "time(s)": self.times2[index],
            "water_delivered(ul)": self.water_delivered2[index],
            "calibration_number": self.calibration_number,
            "water_expected(ul)": np.nan,
            "error(%)": np.nan,
        }

        self.test_row_dicts.append(row_dict)

    def stop_button_clicked(self) -> None:
        if manager.state.can_stop_task():
            log.info("Task manually stopped.", subject=manager.subject.name)
            manager.state = State.SAVE_MANUAL
        elif manager.state.can_go_to_wait():
            manager.state = State.WAIT
        for line_edit in self.time_line_edits:
            line_edit.setEnabled(True)
            line_edit.setStyleSheet("")
            line_edit.setText("0")
        self.times = [0.0 for _ in range(8)]
        self.iterations_line_edit.setEnabled(True)
        self.iterations_line_edit.setStyleSheet("")
        for line_edit in self.water_expected_line_edits2:
            line_edit.setEnabled(True)
            line_edit.setStyleSheet("")
            line_edit.setText("0")
        self.water_expected2 = [0.0 for _ in range(8)]
        self.iterations_line_edit2.setEnabled(True)
        self.iterations_line_edit2.setStyleSheet("")
        self.update_gui()


class CalibrationPlotLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent_layout: WaterCalibrationLayout,
    ) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.parent_layout = parent_layout
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

    def update(self, df: pd.DataFrame, test_point: tuple[float, float] | None) -> None:
        if df.empty:
            self.plot_label.setText("")
            return

        pixmap = QPixmap()
        try:
            figure = water_calibration_plot(
                df.copy(),
                self.plot_width,
                self.plot_height,
                test_point,
            )
            pixmap = create_pixmap(figure)
        except Exception:
            log.error(
                "Can not create water calibration plot",
                exception=traceback.format_exc(),
            )

        if not pixmap.isNull():
            self.plot_label.setPixmap(pixmap)
        else:
            self.plot_label.setText("")


class InfoLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent_layout: WaterCalibrationLayout,
    ) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.parent_layout = parent_layout
        self.update()

    def update(self) -> None:
        self.title = self.create_and_add_label(
            "CALIBRATION POINTS", 0, 1, 40, 2, "black", bold=False
        )
        self.port_label = self.create_and_add_label(
            "Port", 2, 1, 8, 2, "black", bold=False
        )
        self.time_label = self.create_and_add_label(
            "Time(s)", 2, 6, 8, 2, "black", bold=False
        )
        self.water_label = self.create_and_add_label(
            "Water delivered(ul)", 2, 14, 24, 2, "black", bold=False
        )

        for i, point in enumerate(self.parent_layout.calibration_points):
            text = str(point["port_number"])
            self.create_and_add_label(text, 4 + 2 * i, 1, 8, 2, "black", bold=False)
            text = str(point["time(s)"])
            self.create_and_add_label(text, 4 + 2 * i, 8, 8, 2, "black", bold=False)
            text = str(point["water_delivered(ul)"])
            self.create_and_add_label(text, 4 + 2 * i, 16, 14, 2, "black", bold=False)
            self.create_and_add_button(
                "-",
                4 + 2 * i,
                28,
                5,
                2,
                partial(self.delete_point, i),
                "Delete the calibration point",
                "lightcoral",
            )

    def delete_point(self, i: int) -> None:
        utils.delete_all_elements_from_layout(self)
        self.parent_layout.calibration_points.pop(i)
        if len(self.parent_layout.calibration_points) == 0:
            self.parent_layout.allow_test = True
        self.parent_layout.delete_rows.append(i)
        self.parent_layout.update_plot = True
        self.update()
