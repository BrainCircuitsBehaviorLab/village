from __future__ import annotations

import traceback
from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMessageBox, QScrollArea, QWidget

from village.calibration.sound_calibration import SoundCalibration
from village.classes.enums import State
from village.classes.task import Task
from village.gui.layout import Layout
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
        self.calibration_number = -1
        self.delete_row = -1
        self.calibration_points: list[dict] = []
        self.allow_test = False
        self.calibration_denied = False
        self.test_denied = False
        self.calibration_initiated = False
        self.test_initiated = False
        self.update_plot = False
        self.speaker = 0
        self.gain = 0.0
        self.freq = 0
        self.duration = 0
        self.dB_obtained = 0.0
        self.dB_expected2 = 0.0
        self.speaker2 = 0
        self.gain2 = 0.0
        self.freq2 = 0
        self.duration2 = 0
        self.error2 = 0.0
        self.dB_obtained2 = 0.0

        self.test_point: tuple[float, float] | None = None

        # speakers
        self.speaker_label = self.create_and_add_label(
            "SPEAKER", 7, 1, 12, 2, "black", bold=False
        )
        self.speaker_combo = self.create_and_add_combo_box(
            "speaker", 9, 1, 10, 2, ["left(0)", "right(1)"], 0, self.calibration
        )

        self.speaker_label2 = self.create_and_add_label(
            "SPEAKER", 32, 1, 12, 2, "black", bold=False
        )
        self.speaker_combo2 = self.create_and_add_combo_box(
            "speaker", 34, 1, 10, 2, ["left(0)", "right(1)"], 0, self.select_speaker2
        )

        # input
        self.calibration_input_label = self.create_and_add_label(
            "CALIBRATION INPUT",
            5,
            1,
            20,
            2,
            "black",
            description=(
                "Enter a gain value(0-1) and the sound duration and frequency "
                + "to calibrate the speakers. If the frequency is set to 0, "
                + "the calibration will be done using a white-noise sound "
                + "for all frequencies."
            ),
        )

        self.calibration_input_label = self.create_and_add_label(
            "TEST INPUT",
            30,
            1,
            20,
            2,
            "black",
            description=(
                "Enter the expected dB you want to get and the sound duration "
                + "and frequency to test the speakers. If the frequency is set to 0, "
                + "the test will be done using a white-noise sound "
                + "for all frequencies."
            ),
        )

        # first input variable
        self.gain_label = self.create_and_add_label(
            "GAIN(0-1)",
            12,
            12,
            12,
            2,
            "black",
            bold=False,
            description="Gain value between 0 and 1",
        )
        self.gain_line_edit = self.create_and_add_line_edit(
            "0", 14, 12, 8, 2, self.calibration_changed
        )

        self.dB_expected_label2 = self.create_and_add_label(
            "dB EXPECTED",
            37,
            10,
            20,
            2,
            "black",
            bold=False,
            description="The expected dB value",
        )

        self.dB_expected_line_edit2 = self.create_and_add_line_edit(
            "0", 39, 12, 8, 2, self.test_changed
        )

        # second input variable
        text = (
            "Frequency of the sound in Hz. The system will play a simple "
            + "sinusoidal tone of that frequency. Set to 0 for white noise."
        )
        self.freq_label = self.create_and_add_label(
            "FREQ", 12, 1, 12, 2, "black", bold=False, description=text
        )

        self.freq_line_edit = self.create_and_add_line_edit(
            "0", 14, 1, 8, 2, self.calibration_changed
        )

        self.freq_label2 = self.create_and_add_label(
            "FREQ", 37, 1, 20, 2, "black", bold=False, description=text
        )

        self.freq_line_edit2 = self.create_and_add_line_edit(
            "0", 39, 1, 8, 2, self.test_changed
        )

        # duration
        text = "The duration of the sound in seconds."
        self.duration_label = self.create_and_add_label(
            "DURATION(s)", 12, 23, 12, 2, "black", bold=False, description=text
        )
        self.duration_line_edit = self.create_and_add_line_edit(
            "1", 14, 24, 8, 2, self.calibration_changed
        )

        self.duration_label2 = self.create_and_add_label(
            "DURATION(s)", 37, 23, 12, 2, "black", bold=False, description=text
        )
        self.duration_line_edit2 = self.create_and_add_line_edit(
            "1", 39, 24, 8, 2, self.test_changed
        )

        # first button
        self.calibrate_button = self.create_and_add_button(
            "CALIBRATE ->",
            14,
            35,
            12,
            2,
            self.calibrate_button_clicked,
            "Calibrate the speakers with the values set in the input fields",
            "powderblue",
        )
        self.calibrate_button.setDisabled(True)

        self.test_button = self.create_and_add_button(
            "TEST ->",
            39,
            35,
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
            50,
            20,
            2,
            "black",
            description="Enter the measured dB.",
        )

        self.calibration_output_label = self.create_and_add_label(
            "TEST OUTPUT", 30, 50, 20, 2, "black", description="Enter the measured dB."
        )

        # output dB obtained
        self.dB_obtained_label = self.create_and_add_label(
            "dB OBTAINED", 12, 50, 17, 2, "black", bold=False, description="Measured dB"
        )
        self.dB_obtained_line_edit = self.create_and_add_line_edit(
            "0", 14, 50, 8, 2, self.calibration_measured
        )
        self.dB_obtained_line_edit.setDisabled(True)

        self.dB_obtained_label2 = self.create_and_add_label(
            "dB OBTAINED", 37, 50, 17, 2, "black", bold=False, description="Measured dB"
        )
        self.dB_obtained_line_edit2 = self.create_and_add_line_edit(
            "0", 39, 50, 8, 2, self.test_measured
        )
        self.dB_obtained_line_edit2.setDisabled(True)

        # error
        self.error_label2 = self.create_and_add_label(
            "", 41, 50, 18, 2, "black", bold=False
        )

        # calibrate add button
        self.add_button = self.create_and_add_button(
            "ADD ->",
            14,
            69,
            15,
            2,
            self.add_button_clicked,
            "Add this point to the list of calibration points",
            "powderblue",
        )
        self.add_button.setDisabled(True)

        # ok and add buttons
        text = (
            "The value of this test is correct. "
            + "The error is within the acceptable limit. "
            + "Save the test result in sound_calibration.csv."
        )
        self.ok_button2 = self.create_and_add_button(
            "OK",
            39,
            69,
            7,
            2,
            self.ok_button2_clicked,
            text,
            "powderblue",
        )
        self.ok_button2.setDisabled(True)

        text = (
            "The value of this test is not correct. "
            + "The error too large. "
            + "Use the test result as a new calibration point."
        )

        self.add_button2 = self.create_and_add_button(
            "FAIL ->",
            39,
            76,
            8,
            2,
            self.add_button2_clicked,
            text,
            "lightcoral",
        )
        self.add_button2.setDisabled(True)

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
        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        self.gain = 0
        self.duration = 0
        self.freq = -1
        try:
            duration = int(self.duration_line_edit.text())
            if duration > 0:
                self.duration = duration
                self.duration_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.duration_line_edit.setStyleSheet("")
        except Exception:
            self.duration_line_edit.setStyleSheet("")

        try:
            gain = float(self.gain_line_edit.text())
            if gain > 0 and gain <= 1:
                self.gain = gain
                self.gain_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.gain_line_edit.setStyleSheet("")
        except Exception:
            self.gain_line_edit.setStyleSheet("")

        try:
            freq = int(self.freq_line_edit.text())
            if freq >= 0:
                self.freq = freq
                self.freq_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.freq_line_edit.setStyleSheet("")
        except Exception:
            self.freq_line_edit.setStyleSheet("")

        if self.gain > 0 and self.duration > 0 and self.freq >= 0:
            self.calibrate_button.setEnabled(True)
            manager.changing_settings = True
            self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setDisabled(True)
        self.calibrate_button.setDisabled(True)
        self.dB_expected2 = 0
        self.duration2 = 0
        self.freq2 = -1

        try:
            duration2 = int(self.duration_line_edit2.text())
            if duration2 > 0:
                self.duration2 = duration2
                self.duration_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.duration_line_edit2.setStyleSheet("")
        except Exception:
            self.duration_line_edit2.setStyleSheet("")

        try:
            dB_expected2 = float(self.dB_expected_line_edit2.text())
            if dB_expected2 > 0:
                self.dB_expected2 = dB_expected2
                self.dB_expected_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.dB_expected_line_edit2.setStyleSheet("")
        except Exception:
            self.dB_expected_line_edit2.setStyleSheet("")

        try:
            freq2 = int(self.freq_line_edit2.text())
            if freq2 >= 0:
                self.freq2 = freq2
                self.freq_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                self.freq_line_edit2.setStyleSheet("")
        except Exception:
            self.freq_line_edit2.setStyleSheet("")

        if self.dB_expected2 > 0 and self.duration2 > 0 and self.freq2 >= 0:
            self.test_button.setEnabled(True)
            manager.changing_settings = True
            self.update_status_label_buttons()

    def calibrate_button_clicked(self) -> None:
        if self.calibration_denied:
            QMessageBox().information(
                self.window,
                "Warning",
                "You need to mark the test as correct or incorrect first.",
            )
            return
        self.test_denied = True

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        manager.state = State.RUN_MANUAL
        task = SoundCalibration(self.speaker, self.gain, self.freq, self.duration)
        manager.task = Task()
        manager.task.settings.maximum_duration = self.duration + 3
        self.speaker_combo.setDisabled(True)
        self.gain_line_edit.setDisabled(True)
        self.freq_line_edit.setDisabled(True)
        self.duration_line_edit.setDisabled(True)
        self.calibration_initiated = True
        log.start(task="SoundCalibration", subject="None")
        task.run_in_thread()

    def test_button_clicked(self) -> None:
        if self.test_denied:
            QMessageBox().information(
                self.window,
                "Warning",
                "You need to save or delete the current calibration first.",
            )
            return
        self.calibration_denied = True

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        ok = False

        try:
            self.gain2 = manager.sound_calibration.get_sound_gain(
                self.speaker2, self.dB_expected2, freq=self.freq2
            )
            ok = True
        except Exception:
            self.dB_expected2 = 0
            self.dB_expected_line_edit2.setText("0")
            self.dB_expected_line_edit2.setStyleSheet("")
            self.duration_line_edit2.setStyleSheet("")

            text = "Using a frequency value of: "
            text += str(self.freq2)
            text += ". \nThe following speaker can not be tested: "
            text += str(self.speaker2)
            text += ". \nYou need to calibrate it first."
            QMessageBox().information(
                self.window,
                "Warning",
                text,
            )

        if ok:
            manager.state = State.RUN_MANUAL
            task = SoundCalibration(
                self.speaker2, self.gain2, self.freq2, self.duration2
            )
            manager.task = Task()
            manager.task.settings.maximum_duration = self.duration2 + 3
            self.dB_expected_line_edit2.setDisabled(True)
            self.duration_line_edit2.setDisabled(True)
            self.freq_line_edit2.setDisabled(True)
            self.speaker_combo2.setDisabled(True)
            self.test_initiated = True
            log.start(task="SoundCalibration", subject="None")
            task.run_in_thread()

    def save_button_clicked(self) -> None:

        removed_list: list[str] = []
        filtered_df = self.df.copy()

        for freq, group in self.df.groupby("frequency"):
            counts = group["speaker"].value_counts()

            removed_speakers = counts[counts < 2].index

            removed_list.extend(
                [f"speaker {spk}, freq {freq}" for spk in removed_speakers]
            )

            filtered_df = filtered_df[
                ~(
                    (filtered_df["frequency"] == freq)
                    & (filtered_df["speaker"].isin(removed_speakers))
                )
            ]

        manager.sound_calibration.df = pd.concat(
            [manager.sound_calibration.df, filtered_df], ignore_index=True
        )
        manager.sound_calibration.save_from_df()

        if len(removed_list) > 0:
            text = "The following speaker and frequency had only one calibration point "
            text += "and was therefore removed from the calibration: "
            text += "; ".join(removed_list)
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
        self.window.create_sound_calibration_layout()

    def delete_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Delete calibration",
            "Are you sure you want to delete the calibration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.window.create_sound_calibration_layout()

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if manager.state == State.WAIT and self.calibration_initiated:
            self.calibration_initiated = False
            self.calibrate_button.setDisabled(True)
            self.test_button.setDisabled(True)
            self.dB_obtained_line_edit.setEnabled(True)
            self.dB_obtained_line_edit.setStyleSheet(
                "QLineEdit {border: 1px solid black;}"
            )

        if manager.state == State.WAIT and self.test_initiated:
            self.test_initiated = False
            self.calibrate_button.setDisabled(True)
            self.test_button.setDisabled(True)
            self.dB_obtained_line_edit2.setEnabled(True)
            self.dB_obtained_line_edit2.setStyleSheet(
                "QLineEdit {border: 1px solid black;}"
            )

        if self.update_plot:
            if self.delete_row != -1:
                self.df = self.df.drop(index=self.delete_row)
                self.df = self.df.reset_index(drop=True)
                self.delete_row = -1
            self.plot_layout.update(self.df, self.test_point)
            self.update_plot = False

        def some_speaker_has_two_values() -> bool:
            speaker_counts = []
            for point in self.calibration_points:
                speaker = point.get("speaker")
                if speaker in speaker_counts:
                    return True
                else:
                    speaker_counts.append(speaker)
            return False

        if len(self.calibration_points) > 0:
            self.delete_button.setEnabled(True)
        else:
            self.delete_button.setDisabled(True)
            if self.allow_test and self.gain_line_edit.isEnabled():
                self.allow_test = False
                self.test_denied = False
        if some_speaker_has_two_values():
            self.save_button.setEnabled(True)
        else:
            self.save_button.setDisabled(True)

    def select_speaker(self, value: str, key: int) -> None:
        self.speaker = 0 if value == "left(0)" else 1

    def select_speaker2(self, value: str, key: int) -> None:
        self.speaker2 = 0 if value == "left(0)" else 1

    def calibration_measured(self, value: str = "", key: str = "") -> None:
        self.dB_obtained = 0
        try:
            result = round(float(self.dB_obtained_line_edit.text()), 4)
            if result > 0:
                self.dB_obtained = result
                self.add_button.setEnabled(True)
        except Exception:
            pass

    def test_measured(self, value: str = "", key: str = "") -> None:
        self.dB_obtained2 = 0
        self.error_label2.setText("0")
        try:
            result = round(float(self.dB_obtained_line_edit2.text()), 4)
            if result > 0:
                self.dB_obtained2 = result
                error = abs(result - self.dB_expected2) / self.dB_expected2 * 100
                error = round(error, 4)
                self.error2 = error
                text = str(error) + "% error"
                self.error_label2.setText(text)
                self.ok_button2.setEnabled(True)
                self.add_button2.setEnabled(True)
        except Exception:
            pass

    def add_button_clicked(self) -> None:
        if self.date == "":
            self.date = time_utils.now_string()
        if self.calibration_number < 0:
            try:
                max_value = manager.sound_calibration.df["calibration_number"].max()
                if pd.notna(max_value):
                    self.calibration_number = max_value + 1
                else:
                    self.calibration_number = 1
            except Exception:
                self.calibration_number = 1

        row_dict = {
            "date": self.date,
            "speaker": self.speaker,
            "frequency": self.freq,
            "gain": self.gain,
            "dB_obtained": self.dB_obtained,
            "calibration_number": self.calibration_number,
            "dB_expected": np.nan,
            "error(%)": np.nan,
        }

        df = pd.DataFrame([row_dict])
        self.df = pd.concat([self.df, df], ignore_index=True)
        self.calibration_points.append(row_dict)

        self.speaker_combo.setEnabled(True)
        self.gain_line_edit.setEnabled(True)
        self.freq_line_edit.setEnabled(True)
        self.duration_line_edit.setEnabled(True)

        self.dB_obtained_line_edit.setText("0")
        self.dB_obtained_line_edit.setDisabled(True)
        self.dB_obtained_line_edit.setStyleSheet("")

        self.add_button.setDisabled(True)
        self.plot_layout.update(self.df, self.test_point)
        self.info_layout.update()

    def ok_button2_clicked(self) -> None:
        if self.date == "":
            self.date = time_utils.now_string()

        row_dict = {
            "date": self.date,
            "speaker": self.speaker2,
            "frequency": self.freq2,
            "gain": self.gain2,
            "dB_obtained": self.dB_obtained2,
            "calibration_number": -1,
            "dB_expected": self.dB_expected2,
            "error(%)": self.error2,
        }

        df = pd.DataFrame([row_dict])
        manager.sound_calibration.df = pd.concat(
            [manager.sound_calibration.df, df], ignore_index=True
        )
        manager.sound_calibration.save_from_df()

        self.reset_values_after_ok_or_add2()

    def reset_values_after_ok_or_add2(self) -> None:
        self.calibration_denied = False
        self.speaker_combo2.setEnabled(True)
        self.dB_expected_line_edit2.setEnabled(True)
        self.freq_line_edit2.setEnabled(True)
        self.duration_line_edit2.setEnabled(True)

        self.ok_button2.setDisabled(True)
        self.add_button2.setDisabled(True)
        self.dB_expected_line_edit2.setText("0")
        self.dB_expected_line_edit2.setEnabled(True)
        self.duration_line_edit2.setEnabled(True)

        self.dB_obtained_line_edit2.setText("0")
        self.dB_obtained_line_edit2.setDisabled(True)
        self.dB_obtained_line_edit2.setStyleSheet("")
        self.info_layout.update()

    def add_button2_clicked(self) -> None:
        self.ok_button2_clicked()
        self.test_denied = True

        if self.calibration_number < 0:
            try:
                max_value = manager.sound_calibration.df["calibration_number"].max()
                if pd.notna(max_value):
                    self.calibration_number = max_value + 1
                else:
                    self.calibration_number = 1
            except Exception:
                self.calibration_number = 1

        row_dict = {
            "date": self.date,
            "speaker": self.speaker2,
            "frequency": self.freq2,
            "gain": self.gain2,
            "dB_obtained": self.dB_obtained2,
            "calibration_number": self.calibration_number,
            "dB_expected": np.nan,
            "error(%)": np.nan,
        }

        df = pd.DataFrame([row_dict])
        self.df = pd.concat([self.df, df], ignore_index=True)
        self.calibration_points.append(row_dict)
        self.update_plot = True

        self.reset_values_after_ok_or_add2()

    def stop_button_clicked(self) -> None:
        if manager.state.can_stop_task():
            log.info("Task manually stopped.", subject=manager.subject.name)
            manager.state = State.SAVE_MANUAL
        elif manager.state.can_go_to_wait():
            manager.state = State.WAIT
        self.gain_line_edit.setEnabled(True)
        self.gain_line_edit.setStyleSheet("")
        self.gain_line_edit.setText("0")
        self.freq_line_edit.setEnabled(True)
        self.freq_line_edit.setStyleSheet("")
        self.freq_line_edit.setText("0")
        self.gain = 0.0
        self.duration_line_edit.setEnabled(True)
        self.duration_line_edit.setStyleSheet("")
        self.dB_expected_line_edit2.setEnabled(True)
        self.dB_expected_line_edit2.setStyleSheet("")
        self.dB_expected_line_edit2.setText("0")
        self.dB_expected2 = 0.0
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

    def update(self, df: pd.DataFrame, test_point: tuple[float, float] | None) -> None:
        pixmap = QPixmap()
        try:
            figure = sound_calibration_plot(
                df.copy(),
                self.plot_width,
                self.plot_height,
                test_point,
            )
            pixmap = create_pixmap(figure)
        except Exception:
            log.error(
                "Can not create sound calibration plot",
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
        self.speaker_label = self.create_and_add_label(
            "Speaker", 2, 0, 8, 2, "black", bold=False
        )
        self.freq_label = self.create_and_add_label(
            "Freq", 2, 8, 8, 2, "black", bold=False
        )
        self.gain_label = self.create_and_add_label(
            "Gain", 2, 14, 8, 2, "black", bold=False
        )
        self.dB_label = self.create_and_add_label(
            "dB_obtained", 2, 21, 24, 2, "black", bold=False
        )

        for i, point in enumerate(self.parent_layout.calibration_points):
            text = str(point["speaker"])
            self.create_and_add_label(text, 4 + 2 * i, 0, 8, 2, "black", bold=False)
            text = str(point["frequency"])
            self.create_and_add_label(text, 4 + 2 * i, 8, 8, 2, "black", bold=False)
            text = str(point["gain"])
            self.create_and_add_label(text, 4 + 2 * i, 14, 8, 2, "black", bold=False)
            text = str(point["dB_obtained"])
            self.create_and_add_label(text, 4 + 2 * i, 21, 14, 2, "black", bold=False)
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
        if len(self.parent_layout.calibration_points) == 0:
            self.parent_layout.allow_test = True
        self.parent_layout.delete_row = i
        self.parent_layout.update_plot = True
        self.update()
