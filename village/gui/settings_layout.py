from __future__ import annotations

import os
import re
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from PyQt5.QtWidgets import QInputDialog, QMessageBox

from village.classes.enums import Active, Controller, ScreenActive, State, SyncType
from village.devices.camera import cam_box, cam_corridor
from village.devices.sound_device import get_sound_devices
from village.gui.layout import Layout, LineEdit, TimeEdit, ToggleButton
from village.manager import manager
from village.scripts import utils
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import Setting, settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


row1 = 5
column1 = 1
column2 = 28
column3 = 90
column4 = 120
column5 = 149
width1 = 15
width2 = 15
width3 = 22
width4 = 21
width5 = 18
length = 22
size1 = 6
size2 = 45
size3 = 14
size4 = 10
small_box = 5
mini_box = 4


class SettingsLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.critical_changes = False
        self.draw(all=True, modify="")

    def draw(self, all: bool, modify) -> None:
        self.settings_button.setDisabled(True)

        if all:
            self.line_edits: list[LineEdit] = []
            self.line_edits_settings: list[Setting] = []

            self.time_edits: list[TimeEdit] = []
            self.time_edits_settings: list[Setting] = []

            self.toggle_buttons: list[ToggleButton] = []
            self.toggle_buttons_settings: list[Setting] = []

            self.list_of_line_edits: list[list[LineEdit]] = []
            self.list_of_line_edits_settings: list[Setting] = []

            self.list_of_toggle_buttons: list[list[ToggleButton]] = []
            self.list_of_toggle_buttons_settings: list[Setting] = []

            # first column
            row = row1
            name = "MAIN SETTINGS"
            label = self.create_and_add_label(name, row, column1, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.main_settings:
                self.create_label_and_value(row, column1, s, name, width=width1)
                row += 2

            row += 1
            name = "SOUND SETTINGS"
            label = self.create_and_add_label(name, row, column1, length, 2, "black")
            row += 2
            s = settings.sound_settings[0]
            self.create_label_and_value(row, column1, s, "", width=width1)

        if (
            all and settings.get("USE_SOUNDCARD") == Active.ON
        ) or modify == "SOUND SETTINGS":
            row = row1 + 15
            name = "SOUND SETTINGS"
            for s in settings.sound_settings[1:]:
                self.create_label_and_value(row, column1, s, name, width=width1)
                row += 2

        if all:
            row = row1 + 20
            name = "SCREEN SETTINGS"
            label = self.create_and_add_label(name, row, column1, length, 2, "black")
            row += 2
            s = settings.screen_settings[0]
            self.create_label_and_value(row, column1, s, "", width=width1)

        if (
            all and settings.get("USE_SCREEN") != ScreenActive.OFF
        ) or modify == "SCREEN SETTINGS":
            row = row1 + 24
            name = "SCREEN SETTINGS"
            for s in settings.screen_settings[1:]:
                self.create_label_and_value(row, column1, s, name, width=width1)
                row += 2

        if (
            all and settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN
        ) or modify == "TOUCHSCREEN SETTINGS":
            row = row1 + 28
            name = "TOUCHSCREEN SETTINGS"
            for s in settings.touchscreen_settings:
                self.create_label_and_value(row, column1, s, name, width=width1)
                row += 2

        if all:
            # second column
            row = row1
            name = "TELEGRAM SETTINGS"
            label = self.create_and_add_label(name, row, column2, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.telegram_settings:
                self.create_label_and_value(row, column2, s, name, width=width2)
                row += 2

        if all or modify == "DIRECTORY SETTINGS":
            row = row1 + 9
            name = "DIRECTORY SETTINGS"
            label = self.create_and_add_label(name, row, column2, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.directory_settings:
                if s.key == "APP_DIRECTORY":
                    continue
                self.create_label_and_value(row, column2, s, name, width=width2)
                row += 2

        if all:
            row += 1
            name = "SYNC SETTINGS"
            label = self.create_and_add_label(name, row, column2, length, 2, "black")
            row += 2
            s = settings.sync_settings[0]
            self.create_label_and_value(row, column2, s, "", width=width2)

        if (
            all and settings.get("SYNC_TYPE") != SyncType.OFF
        ) or modify == "SYNC SETTINGS":
            row = row1 + 30
            name = "SYNC SETTINGS"
            for s in settings.sync_settings[1:]:
                self.create_label_and_value(row, column2, s, name, width=width2)
                row += 2

        if (
            all and settings.get("SYNC_TYPE") == SyncType.SERVER
        ) or modify == "SERVER SETTINGS":
            row = row1 + 38
            name = "SERVER SETTINGS"
            for s in settings.server_settings:
                self.create_label_and_value(row, column2, s, name, width=width2)
                row += 2

        if all:
            # third column
            row = row1
            name = "DEVICE ADDRESSES"
            label = self.create_and_add_label(name, row, column3, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.device_settings:
                self.create_label_and_value(row, column3, s, name, width=width3)
                row += 2

            row += 1
            name = "HOURLY ALARMS"
            label = self.create_and_add_label(name, row, column3, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.hourly_alarm_settings:
                self.create_label_and_value(row, column3, s, name, width=width3)
                row += 2

            row += 1
            name = "TWICE-DAILY ALARMS"
            label = self.create_and_add_label(name, row, column3, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.cycle_alarm_settings:
                self.create_label_and_value(row, column3, s, name, width=width3)
                row += 2

            row += 1
            name = "END-SESSION ALARMS"
            label = self.create_and_add_label(name, row, column3, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.session_alarm_settings:
                self.create_label_and_value(row, column3, s, name, width=width3)
                row += 2

            # fourth column
            row = row1
            name = "CAMERA SETTINGS"
            label = self.create_and_add_label(name, row, column4, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.cam_framerate_settings:
                self.create_label_and_value(row, column4, s, name, width=width4)
                row += 2

            row += 1
            name = "CORRIDOR SETTINGS"
            label = self.create_and_add_label(name, row, column4, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.corridor_settings:
                self.create_label_and_value(row, column4, s, name, width=width4)
                row += 2

            row += 1
            name = "EXTRA SETTINGS"
            label = self.create_and_add_label(name, row, column4, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.extra_settings:
                self.create_label_and_value(row, column4, s, name, width=width4)
                row += 2

            # fifth column
            row = 5
            name = "VISUAL SETTINGS"
            label = self.create_and_add_label(name, row, column5, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.visual_settings:
                self.create_label_and_value(row, column5, s, name, width=width5)
                row += 2

            row = 23
            name = "CONTROLLER SETTINGS"
            label = self.create_and_add_label(name, row, column5, length, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.controller_settings:
                self.create_label_and_value(row, column5, s, name, width=width5)
                row += 2

        if (
            all and settings.get("BEHAVIOR_CONTROLLER") == Controller.BPOD
        ) or modify == "BPOD SETTINGS":
            name = "BPOD SETTINGS"
            row = row1 + 24
            for s in settings.bpod_settings:
                self.create_label_and_value(row, column5, s, name, width=width5)
                row += 2

        if all:
            self.save_button = self.create_and_add_button(
                "SAVE THE SETTINGS",
                48,
                154,
                22,
                2,
                self.save_button_clicked,
                "Apply and save the settings",
                "powderblue",
            )
            self.save_button.setDisabled(True)

            self.restore_button = self.create_and_add_button(
                "RESTORE FACTORY SETTINGS",
                48,
                176,
                22,
                2,
                self.restore_button_clicked,
                "Restore the factory settings",
                "lightcoral",
            )
            self.restore_button.clicked.connect(self.restore_button_clicked)

    def change_layout(self, auto: bool = False) -> bool:
        if auto:
            return True
        elif self.save_button.isEnabled():

            reply = QMessageBox.question(
                self.window,
                "Save changes",
                "Do you want to save the changes?",
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

    def settings_changed(self, value: str = "", key: str = "") -> None:
        manager.changing_settings = True
        self.update_status_label_buttons()
        self.save_button.setEnabled(True)

    def save_button_clicked(self) -> None:
        self.save(changing_project=False)

    def save(self, changing_project) -> None:
        sync_directory = self.create_sync_directory()

        self.save_button.setDisabled(True)
        manager.changing_settings = False

        critical_keys = [
            "USE_SOUNDCARD",
            "SOUND_DEVICE",
            "SAMPLERATE",
            "USE_SCREEN",
            "SCREEN_SIZE_MM",
            "TOUCH_RESOLUTION",
            "TOUCH_INTERVAL",
            "TELEGRAM_TOKEN",
            "TELEGRAM_CHAT",
            "HEALTHCHECKS_URL",
            "PROJECT_DIRECTORY",
            "CONTROLLER_PORT",
            "MOTOR1_PIN",
            "MOTOR2_PIN",
            "SCALE_ADDRESS",
            "TEMP_SENSOR_ADDRESS",
            "CAM_BOX_INDEX",
            "CAM_CORRIDOR_INDEX",
            "NO_DETECTION_HOURS",
            "NO_SESSION_HOURS",
            "CAM_CORRIDOR_FRAMERATE",
            "CAM_BOX_FRAMERATE",
            "CAM_BOX_RESOLUTION",
            "DETECTION_DURATION",
            "TIME_BETWEEN_DETECTIONS",
            "WEIGHT_THRESHOLD",
            "REPEAT_TARE_TIME",
            "UPDATE_TIME_TABLE",
            "SCREENSAVE_TIME",
            "CORRIDOR_VIDEO_DURATION",
            "BPOD_NET_PORT",
            "BPOD_BAUDRATE",
            "BPOD_SYNC_CHANNEL",
            "BPOD_SYNC_MODE",
            "BEHAVIOR_CONTROLLER",
            "SYNC_TYPE",
            "SAFE_DELETE",
            "MAXIMUM_SYNC_TIME",
            "SYNC_DESTINATION",
            "SYNC_DIRECTORY",
            "SERVER_USER",
            "SERVER_HOST",
            "SERVER_PORT",
        ]

        for i, line_edit in enumerate(self.line_edits):
            s = self.line_edits_settings[i]

            if s.key == "SYNC_DIRECTORY":
                line_edit.setText(sync_directory)

            if s.key in critical_keys and line_edit.text() != str(settings.get(s.key)):
                self.critical_changes = True

            if s.value_type == str:
                value = line_edit.text()

                if s.key == "SYSTEM_NAME":
                    old_value = str(settings.get("SYSTEM_NAME"))

                    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
                        text = (
                            "Are you sure you want to change the system name?\n"
                            + "It is not recommended to do this if you have "
                            + "already started collecting data for an experiment.\n"
                            + "Although the system’s data directory will "
                            + " be renamed automatically, some data may already have "
                            + "been saved in CSV files using the previous "
                            + "system name."
                        )

                        if not changing_project:
                            reply = QMessageBox.question(
                                self.window,
                                "SYSTEM_NAME",
                                text,
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No,
                            )

                            if reply == QMessageBox.Yes:
                                settings.set(s.key, value)
                                utils.change_system_directory_settings()
                                modify = "DIRECTORY SETTINGS"
                                self.remove("DIRECTORY SETTINGS")
                                self.draw(all=False, modify=modify)
                                self.critical_changes = True
                            else:
                                line_edit.setText(old_value)
                        else:
                            settings.set(s.key, value)
                            utils.change_system_directory_settings()
                            modify = "DIRECTORY SETTINGS"
                            self.remove("DIRECTORY SETTINGS")
                            self.draw(all=False, modify=modify)
                    else:
                        text = "Invalid system name. "
                        text += "It must not contain spaces or special characters."
                        QMessageBox.warning(
                            self.window,
                            "SYSTEM_NAME",
                            text,
                        )
                        line_edit.setText(old_value)
                    continue
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
            manager.cycle_change_detector = time_utils.CycleChangeDetector(
                settings.get("DAYTIME"), settings.get("NIGHTTIME")
            )
            manager.update_cycle()

        for i, toggle_button in enumerate(self.toggle_buttons):
            s = self.toggle_buttons_settings[i]

            if (
                s.key in critical_keys
                and toggle_button.text() != settings.get(s.key).name
            ):
                self.critical_changes = True

            value = toggle_button.text()
            settings.set(s.key, value)

        for i, list_line in enumerate(self.list_of_line_edits):
            s = self.list_of_line_edits_settings[i]

            if s.key in critical_keys:
                for j in range(len(list_line)):
                    if list_line[j].text() != str(settings.get(s.key)[j]):
                        self.critical_changes = True

            if s.value_type == list[int]:
                values = [field.text() for field in list_line]
                with suppress(BaseException):
                    values_int = [int(v) for v in values]
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
            if val != settings.get("SOUND_DEVICE"):
                self.critical_changes = True
            settings.set("SOUND_DEVICE", val)
        except Exception:
            pass

        cam_corridor.change = True
        cam_box.change = True

        try:  # can fail if we are changing the system name
            log.info("Settings modified.")
        except Exception:
            pass

        if self.critical_changes and not changing_project:
            text = (
                "Some of the setting changes require a system restart to take effect."
            )
            QMessageBox.information(
                self.window,
                "Restart",
                text,
            )

            self.window.reload_app()

        self.critical_changes = False

    def restore_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Restore factory settings",
            "Are you sure you want to restore to the factory settings?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            log.info("Restoring factory settings.")
            settings.restore_factory_settings()
            self.window.create_settings_layout()

    def create_label_and_value(
        self, row: int, column: int, s: Setting, type: Any, width: int = 0
    ) -> None:
        label = self.create_and_add_label(
            s.key,
            row,
            column,
            length,
            2,
            "black",
            bold=False,
            description=s.description,
        )
        label.setProperty("type", type)

        if s.key in ("DAYTIME", "NIGHTTIME"):
            value = settings.get(s.key)
            time_edit = self.create_and_add_time_edit(
                value, row, column + width, size4, 2, self.settings_changed
            )
            self.time_edits.append(time_edit)
            self.time_edits_settings.append(s)

        elif s.key == "PROJECT_DIRECTORY":
            value = settings.get(s.key)
            path = os.path.dirname(value)
            if not os.path.exists(path):
                utils.create_directories_from_path(path)
            possible_values = [os.path.join(path, name) for name in os.listdir(path)]
            possible_values += ["NEW"]
            index = possible_values.index(value) if value in possible_values else 0
            self.project_directory_combobox = self.create_and_add_combo_box(
                s.key,
                row,
                column + width,
                size2,
                2,
                possible_values,
                index,
                self.change_project_directory,
            )
        elif s.key == "TELEGRAM_TOKEN":
            value = str(settings.get(s.key))
            line_edit = self.create_and_add_line_edit(
                value, row, column + width, size2, 2, self.settings_changed
            )
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)
        elif s.key == "SOUND_DEVICE":
            possible_values = get_sound_devices()
            value = settings.get(s.key)
            index = possible_values.index(value) if value in possible_values else 0
            self.sound_device_combobox = self.create_and_add_combo_box(
                s.key,
                row,
                column + width,
                size4,
                2,
                possible_values,
                index,
                self.change_sound_device,
            )
            self.sound_device_combobox.setProperty("type", type)

        elif s.value_type in (str, int, float):
            value = str(settings.get(s.key))
            if s.key == "DATA_DIRECTORY":
                new_value = os.path.join(settings.get("PROJECT_DIRECTORY"), "data")
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "VIDEOS_DIRECTORY":
                new_value = os.path.join(
                    settings.get("PROJECT_DIRECTORY"), "data", "videos"
                )
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "SESSIONS_DIRECTORY":
                new_value = os.path.join(
                    settings.get("PROJECT_DIRECTORY"), "data", "sessions"
                )
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "SYSTEM_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size2, 2, self.settings_changed
                )

            elif s.key == "CODE_DIRECTORY":
                new_value = os.path.join(settings.get("PROJECT_DIRECTORY"), "code")
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "MEDIA_DIRECTORY":
                new_value = os.path.join(settings.get("PROJECT_DIRECTORY"), "media")
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "SYNC_DIRECTORY":
                new_value = self.create_sync_directory()
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "APP_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size2, 2, self.settings_changed
                )

            elif s.key in [
                "SERVER_USER",
                "SERVER_HOST",
                "SERVER_PORT",
                "SYNC_DESTINATION",
                "TELEGRAM_CHAT",
                "HEALTHCHECKS_URL",
                "MAXIMUM_SYNC_TIME",
            ]:
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size2, 2, self.settings_changed
                )
            elif s.key == "CONTROLLER_PORT":
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size3, 2, self.settings_changed
                )
            elif s.key in (
                "SYSTEM_NAME",
                "SAMPLERATE",
                "TOUCH_INTERVAL",
            ):
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size4, 2, self.settings_changed
                )
            else:
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, size1, 2, self.settings_changed
                )
            if s.key in (
                "BPOD_TARGET_FIRMWARE",
                "APP_DIRECTORY",
                "DATA_DIRECTORY",
                "VIDEOS_DIRECTORY",
                "SESSIONS_DIRECTORY",
                "SYSTEM_DIRECTORY",
                "CODE_DIRECTORY",
                "MEDIA_DIRECTORY",
                "SYNC_DIRECTORY",
            ):
                line_edit.setReadOnly(True)
                line_edit.setDisabled(True)
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)
        elif s.value_type == list[int]:
            values = settings.get(s.key)
            line_edits = []
            c = column
            if s.key == "CAM_BOX_RESOLUTION":
                c = column - 4
            for i, v in enumerate(values):
                value = str(v)
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    c + width + small_box * i,
                    small_box,
                    2,
                    self.settings_changed,
                )
                if s.key == "SCREEN_RESOLUTION":
                    line_edit.setReadOnly(True)
                    line_edit.setDisabled(True)
                line_edit.setProperty("type", type)
                line_edits.append(line_edit)
            self.list_of_line_edits.append(line_edits)
            self.list_of_line_edits_settings.append(s)
        elif s.value_type == list[Active]:
            values_list: list[Active] = settings.get(s.key)
            toggle_buttons = []
            for i, v in enumerate(values_list):
                possible_values = settings.get_values(s.key)
                index = settings.get_indices(s.key)[i]

                toggle_button = self.create_and_add_toggle_button(
                    s.key,
                    row,
                    column + width + mini_box * i,
                    mini_box,
                    2,
                    possible_values,
                    index,
                    self.settings_changed,
                    s.description,
                )
                toggle_button.setProperty("type", type)
                toggle_buttons.append(toggle_button)
            self.list_of_toggle_buttons.append(toggle_buttons)
            self.list_of_toggle_buttons_settings.append(s)
        else:
            possible_values = settings.get_values(s.key)
            index = settings.get_index(s.key)
            if s.key in (
                "DETECTION_COLOR",
                "USE_SOUNDCARD",
                "USE_SCREEN",
                "BEHAVIOR_CONTROLLER",
            ):
                size_to_use = size4
            else:
                size_to_use = size1
            toggle_button = self.create_and_add_toggle_button(
                s.key,
                row,
                column + width,
                size_to_use,
                2,
                possible_values,
                index,
                self.toggle_button_changed,
                s.description,
            )

            toggle_button.setProperty("type", type)
            self.toggle_buttons.append(toggle_button)
            self.toggle_buttons_settings.append(s)

    def create_sync_directory(self) -> str:
        directory = os.path.basename(settings.get("PROJECT_DIRECTORY"))
        index = next(
            (
                i
                for i, item in enumerate(self.line_edits_settings)
                if item.key == "SYNC_DESTINATION"
            ),
            0,
        )
        sync_destination = self.line_edits[index].text()
        new_value = os.path.join(sync_destination, directory + "_data")
        return new_value

    def change_sound_device(self, value: str, key: str) -> None:
        self.settings_changed(value, key)

    def toggle_button_changed(self, value: str, key: str) -> None:
        modify = ""
        if value == "OFF" and key == "USE_SOUNDCARD":
            self.remove("SOUND SETTINGS")
        elif value == "ON" and key == "USE_SOUNDCARD":
            modify = "SOUND SETTINGS"
        elif value == "OFF" and key == "USE_SCREEN":
            self.remove("SCREEN SETTINGS")
            self.remove("TOUCHSCREEN SETTINGS")
        elif value == "SCREEN" and key == "USE_SCREEN":
            modify = "SCREEN SETTINGS"
        elif value == "TOUCHSCREEN" and key == "USE_SCREEN":
            modify = "TOUCHSCREEN SETTINGS"
        elif value == "ARDUINO" and key == "BEHAVIOR_CONTROLLER":
            self.remove("BPOD SETTINGS")
        elif value == "RASPBERRY" and key == "BEHAVIOR_CONTROLLER":
            self.remove("BPOD SETTINGS")
        elif value == "BPOD" and key == "BEHAVIOR_CONTROLLER":
            modify = "BPOD SETTINGS"
        elif value == "HD" and key == "SYNC_TYPE":
            modify = "SYNC SETTINGS"
            self.remove("SERVER SETTINGS")
        elif value == "SERVER" and key == "SYNC_TYPE":
            modify = "SERVER SETTINGS"
        elif value == "OFF" and key == "SYNC_TYPE":
            self.remove("SYNC SETTINGS")
            self.remove("SERVER SETTINGS")

        self.settings_changed(value, key)
        if modify != "":
            self.draw(all=False, modify=modify)

    def remove(self, name: str) -> None:
        for i in reversed(range(len(self.line_edits))):
            if self.line_edits[i].property("type") == name:
                self.line_edits.pop(i)
                self.line_edits_settings.pop(i)
        for i in reversed(range(len(self.time_edits))):
            if self.time_edits[i].property("type") == name:
                self.time_edits.pop(i)
                self.time_edits_settings.pop(i)
        for i in reversed(range(len(self.toggle_buttons))):
            if self.toggle_buttons[i].property("type") == name:
                self.toggle_buttons.pop(i)
                self.toggle_buttons_settings.pop(i)
        for i in reversed(range(len(self.list_of_line_edits))):
            if self.list_of_line_edits[i][0].property("type") == name:
                self.list_of_line_edits.pop(i)
                self.list_of_line_edits_settings.pop(i)
        for i in reversed(range(len(self.list_of_toggle_buttons))):
            if self.list_of_toggle_buttons[i][0].property("type") == name:
                self.list_of_toggle_buttons.pop(i)
                self.list_of_toggle_buttons_settings.pop(i)
        self.delete_optional_widgets(name)

    def change_project_directory(self, value: str, key: str) -> None:
        if value == "NEW":
            text, ok = QInputDialog.getText(
                self.window,
                "NEW",
                "Enter the name of the new project. The system will restart.",
            )
            if ok and text:
                old_project = settings.get("PROJECT_DIRECTORY")
                project_dir = os.path.dirname(old_project)
                path = os.path.join(project_dir, text)
                self.save(changing_project=True)
                if self.create_project_directory(path):
                    utils.change_directory_settings(path)
                    self.window.reload_app()
                    return
            self.project_directory_combobox.blockSignals(True)
            self.project_directory_combobox.setCurrentText(
                settings.get("PROJECT_DIRECTORY")
            )
            self.project_directory_combobox.blockSignals(False)
        else:
            text = (
                "Are you sure you want to change the project directory? The system "
                + "will restart."
            )
            reply = QMessageBox.question(
                self.window,
                "Change project directory",
                text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.save(changing_project=True)
                utils.change_directory_settings(value)
                self.window.reload_app()
            else:
                self.project_directory_combobox.blockSignals(True)
                self.project_directory_combobox.setCurrentText(
                    settings.get("PROJECT_DIRECTORY")
                )
                self.project_directory_combobox.blockSignals(False)

    def create_project_directory(self, path) -> bool:
        return utils.create_directories_from_path(path)

    def update_gui(self) -> None:
        self.update_status_label_buttons()
