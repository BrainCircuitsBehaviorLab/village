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
from village.custom_classes.task import Task
from village.gui.layout import Layout
from village.manager import manager
from village.plots.sound_calibration_plot import sound_calibration_plot
from village.scripts import utils
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.scripts.utils import create_pixmap
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class DummyTask(Task):
    def close(self):
        pass


class SoundCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.sound_calibration_button.setDisabled(True)
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
        self.speaker = 0
        self.gain = 0.0
        self.duration = 0
        self.dB_obtained = 0.0
        self.dB_expected2 = 0.0
        self.speaker2 = 0
        self.gain2 = 0.0
        self.duration2 = 0
        self.error2 = 0.0
        self.dB_obtained2 = 0.0

        self.test_point: tuple[float, float] | None = None

        # input variables
        text = "You can create functions that generate specific sounds for "
        text += "calibration. These functions must be defined in "
        text += "your_script/code/sound_functions.py and included in a list of "
        text += "functions called sound_calibration_functions in the same file. \n"
        text += "Each function must take two arguments, gain and duration, "
        text += "which can be adjusted each time we run a calibration. The function "
        text += "should return a NumPy array of floats representing the sound "
        text += "waveform. In this way, the sound will be mono (single-channel) and "
        text += "can be played through the left or right speaker depending on our "
        text += "selection."

        self.sound_label = self.create_and_add_label(
            "SOUND", 8, 2, 12, 2, "black", bold=False, description=text
        )
        values = [f.__name__ for f in manager.sound_calibration_functions]
        self.sound_combo = self.create_and_add_combo_box(
            "sound", 10, 2, 30, 2, values, 0, self.calibration_changed
        )

        self.sound_label2 = self.create_and_add_label(
            "SOUND", 32, 2, 12, 2, "black", bold=False, description=text
        )
        self.sound_combo2 = self.create_and_add_combo_box(
            "sound", 34, 2, 30, 2, values, 0, self.test_changed
        )

        self.speaker_label = self.create_and_add_label(
            "SPEAKER", 13, 2, 12, 2, "black", bold=False
        )
        self.speaker_combo = self.create_and_add_combo_box(
            "speaker",
            15,
            2,
            10,
            2,
            ["left(0)", "right(1)"],
            0,
            self.calibration_changed,
        )

        self.speaker_label2 = self.create_and_add_label(
            "SPEAKER", 37, 2, 12, 2, "black", bold=False
        )
        self.speaker_combo2 = self.create_and_add_combo_box(
            "speaker", 39, 2, 10, 2, ["left(0)", "right(1)"], 0, self.test_changed
        )

        self.calibration_input_label = self.create_and_add_label(
            "CALIBRATION INPUT",
            6,
            2,
            20,
            2,
            "black",
            description=(
                "Enter a gain value(0-1) and the sound duration "
                + "to calibrate the speakers."
            ),
        )

        self.calibration_input_label = self.create_and_add_label(
            "TEST INPUT",
            30,
            2,
            20,
            2,
            "black",
            description=(
                "Enter the expected dB you want to get and the sound duration "
                + "to test the speakers"
            ),
        )

        # first input variable
        self.gain_label = self.create_and_add_label(
            "GAIN(0-1)",
            13,
            14,
            12,
            2,
            "black",
            bold=False,
            description="Gain value between 0 and 1",
        )
        self.gain_line_edit = self.create_and_add_line_edit(
            "0", 15, 14, 8, 2, self.calibration_changed
        )

        self.dB_expected_label2 = self.create_and_add_label(
            "dB EXPECTED",
            37,
            13,
            20,
            2,
            "black",
            bold=False,
            description="The expected dB value",
        )

        self.dB_expected_line_edit2 = self.create_and_add_line_edit(
            "0", 39, 14, 8, 2, self.test_changed
        )

        # duration
        text = "The duration of the sound in seconds."
        self.duration_label = self.create_and_add_label(
            "DURATION(s)", 13, 23, 12, 2, "black", bold=False, description=text
        )
        self.duration_line_edit = self.create_and_add_line_edit(
            "1", 15, 24, 8, 2, self.calibration_changed
        )

        self.duration_label2 = self.create_and_add_label(
            "DURATION(s)", 37, 24, 12, 2, "black", bold=False, description=text
        )
        self.duration_line_edit2 = self.create_and_add_line_edit(
            "1", 39, 25, 8, 2, self.test_changed
        )

        # first button
        self.calibrate_button = self.create_and_add_button(
            "CALIBRATE ->",
            15,
            36,
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
            36,
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
            6,
            51,
            20,
            2,
            "black",
            description="Enter the measured dB.",
        )

        self.calibration_output_label = self.create_and_add_label(
            "TEST OUTPUT", 30, 51, 20, 2, "black", description="Enter the measured dB."
        )

        # output dB obtained
        self.dB_obtained_label = self.create_and_add_label(
            "dB OBTAINED", 13, 51, 17, 2, "black", bold=False, description="Measured dB"
        )
        self.dB_obtained_line_edit = self.create_and_add_line_edit(
            "0", 15, 51, 8, 2, self.calibration_measured
        )
        self.dB_obtained_line_edit.setDisabled(True)

        self.dB_obtained_label2 = self.create_and_add_label(
            "dB OBTAINED", 37, 51, 17, 2, "black", bold=False, description="Measured dB"
        )
        self.dB_obtained_line_edit2 = self.create_and_add_line_edit(
            "0", 39, 51, 8, 2, self.test_measured
        )
        self.dB_obtained_line_edit2.setDisabled(True)

        # error
        self.error_label2 = self.create_and_add_label(
            "", 41, 51, 18, 2, "black", bold=False
        )

        # calibrate add button
        self.add_button = self.create_and_add_button(
            "ADD ->",
            15,
            66,
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
            66,
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
            73,
            8,
            2,
            self.add_button2_clicked,
            text,
            "lightcoral",
        )
        self.add_button2.setDisabled(True)

        # extra buttons
        save_text = "Save the calibration. At least two points are "
        save_text += "needed to build the calibration curve for each sound."
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
        self.plot_layout = CalibrationPlotLayout(self.window, 36, 87, self)
        self.addLayout(self.plot_layout, 5, 121, 38, 79)

    def change_layout(self, auto: bool = False) -> bool:
        if manager.state in [State.RUN_MANUAL, State.SAVE_MANUAL]:
            if not auto:
                QMessageBox.information(
                    self.window, "WARNING", "Wait until the task finishes."
                )
            return False
        elif auto:
            manager.changing_settings = False
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
        self.gain = 0
        self.duration = 0
        self.speaker = self.speaker_combo.currentIndex()
        self.sound_index = self.sound_combo.currentIndex()
        self.sound = manager.sound_calibration_functions[self.sound_index].__name__

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

        if self.gain > 0 and self.duration > 0:
            self.calibrate_button.setEnabled(True)
            manager.changing_settings = True
            self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setDisabled(True)
        self.calibrate_button.setDisabled(True)
        self.dB_expected2 = 0
        self.duration2 = 0
        self.speaker2 = self.speaker_combo2.currentIndex()
        self.sound_index2 = self.sound_combo2.currentIndex()
        self.sound2 = manager.sound_calibration_functions[self.sound_index2].__name__

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

        if self.dB_expected2 > 0 and self.duration2 > 0:
            self.test_button.setEnabled(True)
            manager.changing_settings = True
            self.update_status_label_buttons()

    def calibrate_button_clicked(self) -> None:
        if self.calibration_denied:
            QMessageBox.information(
                self.window,
                "Warning",
                "You need to mark the test as correct or incorrect first.",
            )
            return
        self.test_denied = True

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        manager.state = State.RUN_MANUAL
        manager.calibrating = True
        task = SoundCalibration(
            self.speaker, self.gain, self.sound_index, self.duration
        )
        manager.task = DummyTask()
        manager.task.settings.maximum_duration = self.duration + 3
        self.speaker_combo.setDisabled(True)
        self.gain_line_edit.setDisabled(True)
        self.duration_line_edit.setDisabled(True)
        self.dB_expected_line_edit2.setDisabled(True)
        self.duration_line_edit2.setDisabled(True)
        self.speaker_combo2.setDisabled(True)
        self.calibration_initiated = True
        log.start(task="SoundCalibration", subject="None")
        task.run_in_thread()

    def test_button_clicked(self) -> None:
        if self.test_denied:
            QMessageBox.information(
                self.window,
                "Warning",
                "You need to save or delete the current calibration first.",
            )
            return

        self.calibrate_button.setDisabled(True)
        self.test_button.setDisabled(True)
        ok = False

        try:
            self.gain2 = manager.sound_calibration.get_sound_gain(
                self.speaker2, self.dB_expected2, sound_name=self.sound2
            )
            self.calibration_denied = True
            ok = True
        except Exception:
            text = f"""
            \n\n\t--> SOUND CALIBRATION PROBLEM !!!!!!\n
            It is not possible to provide a valid gain value
            for a target dB of {self.dB_expected2} for the speaker {self.speaker2} and
            sound {self.sound2}.\n
            1. Make sure you have calibrated the sound you are using.\n
            2. Make sure the dB you want to obtain is within calibration range.\n
            3. Ultimately, check sound_calibration.csv in 'data'.\n
            """
            QMessageBox.information(
                self.window,
                "Warning",
                text,
            )

            self.dB_expected2 = 0
            self.dB_expected_line_edit2.setText("0")
            self.dB_expected_line_edit2.setStyleSheet("")
            self.duration_line_edit2.setStyleSheet("")

        if ok:
            manager.state = State.RUN_MANUAL
            manager.calibrating = True
            task = SoundCalibration(
                self.speaker2, self.gain2, self.sound_index2, self.duration2
            )
            manager.task = DummyTask()
            manager.task.settings.maximum_duration = self.duration2 + 3
            self.speaker_combo.setDisabled(True)
            self.gain_line_edit.setDisabled(True)
            self.duration_line_edit.setDisabled(True)
            self.dB_expected_line_edit2.setDisabled(True)
            self.duration_line_edit2.setDisabled(True)
            self.speaker_combo2.setDisabled(True)
            self.test_initiated = True
            log.start(task="SoundCalibration", subject="None")
            task.run_in_thread()

    def save_button_clicked(self) -> None:

        removed_list: list[str] = []
        filtered_df = self.df.copy()

        for sound, group in self.df.groupby("sound_name"):
            counts = group["speaker"].value_counts()

            removed_speakers = counts[counts < 2].index

            removed_list.extend(
                [f"speaker {spk}, sound {sound}" for spk in removed_speakers]
            )

            filtered_df = filtered_df[
                ~(
                    (filtered_df["sound_name"] == sound)
                    & (filtered_df["speaker"].isin(removed_speakers))
                )
            ]

        manager.sound_calibration.df = pd.concat(
            [manager.sound_calibration.df, filtered_df], ignore_index=True
        )
        manager.sound_calibration.save_from_df()

        if len(removed_list) > 0:
            text = "The following speaker and sound had only one calibration point "
            text += "and was therefore removed from the calibration: "
            text += "; ".join(removed_list)
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
        log.info("Sound calibration saved.")
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
            if not manager.sound_calibration_error:
                self.calibrate_button.setDisabled(True)
                self.test_button.setDisabled(True)
                self.dB_obtained_line_edit.setEnabled(True)
                self.dB_obtained_line_edit.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                manager.sound_calibration_error = False
                text = "It was not possible to play the calibration sound. "
                text += "Check the events for more information about the error."
                QMessageBox.information(self.window, "ERROR", text)
                self.speaker_combo.setEnabled(True)
                self.gain_line_edit.setEnabled(True)
                self.duration_line_edit.setEnabled(True)
                self.dB_obtained_line_edit.setText("0")
                self.dB_obtained_line_edit.setDisabled(True)
                self.dB_obtained_line_edit.setStyleSheet("")

        if manager.state == State.WAIT and self.test_initiated:
            self.test_initiated = False
            if not manager.sound_calibration_error:
                self.calibrate_button.setDisabled(True)
                self.test_button.setDisabled(True)
                self.dB_obtained_line_edit2.setEnabled(True)
                self.dB_obtained_line_edit2.setStyleSheet(
                    "QLineEdit {border: 1px solid black;}"
                )
            else:
                manager.sound_calibration_error = False
                text = "It was not possible to play the calibration sound. "
                text += "Check the events for more information about the error."
                QMessageBox.information(self.window, "ERROR", text)
                self.reset_values_after_ok_or_add2()

        if self.update_plot:
            if self.delete_rows:
                for row in self.delete_rows:
                    self.df = self.df.drop(index=row)
                    self.df = self.df.reset_index(drop=True)
                self.delete_rows = []
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

        if len(self.calibration_points) == 0:
            if self.allow_test and self.gain_line_edit.isEnabled():
                self.allow_test = False
                self.test_denied = False
        if some_speaker_has_two_values():
            self.save_button.setEnabled(True)
        else:
            self.save_button.setDisabled(True)

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
        self.error_label2.setText("")
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

                df = manager.sound_calibration.df.copy()

                df = df[df["speaker"] == self.speaker2]
                df = df[df["sound_name"] == self.sound2]
                max_calibration = df["calibration_number"].max()
                self.df = df[df["calibration_number"] == max_calibration]
                self.test_point = (self.gain2, result)
                self.update_plot = True
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
            "sound_name": self.sound,
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
            "sound_name": self.sound2,
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
        manager.changing_settings = False

        self.reset_values_after_ok_or_add2()

    def reset_values_after_ok_or_add2(self, delete_df=True) -> None:
        if delete_df:
            self.df = pd.DataFrame()
        self.test_point = None

        self.calibration_denied = False
        self.speaker_combo.setEnabled(True)
        self.speaker_combo2.setEnabled(True)
        self.gain_line_edit.setEnabled(True)
        self.dB_expected_line_edit2.setEnabled(True)
        self.dB_expected_line_edit2.setStyleSheet("")
        self.dB_expected_line_edit2.setText("0")
        self.duration_line_edit.setEnabled(True)
        self.duration_line_edit2.setEnabled(True)
        self.duration_line_edit2.setStyleSheet("")

        self.ok_button2.setDisabled(True)
        self.add_button2.setDisabled(True)

        self.dB_obtained_line_edit2.setText("0")
        self.dB_obtained_line_edit2.setDisabled(True)
        self.dB_obtained_line_edit2.setStyleSheet("")
        self.info_layout.update()
        self.update_plot = True

    def add_button2_clicked(self) -> None:
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
            "sound_name": self.sound2,
            "gain": self.gain2,
            "dB_obtained": self.dB_obtained2,
            "calibration_number": self.calibration_number,
            "dB_expected": np.nan,
            "error(%)": np.nan,
        }
        self.df = pd.DataFrame([row_dict])
        self.calibration_points.append(row_dict)
        self.update_plot = True

        self.reset_values_after_ok_or_add2(delete_df=False)

    def stop_button_clicked(self) -> None:
        if manager.state.can_stop_task():
            log.info("Task manually stopped.", subject=manager.subject.name)
            manager.state = State.SAVE_MANUAL
        elif manager.state.can_go_to_wait():
            manager.state = State.WAIT
        self.gain_line_edit.setEnabled(True)
        self.gain_line_edit.setStyleSheet("")
        self.gain_line_edit.setText("0")
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
            self.plot_label.setText("")


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
            "CALIBRATION POINTS", 0, 1, 40, 2, "black", bold=False
        )
        self.speaker_label = self.create_and_add_label(
            "Speaker", 2, 1, 7, 2, "black", bold=False
        )
        self.speaker_label = self.create_and_add_label(
            "Sound_name", 2, 8, 11, 2, "black", bold=False
        )
        self.gain_label = self.create_and_add_label(
            "Gain", 2, 18, 4, 2, "black", bold=False
        )
        self.dB_label = self.create_and_add_label(
            "dB_obtained", 2, 22, 24, 2, "black", bold=False
        )

        for i, point in enumerate(self.parent_layout.calibration_points):
            text = str(point["speaker"])
            self.create_and_add_label(text, 4 + 2 * i, 1, 4, 2, "black", bold=False)
            text = str(point["sound_name"])
            self.create_and_add_label(text, 4 + 2 * i, 7, 12, 2, "black", bold=False)
            text = str(point["gain"])
            self.create_and_add_label(text, 4 + 2 * i, 18, 5, 2, "black", bold=False)
            text = str(point["dB_obtained"])
            self.create_and_add_label(text, 4 + 2 * i, 24, 14, 2, "black", bold=False)
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
