from __future__ import annotations

import os
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from PyQt5.QtWidgets import QInputDialog, QMessageBox

from village.classes.enums import Active, ScreenActive, State
from village.devices.camera import cam_box, cam_corridor
from village.devices.sound_device import get_sound_devices
from village.gui.layout import Layout, LineEdit, TimeEdit, ToggleButton
from village.manager import manager
from village.scripts import utils
from village.settings import Setting, settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


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

            row = 6
            name = "MAIN SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.main_settings:
                self.create_label_and_value(row, 0, s, name, width=27)
                row += 2

            row += 4
            name = "CORRIDOR SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.corridor_settings:
                self.create_label_and_value(row, 0, s, name, width=27)
                row += 2

            row += 4
            name = "ALARM SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.alarm_settings:
                self.create_label_and_value(row, 0, s, name, width=27)
                row += 2

        if all or modify == "DIRECTORY SETTINGS":
            row = 6
            name = "DIRECTORY SETTINGS"
            label = self.create_and_add_label(name, row, 128, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.directory_settings:
                self.create_label_and_value(row, 128, s, name, width=20)
                row += 2

        if all:
            row += 4
            name = "TELEGRAM SETTINGS"
            label = self.create_and_add_label(name, row, 128, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.telegram_settings:
                self.create_label_and_value(row, 128, s, name, width=20)
                row += 2

        if all:
            row += 4
            name = "SERVER SETTINGS"
            label = self.create_and_add_label(name, row, 128, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.server_settings:
                self.create_label_and_value(row, 128, s, name, width=20)
                row += 2

        if all:
            row = 6
            name = "SOUND SETTINGS"
            label = self.create_and_add_label(name, row, 44, 30, 2, "black")
            row = 8
            s = settings.sound_settings[0]
            self.create_label_and_value(row, 44, s, "")

        if (
            all and settings.get("USE_SOUNDCARD") == Active.ON
        ) or modify == "SOUND SETTINGS":
            row = 10
            name = "SOUND SETTINGS"
            for s in settings.sound_settings[1:]:
                self.create_label_and_value(row, 44, s, name)
                row += 2

        if all:
            row = 16
            name = "SCREEN SETTINGS"
            label = self.create_and_add_label(name, row, 44, 30, 2, "black")
            row = 18
            s = settings.screen_settings[0]
            self.create_label_and_value(row, 44, s, "")

        if (
            all and settings.get("USE_SCREEN") != ScreenActive.OFF
        ) or modify == "SCREEN SETTINGS":
            row = 20
            name = "SCREEN SETTINGS"
            for s in settings.screen_settings[1:]:
                self.create_label_and_value(row, 44, s, name)
                row += 2

        if (
            all and settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN
        ) or modify == "TOUCHSCREEN SETTINGS":
            row = 24
            name = "TOUCHSCREEN SETTINGS"
            for s in settings.touchscreen_settings:
                self.create_label_and_value(row, 44, s, name)
                row += 2

        if all or modify == "BPOD SETTINGS":
            row = 30
            name = "BPOD SETTINGS"
            label = self.create_and_add_label(name, row, 44, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.bpod_settings:
                self.create_label_and_value(row, 44, s, name, width=31)
                row += 2

        if all:
            self.save_button = self.create_and_add_button(
                "SAVE THE SETTINGS",
                44,
                186,
                26,
                2,
                self.save_button_clicked,
                "Apply and save the settings",
                "powderblue",
            )
            self.save_button.setDisabled(True)

            self.restore_button = self.create_and_add_button(
                "RESTORE FACTORY SETTINGS",
                48,
                186,
                26,
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
        self.save_button.setDisabled(True)
        manager.changing_settings = False

        critical_keys = [
            "USE_SOUNDCARD",
            "USE_SCREEN",
            "USE_TOUCHSCREEN",
            "SOUND_DEVICE",
            "SAMPLERATE",
            "SCREEN_SIZE_MM",
            "SCREEN_RESOLUTION",
            "BPOD_SERIAL_PORT",
            "BPOD_NET_PORT",
            "BPOD_BAUDRATE",
            "BPOD_SYNC_CHANNEL",
            "BPOD_SYNC_MODE",
            "TELEGRAM_TOKEN",
            "TELEGRAM_CHAT",
            "TELEGRAM_USERS",
        ]

        for i, line_edit in enumerate(self.line_edits):
            s = self.line_edits_settings[i]

            if s.key in critical_keys and line_edit.text() != str(settings.get(s.key)):
                self.critical_changes = True

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
                    values_int = (int(values[0]), int(values[1]))
                    settings.set(s.key, values_int)
            else:
                values = [field.text() for field in list_line]
                settings.set(s.key, values)

        for i, list_toggle in enumerate(self.list_of_toggle_buttons):
            s = self.list_of_toggle_buttons_settings[i]

            values = [field.text() for field in list_toggle]
            settings.set(s.key, values)

        val = self.sound_device_combobox.currentText()
        if val != settings.get("SOUND_DEVICE"):
            self.critical_changes = True
        settings.set("SOUND_DEVICE", val)

        cam_corridor.change = True
        cam_box.change = True

        if self.critical_changes:
            text = (
                "Some of the setting changes require a system restart to take effect."
            )
            reply = QMessageBox.question(
                self.window,
                "Restart",
                text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
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
            settings.restore_factory_settings()
            self.window.create_settings_layout()

    def create_label_and_value(
        self, row: int, column: int, s: Setting, type: Any, width: int = 30
    ) -> None:
        label = self.create_and_add_label(
            s.key, row, column, 30, 2, "black", bold=False, description=s.description
        )
        label.setProperty("type", type)

        if s.key in ("DAYTIME", "NIGHTTIME"):
            value = settings.get(s.key)
            time_edit = self.create_and_add_time_edit(
                value, row, column + width, 13, 2, self.settings_changed
            )
            self.time_edits.append(time_edit)
            self.time_edits_settings.append(s)

        elif s.key == "PROJECT_DIRECTORY":
            value = settings.get(s.key)
            path = os.path.dirname(value)
            # check if path exists
            if not os.path.exists(path):
                utils.create_directories_from_path(path)
            possible_values = [os.path.join(path, name) for name in os.listdir(path)]
            possible_values += ["NEW"]
            index = possible_values.index(value) if value in possible_values else 0
            self.project_directory_combobox = self.create_and_add_combo_box(
                s.key,
                row,
                148,
                64,
                2,
                possible_values,
                index,
                self.change_project_directory,
            )
        elif s.key == "TELEGRAM_TOKEN":
            value = str(settings.get(s.key))
            line_edit = self.create_and_add_line_edit(
                value, row, column + width, 64, 2, self.settings_changed
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
                48,
                2,
                possible_values,
                index,
                self.change_sound_device,
            )
            self.sound_device_combobox.setProperty("type", type)

        elif s.value_type in (str, int, float):
            value = str(settings.get(s.key))
            if s.key == "DATA_DIRECTORY":
                new_value = settings.get("PROJECT_DIRECTORY") + "/data"
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, 64, 2, self.settings_changed
                )
            elif s.key == "VIDEOS_DIRECTORY":
                new_value = settings.get("PROJECT_DIRECTORY") + "/data/videos"
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, 64, 2, self.settings_changed
                )
            elif s.key == "SESSIONS_DIRECTORY":
                new_value = settings.get("PROJECT_DIRECTORY") + "/data/sessions"
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, 64, 2, self.settings_changed
                )
            elif s.key == "CODE_DIRECTORY":
                new_value = settings.get("PROJECT_DIRECTORY") + "/code"
                line_edit = self.create_and_add_line_edit(
                    new_value, row, column + width, 64, 2, self.settings_changed
                )
            elif s.key == "APP_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, 64, 2, self.settings_changed
                )
            else:
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width, 13, 2, self.settings_changed
                )
            if s.key in (
                "BPOD_TARGET_FIRMWARE",
                "APP_DIRECTORY",
                "DATA_DIRECTORY",
                "VIDEOS_DIRECTORY",
                "SESSIONS_DIRECTORY",
                "CODE_DIRECTORY",
            ):
                line_edit.setReadOnly(True)
                line_edit.setDisabled(True)
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)
        elif s.key == "TELEGRAM_USERS":
            values = settings.get(s.key)
            line_edits = []
            for i, v in enumerate(values):
                value = str(v)
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width + 13 * i, 13, 2, self.settings_changed
                )
                line_edit.setProperty("type", type)
                line_edits.append(line_edit)
            self.list_of_line_edits.append(line_edits)
            self.list_of_line_edits_settings.append(s)
        elif s.value_type == list[int]:
            values = settings.get(s.key)
            line_edits = []
            for i, v in enumerate(values):
                value = str(v)
                line_edit = self.create_and_add_line_edit(
                    value, row, column + width + 8 * i, 8, 2, self.settings_changed
                )
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
                    column + width + 6 * i,
                    6,
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
            toggle_button = self.create_and_add_toggle_button(
                s.key,
                row,
                column + width,
                13,
                2,
                possible_values,
                index,
                self.toggle_button_changed,
                s.description,
            )

            toggle_button.setProperty("type", type)
            self.toggle_buttons.append(toggle_button)
            self.toggle_buttons_settings.append(s)

    def change_sound_device(self, value: str, key: str) -> None:
        self.settings_changed(value, key)

    def toggle_button_changed(self, value: str, key: str) -> None:
        modify = ""
        if value == "OFF" and key == "USE_SOUNDCARD":
            self.delete_optional_widgets("SOUND SETTINGS")
        elif value == "ON":
            modify = "SOUND SETTINGS"
        elif value == "OFF":
            self.delete_optional_widgets("SCREEN SETTINGS")
            self.delete_optional_widgets("TOUCHSCREEN SETTINGS")
        elif value == "SCREEN":
            modify = "SCREEN SETTINGS"
        elif value == "TOUCHSCREEN":
            modify = "TOUCHSCREEN SETTINGS"

        self.settings_changed(value, key)
        if modify != "":
            self.draw(all=False, modify=modify)

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
