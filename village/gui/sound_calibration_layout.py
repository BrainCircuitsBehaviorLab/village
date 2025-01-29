from __future__ import annotations

import traceback
from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMessageBox, QPushButton, QScrollArea, QWidget

from village.calibration.sound_calibration import SoundCalibration
from village.classes.enums import State
from village.gui.layout import Label, Layout, LineEdit
from village.log import log
from village.manager import manager
from village.plots.create_pixmap import create_pixmap
from village.plots.sound_calibration_plot import sound_calibration_plot
from village.scripts import time_utils, utils
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class SoundCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.df = pd.DataFrame()
        self.date = ""
        self.calibration_number = 0
        self.delete_row = -1
        self.calibration_points: list[dict] = []
        self.calibration_initiated = False
        self.test_initiated = False
        self.update_plot = False
        self.gain_line_edits: list[LineEdit] = []
        self.dB_obtained_line_edits: list[LineEdit] = []
        self.dB_obtained_labels: list[Label] = []

        self.dB_expected_line_edits2: list[LineEdit] = []
        self.dB_obtained_line_edits2: list[LineEdit] = []
        self.error_labels2: list[Label] = []

        self.ok_buttons2: list[QPushButton] = []
        self.add_buttons2: list[QPushButton] = []

        self.indices: list[int] = []
        self.gains = [0.0 for _ in range(2)]
        self.dB_obtained = [0.0 for _ in range(2)]
        self.indices2: list[int] = []
        self.indices2_cleared: list[int] = []
        self.dB_expected2 = [0.0 for _ in range(2)]
        self.gains2 = [0.0 for _ in range(2)]
        self.errors2 = [0.0 for _ in range(2)]
        self.dB_obtained2 = [0.0 for _ in range(2)]

        # speakers
        self.create_and_add_label("speaker left(0)", 11, 1, 8, 2, "black", bold=False)
        self.create_and_add_label("speaker right(1)", 13, 1, 8, 2, "black", bold=False)

        self.create_and_add_label("speaker left(0)", 34, 1, 8, 2, "black", bold=False)
        self.create_and_add_label("speaker right(1)", 36, 1, 8, 2, "black", bold=False)

        # input
        self.calibration_input_label = self.create_and_add_label(
            "CALIBRATION INPUT",
            5,
            5,
            20,
            2,
            "black",
        )

        self.calibration_input_label = self.create_and_add_label(
            "TEST INPUT",
            30,
            5,
            20,
            2,
            "black",
        )

        # first input variable
        self.gain_label = self.create_and_add_label(
            "GAIN", 7, 7, 12, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 9 + 2 * i, 7, 8, 2, self.calibration_changed
            )
            self.gain_line_edits.append(line_edit)

        self.dB_expected_label2 = self.create_and_add_label(
            "dB EXPECTED", 32, 5, 20, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 34 + 2 * i, 7, 8, 2, self.test_changed
            )
            self.dB_expected_line_edits2.append(line_edit)

        # second input variable
        self.freq_label = self.create_and_add_label(
            "FREQ", 7, 18, 12, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 9 + 2 * i, 18, 8, 2, self.calibration_changed
            )
            self.freq_line_edits.append(line_edit)

        self.freq_label2 = self.create_and_add_label(
            "FREQ", 32, 18, 20, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 34 + 2 * i, 18, 8, 2, self.test_changed
            )
            self.freq_line_edits2.append(line_edit)

        # duration
        self.duration_label = self.create_and_add_label(
            "DURATION(s)", 7, 28, 12, 2, "black", bold=False
        )
        self.duration_line_edit = self.create_and_add_line_edit(
            "1", 9, 19, 28, 2, self.calibration_changed
        )

        self.duration_label2 = self.create_and_add_label(
            "DURATION(s)", 32, 28, 12, 2, "black", bold=False
        )
        self.duration_line_edit2 = self.create_and_add_line_edit(
            "1", 34, 28, 8, 2, self.test_changed
        )

        # first button
        self.calibrate_button = self.create_and_add_button(
            "CALIBRATE ->",
            11,
            28,
            12,
            2,
            self.calibrate_button_clicked,
            "Calibrate the speakers with the values set in the input fields",
            "powderblue",
        )
        self.calibrate_button.setDisabled(True)

        self.test_button = self.create_and_add_button(
            "TEST ->",
            36,
            28,
            12,
            2,
            self.test_button_clicked,
            "Test the calibration of the speakers",
            "powderblue",
        )
        self.test_button.setDisabled(True)

        # output
        self.calibration_output_label = self.create_and_add_label(
            "CALIBRATION OUTPUT",
            5,
            45,
            20,
            2,
            "black",
        )

        self.calibration_output_label = self.create_and_add_label(
            "TEST OUTPUT",
            30,
            45,
            20,
            2,
            "black",
        )

        # output dB obtained
        self.dB_obtained_label = self.create_and_add_label(
            "dB OBTAINED", 7, 45, 17, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 9 + 2 * i, 45, 8, 2, self.calibration_measured
            )
            line_edit.setDisabled(True)
            self.dB_obtained_line_edits.append(line_edit)

        self.dB_obtained_label2 = self.create_and_add_label(
            "dB OBTAINED", 32, 45, 17, 2, "black", bold=False
        )
        for i in range(2):
            line_edit = self.create_and_add_line_edit(
                "0", 34 + 2 * i, 45, 8, 2, self.test_measured
            )
            line_edit.setDisabled(True)
            self.dB_obtained_line_edits2.append(line_edit)

        # error
        for i in range(2):
            label = self.create_and_add_label(
                "", 34 + 2 * i, 45, 18, 2, "black", bold=False
            )
            label.setAlignment(Qt.AlignCenter)
            self.error_labels2.append(label)

        # buttons
        self.add_button = self.create_and_add_button(
            "ADD ->",
            16,
            66,
            15,
            2,
            self.add_button_clicked,
            "Add the values of the calibration points",
            "powderblue",
        )
        self.add_button.setDisabled(True)

        # ok and add buttons
        for i in range(2):
            button = self.create_and_add_button(
                "OK",
                34 + 2 * i,
                66,
                7,
                2,
                partial(self.ok_button_clicked, i),
                """The value of this test is correct.
                The error is within the acceptable limit.
                Save the test result in sound_calibration.csv.""",
                "powderblue",
            )
            button.setDisabled(True)
            self.ok_buttons2.append(button)

        for i in range(2):
            button = self.create_and_add_button(
                "ADD ->",
                34 + 2 * i,
                73,
                8,
                2,
                partial(self.add_button2_clicked, i),
                """The value of this test is not correct.
                The error too large.
                Use the test result as a new calibration point.""",
                "lightcoral",
            )
            button.setDisabled(True)
            self.add_buttons2.append(button)

        # extra buttons
        self.save_button = self.create_and_add_button(
            "SAVE CALIBRATION",
            44,
            192,
            20,
            2,
            self.save_button_clicked,
            "Save the calibration",
            "powderblue",
        )
        self.save_button.setDisabled(True)

        self.delete_button = self.create_and_add_button(
            "DELETE CALIBRATION",
            48,
            192,
            20,
            2,
            self.delete_button_clicked,
            "Delete the calibration",
            "lightcoral",
        )
        self.delete_button.setDisabled(True)

        # info layout
        widget = QWidget()
        widget.setStyleSheet("background-color: #E0E0E0;")
        self.info_layout = InfoLayout(self.window, 40, 40, self)
        widget.setLayout(self.info_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.addWidget(self.scroll_area, 4, 85, 46, 40)

        # plot layout
        self.plot_layout = CalibrationPlotLayout(self.window, 36, 87, self)
        self.addLayout(self.plot_layout, 4, 125, 38, 87)

    def change_layout(self, auto: bool = False) -> bool:
        if manager.state in [State.RUN_MANUAL, State.SAVE_MANUAL]:
            if not auto:
                QMessageBox().information(
                    self.window, "WARNING", "Wait until the task finishes."
                )
            return False
        elif auto:
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
        self.gains = [0.0 for _ in range(2)]
        try:
            self.duration = abs(int(self.duration_line_edit.text()))
            if self.duration > 0:
                self.duration_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.duration_line_edit.setStyleSheet("")
        except Exception:
            self.duration = 0
            self.duration_line_edit.setStyleSheet("")

        for i in range(2):
            gain = self.gain_line_edits[i].text()
            try:
                gain_float = float(gain)
                self.gains[i] = gain_float
                if gain_float > 0:
                    self.gain_line_edits[i].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.gain_line_edits[i].setStyleSheet("")
            except Exception:
                self.gain_line_edits[i].setStyleSheet("")
                gain = "0"

            if gain != "0" and self.duration != 0:
                self.calibrate_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setEnabled(False)
        self.dB_expected2 = [0.0 for _ in range(2)]

        try:
            self.duration2 = abs(int(self.duration_line_edit2.text()))
            if self.duration2 > 0:
                self.duration_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.duration_line_edit2.setStyleSheet("")
        except Exception:
            self.duration2 = 0
            self.duration_line_edit2.setStyleSheet("")

        for i in range(2):
            dB = self.dB_expected_line_edits2[i].text()
            try:
                dB_float = float(dB)
                self.dB_expected2[i] = dB_float
                if dB_float > 0:
                    self.dB_expected_line_edits2[i].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.dB_expected_line_edits2[i].setStyleSheet("")
            except Exception:
                dB = "0"
                self.dB_expected_line_edits2[i].setStyleSheet("")

            if dB != "0" and self.duration2 != 0:
                self.test_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def calibrate_button_clicked(self) -> None:
        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.indices = [i for i, val in enumerate(self.gains) if val != 0]
        manager.state = State.RUN_MANUAL
        task = SoundCalibration(self.speaker, self.gain, self.freq, self.duration)
        for line_edit in self.gain_line_edits:
            line_edit.setDisabled(True)
        self.duration_line_edit.setDisabled(True)
        self.calibration_initiated = True
        log.start(task="SoundCalibration", subject="None")
        task.run_in_thread()

    def test_button_clicked(self) -> None:
        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.indices2 = [i for i, val in enumerate(self.dB_expected2) if val != 0]
        self.indices2_cleared = []
        errors: list[int] = []
        ok = 0
        for i in range(len(self.dB_expected2)):
            if i not in self.indices2:
                self.gains2[i] = 0
            else:
                try:
                    self.gains2[i] = manager.water_calibration.get_valve_time(
                        i, self.dB_expected2[i]
                    )
                    ok += 1
                except Exception:
                    self.dB_expected2[i] = 0
                    self.dB_expected_line_edits2[i].setText("0")
                    self.dB_expected_line_edits2[i].setStyleSheet("")
                    errors.append(i)
                    self.indices2.remove(i)

        if errors:
            text = "The following ports can not be tested: "
            text += ", ".join([str(error) for error in errors])
            text += ". \nYou need to calibrate them first."
            QMessageBox().information(
                self.window,
                "Warning",
                text,
            )

        if ok > 0:
            manager.state = State.RUN_MANUAL
            task = SoundCalibration(self.speaker, self.gain, self.freq, self.duration)
            for line_edit in self.dB_expected_line_edits2:
                line_edit.setDisabled(True)
            self.duration_line_edit2.setDisabled(True)
            self.calibration_initiated = True
            log.start(task="SoundCalibration", subject="None")
            task.run_in_thread()
            self.test_initiated = True
        else:
            self.duration_line_edit2.setStyleSheet("")

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
            QMessageBox().information(
                self.window,
                "Warning",
                text,
            )
        else:
            text = "The calibration was saved successfully."
            QMessageBox().information(
                self.window,
                "Success",
                text,
            )
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
            for index in range(len(self.dB_obtained_line_edits)):
                if index in self.indices:
                    self.dB_obtained_line_edits[index].setEnabled(True)
                    self.dB_obtained_line_edits[index].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.dB_obtained_line_edits[index].setStyleSheet("")

        if manager.state == State.WAIT and self.test_initiated:
            self.test_initiated = False
            self.test_button.setDisabled(True)
            for index in range(len(self.dB_obtained_line_edits2)):
                if index in self.indices2:
                    self.dB_obtained_line_edits2[index].setEnabled(True)
                    self.dB_obtained_line_edits2[index].setStyleSheet(
                        "QLineEdit {border: 1px solid black;}"
                    )
                else:
                    self.dB_obtained_line_edits2[index].setStyleSheet("")

        for line_edit in self.dB_obtained_labels:
            if line_edit.text() != "0":
                self.add_button.setEnabled(True)

        if self.update_plot:
            if self.delete_row != -1:
                self.df = self.df.drop(index=self.delete_row)
                self.df = self.df.reset_index(drop=True)
                self.delete_row = -1
            self.plot_layout.update(self.df)
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

        if len(self.calibration_points) > 0:
            self.delete_button.setEnabled(True)
        else:
            self.delete_button.setDisabled(True)
        if some_port_has_two_values():
            self.save_button.setEnabled(True)
        else:
            self.save_button.setDisabled(True)

        if len(self.indices2) == len(self.indices2_cleared) and len(self.indices2) > 0:
            self.indices2 = []
            self.indices2_cleared = []

            for line_edit in self.dB_expected_line_edits2:
                line_edit.setText("0")
                line_edit.setEnabled(True)
                self.duration_line_edit2.setEnabled(True)

            for line_edit in self.dB_obtained_line_edits2:
                line_edit.setText("0")
                line_edit.setDisabled(True)
                line_edit.setStyleSheet("")
            self.calibrate_button.setEnabled(True)
            self.test_button.setEnabled(True)
            # self.plot_layout.update(self.df)
            self.info_layout.update()

    def select_port(self, value: str, index: int) -> None:
        pass

    def calibration_measured(self, value: str = "", key: str = "") -> None:
        self.dB_obtained = [0.0 for _ in range(2)]
        for line_edit in self.dB_obtained_labels:
            line_edit.setText("0")
        try:
            for index in self.indices:
                line_edit = self.dB_obtained_line_edits[index]
                result = round((float(line_edit.text()) / self.duration * 1000), 4)
                if result > 0:
                    self.dB_obtained[index] = result
                    self.dB_obtained_labels[index].setText(str(result))
        except Exception:
            pass

    def test_measured(self, value: str = "", key: str = "") -> None:
        self.dB_obtained2 = [0.0 for _ in range(2)]
        for line_edit in self.error_labels2:
            line_edit.setText("0")
        try:
            for index in self.indices2:
                line_edit = self.dB_obtained_line_edits2[index]
                result = round((float(line_edit.text()) / self.duration2 * 1000), 4)
                if result > 0:
                    self.dB_obtained2[index] = result
                    error = (
                        abs(result - self.dB_expected2[index])
                        / self.dB_expected2[index]
                        * 100
                    )
                    error = round(error, 4)
                    self.errors2[index] = error
                    text = str(result) + " (" + str(error) + "% error)"
                    self.error_labels2[index].setText(text)
                    self.ok_buttons2[index].setEnabled(True)
                    self.add_buttons2[index].setEnabled(True)
        except Exception:
            pass

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
                "port_number": i,
                "time(s)": self.gains[i],
                "water_delivered(ul)": self.dB_obtained[i],
                "calibration_number": self.calibration_number,
                "water_expected(ul)": np.nan,
                "error(%)": np.nan,
            }

            df = pd.DataFrame([row_dict])
            self.df = pd.concat([self.df, df], ignore_index=True)
            self.calibration_points.append(row_dict)

        for line_edit in self.gain_line_edits:
            line_edit.setEnabled(True)
            self.duration_line_edit.setEnabled(True)

        for line_edit in self.dB_obtained_line_edits:
            line_edit.setText("0")
            line_edit.setDisabled(True)
            line_edit.setStyleSheet("")
        self.add_button.setDisabled(True)
        self.calibrate_button.setEnabled(True)
        self.test_button.setEnabled(True)
        self.plot_layout.update(self.df)
        self.info_layout.update()

    def ok_button_clicked(self, index: int) -> None:
        self.ok_buttons2[index].setDisabled(True)
        self.add_buttons2[index].setDisabled(True)

        if self.date == "":
            self.date = time_utils.now_string()
        self.calibration_number = np.nan
        row_dict = {
            "date": self.date,
            "port_number": index + 1,
            "time(s)": self.gains2[index],
            "water_delivered(ul)": self.dB_obtained2[index],
            "calibration_number": np.nan,
            "water_expected(ul)": self.dB_obtained2[index],
            "error(%)": self.errors2[index],
        }

        self.indices2_cleared.append(index)

        df = pd.DataFrame([row_dict])
        manager.water_calibration.df = pd.concat(
            [manager.water_calibration.df, df], ignore_index=True
        )
        manager.water_calibration.save_from_df()

    def add_button2_clicked(self, index: int) -> None:
        self.ok_buttons2[index].setDisabled(True)
        self.add_buttons2[index].setDisabled(True)

        if self.date == "":
            self.date = time_utils.now_string()
        self.calibration_number = np.nan
        row_dict = {
            "date": self.date,
            "port_number": index + 1,
            "time(s)": self.gains2[index],
            "water_delivered(ul)": self.dB_obtained2[index],
            "calibration_number": np.nan,
            "water_expected(ul)": self.dB_obtained2[index],
            "error(%)": self.errors2[index],
        }

        self.indices2_cleared.append(index)

        df = pd.DataFrame([row_dict])
        self.df = pd.concat([self.df, df], ignore_index=True)
        self.calibration_points.append(row_dict)
        self.update_plot = True

    def stop_button_clicked(self) -> None:
        if manager.state.can_stop_task():
            log.info("Task manually stopped.", subject=manager.subject.name)
            manager.state = State.SAVE_MANUAL
        elif manager.state.can_go_to_wait():
            manager.state = State.WAIT
        for line_edit in self.gain_line_edits:
            line_edit.setEnabled(True)
            line_edit.setStyleSheet("")
            line_edit.setText("0")
        self.gains = [0.0 for _ in range(2)]
        self.duration_line_edit.setEnabled(True)
        self.duration_line_edit.setStyleSheet("")
        for line_edit in self.dB_expected_line_edits2:
            line_edit.setEnabled(True)
            line_edit.setStyleSheet("")
            line_edit.setText("0")
        self.dB_expected2 = [0.0 for _ in range(2)]
        self.duration_line_edit2.setEnabled(True)
        self.duration_line_edit2.setStyleSheet("")
        self.update_gui()


class CalibrationPlotLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent_layout: SoundCalibrationLayout,
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

    def update(self, df: pd.DataFrame) -> None:
        pixmap = QPixmap()
        try:
            figure = sound_calibration_plot(
                df.copy(),
                self.plot_width,
                self.plot_height,
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
            self.plot_label.setText("Plot could not be generated")


class InfoLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent_layout: SoundCalibrationLayout,
    ) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.parent_layout = parent_layout
        self.update()

    def update(self) -> None:
        self.title = self.create_and_add_label(
            "CALIBRATION POINTS", 0, 0, 40, 2, "black", bold=False
        )
        self.port_label = self.create_and_add_label(
            "Port", 2, 0, 8, 2, "black", bold=False
        )
        self.time_label = self.create_and_add_label(
            "Time(s)", 2, 6, 8, 2, "black", bold=False
        )
        self.water_label = self.create_and_add_label(
            "Water delivered(ul)", 2, 14, 24, 2, "black", bold=False
        )

        for i, point in enumerate(self.parent_layout.calibration_points):
            text = str(point["port_number"])
            self.create_and_add_label(text, 4 + 2 * i, 0, 8, 2, "black", bold=False)
            text = str(point["time(s)"])
            self.create_and_add_label(text, 4 + 2 * i, 8, 8, 2, "black", bold=False)
            text = str(point["water_delivered(ul)"])
            self.create_and_add_label(text, 4 + 2 * i, 16, 14, 2, "black", bold=False)
            self.create_and_add_button(
                "-",
                4 + 2 * i,
                30,
                5,
                2,
                partial(self.delete_point, i),
                "Delete the calibration point",
                "lightcoral",
            )

    def delete_point(self, i: int) -> None:
        utils.delete_all_elements_from_layout(self)
        self.parent_layout.calibration_points.pop(i)
        self.parent_layout.delete_row = i
        self.parent_layout.update_plot = True
        self.update()
