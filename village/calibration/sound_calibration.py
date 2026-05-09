from __future__ import annotations

import time
import traceback
from functools import partial
from threading import Thread
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMessageBox, QScrollArea, QWidget

from village.classes.enums import Active, State
from village.custom_classes.calibration_base import CalibrationBase
from village.custom_classes.task import Task
from village.devices.sound_device import sound_device
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


# ── Sound runner (internal) ────────────────────────────────────────────────────


class _SoundCalibration:
    """Plays a sound at a given gain/duration for calibration measurement."""

    def __init__(
        self, speaker: int, gain: float, sound_index: int, duration: float
    ) -> None:
        self.speaker = speaker
        self.gain = gain
        self.sound_index = sound_index
        self.duration = duration

    def run(self) -> None:
        try:
            generator = manager.sound_calibration_functions[self.sound_index]
            sound = generator(duration=self.duration, gain=self.gain)
            if self.speaker == 0:
                sound_device.load(sound, None)
            else:
                sound_device.load(None, sound)
            sound_device.play()
            time.sleep(self.duration + 1)
            sound_device.stop()
        except Exception:
            log.error("Error calibrating sound", exception=traceback.format_exc())
            manager.sound_calibration_error = True

    def run_in_thread(self, daemon: bool = True) -> None:
        self.process = Thread(target=self.run, daemon=daemon)
        self.process.start()

    def close(self) -> None:
        pass


class _DummyTask(Task):
    """Minimal task used as a placeholder during sound calibration."""

    def close(self) -> None:
        pass


# ── Calibration panel ──────────────────────────────────────────────────────────


class SoundCalibration(CalibrationBase):
    """Sound speaker calibration and testing panel."""

    name = "SOUND CALIBRATION"
    col_name = "sound_calibration"
    col_columns = [
        "date",
        "speaker",
        "sound_name",
        "gain",
        "dB_obtained",
        "calibration_number",
        "dB_expected",
        "error(%)",
    ]
    col_types = [str, int, str, float, float, int, float, float]

    @classmethod
    def is_active(cls) -> bool:
        return settings.get("USE_SOUNDCARD") == Active.ON

    def draw(self) -> None:
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False

        self.session_df = pd.DataFrame()
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

        # sound function description tooltip
        sound_tip = (
            "You can create functions that generate specific sounds for "
            "calibration. These functions must be defined in "
            "your_script/code/sound_functions.py and included in a list of "
            "functions called sound_calibration_functions in the same file. \n"
            "Each function must take two arguments, gain and duration, "
            "which can be adjusted each time we run a calibration. The function "
            "should return a NumPy array of floats representing the sound "
            "waveform. In this way, the sound will be mono (single-channel) and "
            "can be played through the left or right speaker depending on our "
            "selection."
        )

        values = [f.__name__ for f in manager.sound_calibration_functions]

        # ── calibration input ──────────────────────────────────────────────────
        self.layout.create_and_add_label(
            "CALIBRATION INPUT",
            0,
            2,
            20,
            2,
            "black",
            description=(
                "Enter a gain value(0-1) and the sound duration "
                "to calibrate the speakers."
            ),
        )
        self.layout.create_and_add_label(
            "SOUND", 2, 2, 12, 2, "black", bold=False, description=sound_tip
        )
        self.sound_combo = self.layout.create_and_add_combo_box(
            "sound", 4, 2, 30, 2, values, 0, self.calibration_changed
        )
        self.layout.create_and_add_label("SPEAKER", 7, 2, 12, 2, "black", bold=False)
        self.speaker_combo = self.layout.create_and_add_combo_box(
            "speaker",
            9,
            2,
            10,
            2,
            ["left(0)", "right(1)"],
            0,
            self.calibration_changed,
        )
        self.layout.create_and_add_label(
            "GAIN(0-1)",
            7,
            14,
            12,
            2,
            "black",
            bold=False,
            description="Gain value between 0 and 1",
        )
        self.gain_line_edit = self.layout.create_and_add_line_edit(
            "0", 9, 14, 8, 2, self.calibration_changed
        )
        self.layout.create_and_add_label(
            "DURATION(s)",
            7,
            23,
            12,
            2,
            "black",
            bold=False,
            description="The duration of the sound in seconds.",
        )
        self.duration_line_edit = self.layout.create_and_add_line_edit(
            "1", 9, 24, 8, 2, self.calibration_changed
        )
        self.calibrate_button = self.layout.create_and_add_button(
            "CALIBRATE ->",
            9,
            36,
            12,
            2,
            self.calibrate_button_clicked,
            "Calibrate the speakers with the values set in the input fields",
            "powderblue",
        )
        self.calibrate_button.setDisabled(True)

        # ── calibration output ─────────────────────────────────────────────────
        self.layout.create_and_add_label(
            "CALIBRATION OUTPUT",
            0,
            51,
            20,
            2,
            "black",
            description="Enter the measured dB.",
        )
        self.layout.create_and_add_label(
            "dB OBTAINED",
            7,
            51,
            17,
            2,
            "black",
            bold=False,
            description="Measured dB",
        )
        self.dB_obtained_line_edit = self.layout.create_and_add_line_edit(
            "0", 9, 51, 8, 2, self.calibration_measured
        )
        self.dB_obtained_line_edit.setDisabled(True)
        self.add_button = self.layout.create_and_add_button(
            "ADD ->",
            9,
            66,
            15,
            2,
            self.add_button_clicked,
            "Add this point to the list of calibration points",
            "powderblue",
        )
        self.add_button.setDisabled(True)

        # ── test input ─────────────────────────────────────────────────────────
        self.layout.create_and_add_label(
            "TEST INPUT",
            23,
            2,
            20,
            2,
            "black",
            description=(
                "Enter the expected dB you want to get and the sound duration "
                "to test the speakers"
            ),
        )
        self.layout.create_and_add_label(
            "SOUND", 25, 2, 12, 2, "black", bold=False, description=sound_tip
        )
        self.sound_combo2 = self.layout.create_and_add_combo_box(
            "sound", 27, 2, 30, 2, values, 0, self.test_changed
        )
        self.layout.create_and_add_label("SPEAKER", 30, 2, 12, 2, "black", bold=False)
        self.speaker_combo2 = self.layout.create_and_add_combo_box(
            "speaker", 32, 2, 10, 2, ["left(0)", "right(1)"], 0, self.test_changed
        )
        self.layout.create_and_add_label(
            "dB EXPECTED",
            30,
            13,
            20,
            2,
            "black",
            bold=False,
            description="The expected dB value",
        )
        self.dB_expected_line_edit2 = self.layout.create_and_add_line_edit(
            "0", 32, 14, 8, 2, self.test_changed
        )
        self.layout.create_and_add_label(
            "DURATION(s)",
            30,
            24,
            12,
            2,
            "black",
            bold=False,
            description="The duration of the sound in seconds.",
        )
        self.duration_line_edit2 = self.layout.create_and_add_line_edit(
            "1", 32, 25, 8, 2, self.test_changed
        )
        self.test_button = self.layout.create_and_add_button(
            "TEST ->",
            32,
            36,
            12,
            2,
            self.test_button_clicked,
            "Test the calibration of the speakers",
            "powderblue",
        )
        self.test_button.setDisabled(True)

        # ── test output ────────────────────────────────────────────────────────
        self.layout.create_and_add_label(
            "TEST OUTPUT",
            23,
            51,
            20,
            2,
            "black",
            description="Enter the measured dB.",
        )
        self.layout.create_and_add_label(
            "dB OBTAINED",
            30,
            51,
            17,
            2,
            "black",
            bold=False,
            description="Measured dB",
        )
        self.dB_obtained_line_edit2 = self.layout.create_and_add_line_edit(
            "0", 32, 51, 8, 2, self.test_measured
        )
        self.dB_obtained_line_edit2.setDisabled(True)
        self.error_label2 = self.layout.create_and_add_label(
            "", 34, 51, 18, 2, "black", bold=False
        )
        self.ok_button2 = self.layout.create_and_add_button(
            "OK",
            32,
            66,
            7,
            2,
            self.ok_button2_clicked,
            "The value is correct. Save the test result.",
            "powderblue",
        )
        self.ok_button2.setDisabled(True)
        self.add_button2 = self.layout.create_and_add_button(
            "FAIL ->",
            32,
            73,
            8,
            2,
            self.add_button2_clicked,
            "The error is too large. Use the result as a new calibration point.",
            "lightcoral",
        )
        self.add_button2.setDisabled(True)

        # ── save / delete ──────────────────────────────────────────────────────
        self.save_button = self.layout.create_and_add_button(
            "SAVE CALIBRATION",
            38,
            152,
            20,
            2,
            self.save_button_clicked,
            "Save the calibration. At least two points are needed per sound.",
            "powderblue",
        )
        self.save_button.setDisabled(True)
        self.delete_button = self.layout.create_and_add_button(
            "DELETE CALIBRATION",
            41,
            152,
            20,
            2,
            self.delete_button_clicked,
            "Delete the calibration",
            "lightcoral",
        )

        # ── info layout ────────────────────────────────────────────────────────
        widget = QWidget()
        widget.setStyleSheet("background-color: #E0E0E0;")
        self.info_layout = _InfoLayout(self.window, 40, 32, self)
        widget.setLayout(self.info_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area, 0, 85, 44, 36)

        # ── plot layout ────────────────────────────────────────────────────────
        self.plot_layout = _CalibrationPlotLayout(self.window, 36, 51, self)
        self.layout.addLayout(self.plot_layout, 0, 121, 38, 51)

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
            if 0 < gain <= 1:
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
            dB = float(self.dB_expected_line_edit2.text())
            if dB > 0:
                self.dB_expected2 = dB
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
        task = _SoundCalibration(
            self.speaker, self.gain, self.sound_index, self.duration
        )
        manager.task = _DummyTask()
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
            self.gain2 = self.get_sound_gain(
                self.speaker2, self.dB_expected2, sound_name=self.sound2
            )
            self.calibration_denied = True
            ok = True
        except Exception:
            text = (
                f"\n\n\t--> SOUND CALIBRATION PROBLEM !!!!!!\n\n"
                f"It is not possible to provide a valid gain value\n"
                f"for a target dB of {self.dB_expected2} for speaker "
                f"{self.speaker2} and sound {self.sound2}.\n\n"
                f"1. Make sure you have calibrated the sound you are using.\n"
                f"2. Make sure the dB you want is within calibration range.\n"
                f"3. Check sound_calibration.csv in 'data'.\n"
            )
            QMessageBox.information(self.window, "Warning", text)
            self.dB_expected2 = 0
            self.dB_expected_line_edit2.setText("0")
            self.dB_expected_line_edit2.setStyleSheet("")
            self.duration_line_edit2.setStyleSheet("")
        if ok:
            manager.state = State.RUN_MANUAL
            manager.calibrating = True
            task = _SoundCalibration(
                self.speaker2, self.gain2, self.sound_index2, self.duration2
            )
            manager.task = _DummyTask()
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
        filtered_df = self.session_df.copy()
        for sound, group in self.session_df.groupby("sound_name"):
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
        self.df = pd.concat([self.df, filtered_df], ignore_index=True)
        self.save_from_df()
        if removed_list:
            text = (
                "The following speaker/sound combinations had only one calibration "
                "point and were removed: " + "; ".join(removed_list)
            )
            QMessageBox.information(self.window, "Warning", text)
        else:
            QMessageBox.information(
                self.window, "Success", "The calibration was saved successfully."
            )
        log.info("Sound calibration saved.")
        self.reset()

    def delete_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Delete calibration",
            "Are you sure you want to delete the calibration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.reset()

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
                text = (
                    "It was not possible to play the calibration sound. "
                    "Check the events for more information about the error."
                )
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
                text = (
                    "It was not possible to play the calibration sound. "
                    "Check the events for more information about the error."
                )
                QMessageBox.information(self.window, "ERROR", text)
                self.reset_values_after_ok_or_add2()

        if self.update_plot:
            if self.delete_rows:
                for row in self.delete_rows:
                    self.session_df = self.session_df.drop(index=row)
                    self.session_df = self.session_df.reset_index(drop=True)
                self.delete_rows = []
            self.plot_layout.update(self.session_df, self.test_point)
            self.update_plot = False

        def some_speaker_has_two_values() -> bool:
            speaker_counts: list = []
            for point in self.calibration_points:
                speaker = point.get("speaker")
                if speaker in speaker_counts:
                    return True
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
                self.error2 = round(error, 4)
                self.error_label2.setText(str(self.error2) + "% error")
                self.ok_button2.setEnabled(True)
                self.add_button2.setEnabled(True)
                df = self.df.copy()
                df = df[df["speaker"] == self.speaker2]
                df = df[df["sound_name"] == self.sound2]
                max_calibration = df["calibration_number"].max()
                self.session_df = df[df["calibration_number"] == max_calibration]
                self.test_point = (self.gain2, result)
                self.update_plot = True
        except Exception:
            pass

    def add_button_clicked(self) -> None:
        if self.date == "":
            self.date = time_utils.now_string()
        if self.calibration_number < 0:
            try:
                max_value = self.df["calibration_number"].max()
                self.calibration_number = (
                    int(max_value) + 1 if pd.notna(max_value) else 1
                )
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
        self.session_df = pd.concat([self.session_df, df], ignore_index=True)
        self.calibration_points.append(row_dict)
        self.speaker_combo.setEnabled(True)
        self.gain_line_edit.setEnabled(True)
        self.duration_line_edit.setEnabled(True)
        self.dB_obtained_line_edit.setText("0")
        self.dB_obtained_line_edit.setDisabled(True)
        self.dB_obtained_line_edit.setStyleSheet("")
        self.add_button.setDisabled(True)
        self.plot_layout.update(self.session_df, self.test_point)
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
        self.df = pd.concat([self.df, df], ignore_index=True)
        self.save_from_df()
        manager.changing_settings = False
        self.reset_values_after_ok_or_add2()

    def reset_values_after_ok_or_add2(self, delete_df: bool = True) -> None:
        if delete_df:
            self.session_df = pd.DataFrame()
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
                max_value = self.df["calibration_number"].max()
                self.calibration_number = (
                    int(max_value) + 1 if pd.notna(max_value) else 1
                )
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
        df = pd.DataFrame([row_dict])
        self.session_df = pd.concat([self.session_df, df], ignore_index=True)
        self.calibration_points.append(row_dict)
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


# ── Internal sub-layouts ───────────────────────────────────────────────────────


class _CalibrationPlotLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent: SoundCalibration,
    ) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.parent = parent
        self._draw()

    def _draw(self) -> None:
        self.plot_label = QLabel()
        self.plot_label.setStyleSheet(
            "QLabel {border: 1px solid gray; background-color: white;}"
        )
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.layout.addWidget(self.plot_label, 0, 0, self.rows, self.columns)
        self.pixmap = QPixmap()
        self.plot_width = (self.columns * self.column_width - 10) / dpi
        self.plot_height = (self.rows * self.row_height - 5) / dpi

    def update(self, df: pd.DataFrame, test_point: tuple[float, float] | None) -> None:
        pixmap = QPixmap()
        try:
            figure = sound_calibration_plot(
                df.copy(), self.plot_width, self.plot_height, test_point
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


class _InfoLayout(Layout):
    def __init__(
        self,
        window: GuiWindow,
        rows: int,
        columns: int,
        parent: SoundCalibration,
    ) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.parent = parent
        self.update()

    def update(self) -> None:
        self.layout.create_and_add_label(
            "CALIBRATION POINTS", 0, 1, 40, 2, "black", bold=False
        )
        self.layout.create_and_add_label("Speaker", 2, 1, 7, 2, "black", bold=False)
        self.layout.create_and_add_label("Sound_name", 2, 8, 11, 2, "black", bold=False)
        self.layout.create_and_add_label("Gain", 2, 18, 4, 2, "black", bold=False)
        self.layout.create_and_add_label(
            "dB_obtained", 2, 22, 24, 2, "black", bold=False
        )
        for i, point in enumerate(self.parent.calibration_points):
            self.layout.create_and_add_label(
                str(point["speaker"]), 4 + 2 * i, 1, 4, 2, "black", bold=False
            )
            self.layout.create_and_add_label(
                str(point["sound_name"]), 4 + 2 * i, 7, 12, 2, "black", bold=False
            )
            self.layout.create_and_add_label(
                str(point["gain"]), 4 + 2 * i, 18, 5, 2, "black", bold=False
            )
            self.layout.create_and_add_label(
                str(point["dB_obtained"]), 4 + 2 * i, 24, 14, 2, "black", bold=False
            )
            self.layout.create_and_add_button(
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
        self.parent.calibration_points.pop(i)
        if len(self.parent.calibration_points) == 0:
            self.parent.allow_test = True
        self.parent.delete_rows.append(i)
        self.parent.update_plot = True
        self.update()
