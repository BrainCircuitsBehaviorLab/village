from __future__ import annotations  # noqa: I001
from contextlib import suppress
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QMessageBox
from village.classes.enums import State
from village.devices.camera import cam_box, cam_corridor
from village.gui.layout import Layout, Label, LineEdit
from village.manager import manager
from village.settings import settings
from village.calibration.water_calibration import WaterCalibration
import traceback
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QLabel,
)
from village.log import log
from village.plots.water_calibration_plot import water_calibration_plot
from village.plots.create_pixmap import create_pixmap

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class WaterCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.calibration_initiated = False
        self.time_line_edits: list[LineEdit] = []
        self.total_weight_line_edits: list[LineEdit] = []
        self.water_delivered_labels: list[Label] = []

        self.water_line_edits2: list[LineEdit] = []
        self.total_weight_line_edits2: list[LineEdit] = []
        self.water_delivered_labels2: list[Label] = []
        self.error_labels2: list[Label] = []

        self.times = [0.0 for _ in range(8)]
        self.water2 = [0.0 for _ in range(8)]
        self.expected_weight2 = [0.0 for _ in range(8)]

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
            16,
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
            16,
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
            "Save calibration",
            44,
            187,
            25,
            2,
            self.delete_button_clicked,
            "Save the calibration",
            "powderblue",
        )
        self.save_button.clicked.connect(self.save_button_clicked)

        self.delete_button = self.create_and_add_button(
            "Delete calibration",
            48,
            187,
            25,
            2,
            self.delete_button_clicked,
            "Delete the calibration",
            "mistyrose",
        )
        self.delete_button.clicked.connect(self.delete_button_clicked)

        self.plot_layout = CalibrationPlotLayout(self.window, 26, 82)
        self.addLayout(self.plot_layout, 4, 130, 26, 82)

        self.info_layout = InfoLayout(self.window, 20, 82)
        self.addLayout(self.plot_layout, 30, 130, 20, 82)

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
        except Exception:
            self.iterations = 0

        for i in range(8):
            time = self.time_line_edits[i].text()
            try:
                time_float = float(time)
                self.times[i] = time_float
            except Exception:
                time = "0"

            if time != "0" and self.iterations != 0:
                self.calibrate_button.setEnabled(True)
                manager.changing_settings = True
                self.update_status_label_buttons()

    def test_changed(self, value: str = "", key: str = "") -> None:
        self.test_button.setEnabled(False)
        self.water2 = [0.0 for _ in range(8)]
        self.expected_weight2 = [0.0 for _ in range(8)]

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
        self.save_button.setDisabled(True)
        manager.changing_settings = False

        for i, line_edit in enumerate(self.line_edits):
            s = self.line_edits_settings[i]

            if s.value_type == str:
                value = line_edit.text()
                settings.set(s.key, value)
            elif s.value_type == float:
                try:
                    value_float = float(line_edit.text())
                    settings.set(s.key, value_float)
                    line_edit.setText(str(value_float))
                except ValueError:
                    line_edit.setText(str(settings.get(s.key)))

            elif s.value_type == int:
                try:
                    value_int = round(float(line_edit.text()))
                    settings.set(s.key, value_int)
                    line_edit.setText(str(value_int))
                except ValueError:
                    line_edit.setText(str(settings.get(s.key)))

        for i, time_edit in enumerate(self.time_edits):
            s = self.time_edits_settings[i]
            value = time_edit.time().toString("HH:mm")
            settings.set(s.key, value)

        for i, toggle_button in enumerate(self.toggle_buttons):
            s = self.toggle_buttons_settings[i]

            value = toggle_button.text()
            settings.set(s.key, value)

        for i, list_line in enumerate(self.list_of_line_edits):
            s = self.list_of_line_edits_settings[i]

            if s.value_type == list[int]:
                values = [field.text() for field in list_line]
                with suppress(BaseException):
                    values_int = (int(values[0]), int(values[1]))
                    settings.set(s.key, values_int)
            else:
                values = [field.text() for field in list_line]
                settings.set(s.key, values)

        for i, list_toggle in enumerate(self.list_of_toggle_buttons):
            s = self.list_of_toggle_buttons_settings[i]

            values = [field.text() for field in list_toggle]
            settings.set(s.key, values)

        try:
            val = self.sound_device_combobox.currentText()
            settings.set("SOUND_DEVICE", val)
        except AttributeError:
            pass

        cam_corridor.change = True
        cam_box.change = True

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
            for index in self.indices:
                self.total_weight_line_edits[index].setEnabled(True)
        self.add_button.setDisabled(True)
        for line_edit in self.water_delivered_labels:
            if line_edit.text() != "0":
                self.add_button.setEnabled(True)
        self.plot_layout.update_gui()
        self.info_layout.update_gui()

    def select_port(self, value: str, index: int) -> None:
        pass

    def calibration_weighted(self, value: str = "", key: str = "") -> None:
        for line_edit in self.water_delivered_labels:
            line_edit.setText("0")
        try:
            for index in self.indices:
                line_edit = self.total_weight_line_edits[index]
                result = float(line_edit.text()) / self.iterations * 1000
                if result > 0:
                    self.water_delivered_labels[index].setText(str(result))
        except Exception:
            pass

    def test_weighted(self, value: str = "", key: str = "") -> None:
        for index in self.indices:
            self.error_labels2[index].setText("0")

    def add_button_clicked(self) -> None:
        pass


class CalibrationPlotLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self.draw()

    def draw(self) -> None:
        self.plot_label = QLabel()
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.addWidget(self.plot_label, 0, 0, self.rows, self.columns)

        self.pixmap = QPixmap()

        self.plot_width = (self.columns * self.column_width - 10) / dpi
        self.plot_height = (self.rows * self.row_height - 5) / dpi

    def update_gui(self) -> None:
        try:
            figure = water_calibration_plot(
                manager.water_calibration.df.copy(),
                self.plot_width,
                self.plot_height,
            )
            pixmap = create_pixmap(figure)
        except Exception:
            log.error(
                "Can not create corridor plot",
                exception=traceback.format_exc(),
            )

        if not pixmap.isNull():
            self.plot_label.setPixmap(pixmap)
        else:
            self.plot_label.setText("Plot could not be generated")
            # TODO: should the figure be closed?


class InfoLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.draw()

    def draw(self) -> None:
        text = manager.events.df.tail(12).to_csv(sep="\t", index=False, header=False)
        self.events_text = self.create_and_add_label(text, 0, 0, 82, 20, "black")

    def update_gui(self) -> None:
        text = manager.events.df.tail(12).to_csv(sep="\t", index=False, header=False)
        self.events_text.setText(text)
