from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from PyQt5.QtWidgets import QMessageBox

from village.app.data import data
from village.app.dev import dev
from village.app.settings import Setting, settings
from village.app.utils import utils
from village.classes.enums import Active, ControlDevice, ScreenActive
from village.gui.layout import Layout, LineEdit, PushButton, ToggleButton

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class SettingsLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.apply_button = PushButton("", "black", self.apply_button_clicked, "")
        self.restore_button = PushButton("", "black", self.restore_button_clicked, "")
        self.draw(all=True, modify="")

    def draw(self, all: bool, modify) -> None:
        self.settings_button.setDisabled(True)

        if all:
            self.line_edits: list[LineEdit] = []
            self.line_edits_settings: list[Setting] = []

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
                self.create_label_and_value(row, 0, s, name)
                row += 2

            row += 4
            name = "CORRIDOR SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.corridor_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2

        if (
            all and settings.get("USE_SOUNDCARD") == Active.ON
        ) or modify == "SOUND SETTINGS":
            row = 36
            name = "SOUND SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.sound_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2

        if all:
            row = 6
            name = "ALARM SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.alarm_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2

            row += 4
            name = "DIRECTORY SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.directory_settings:
                if s.key == "PROJECT_DIRECTORY":
                    self.create_label_and_value(row, 50, s, name)
                    row += 2
                    # create a button to open the directory
                    self.create_and_add_button(
                        "Create new project",
                        row,
                        50 + 35,
                        25,
                        2,
                        self.create_project_directory,
                        "Open the project directory",
                        "powderblue",
                    )
                else:
                    self.create_label_and_value(row, 50, s, name)
                row += 2

        if (
            all and settings.get("USE_SCREEN") == ScreenActive.TOUCHSCREEN
        ) or modify == "TOUCHSCREEN SETTINGS":
            row = 34
            name = "TOUCHSCREEN SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.touchscreen_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2
        elif (
            all and settings.get("USE_SCREEN") == ScreenActive.SCREEN
        ) or modify == "SCREEN SETTINGS":
            row = 34
            name = "SCREEN SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.screen_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2

        if all:
            row = 6
            name = "TELEGRAM SETTINGS"
            label = self.create_and_add_label(name, row, 118, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.telegram_settings:
                self.create_label_and_value(row, 118, s, name)
                row += 2

        if (
            all and settings.get("CONTROL_DEVICE") == ControlDevice.BPOD
        ) or modify == "BPOD SETTINGS":
            row = 18
            name = "BPOD SETTINGS"
            label = self.create_and_add_label(name, row, 118, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.bpod_settings:
                self.create_label_and_value(row, 118, s, name)
                row += 2
        elif (
            all and settings.get("CONTROL_DEVICE") == ControlDevice.HARP
        ) or modify == "HARP SETTINGS":
            row = 18
            name = "HARP SETTINGS"
            label = self.create_and_add_label(name, row, 118, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.harp_settings:
                self.create_label_and_value(row, 118, s, name)
                row += 2

        if all:
            self.apply_button = self.create_and_add_button(
                "Apply changes",
                44,
                187,
                25,
                2,
                self.apply_button_clicked,
                "Apply and save the settings",
                "powderblue",
            )
            self.apply_button.setDisabled(True)

            self.restore_button = self.create_and_add_button(
                "Restore factory settings",
                48,
                187,
                25,
                2,
                self.restore_button_clicked,
                "Restore the factory settings" "mistyrose",
            )
            self.restore_button.clicked.connect(self.restore_button_clicked)

    def change_layout(self) -> bool:
        if self.apply_button.isEnabled():

            reply = QMessageBox.question(
                self.window,
                "Save changes",
                "Do you want to save the changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.apply_button.setDisabled(True)
                self.apply_button_clicked()
                return True
            elif reply == QMessageBox.Discard:
                self.apply_button.setDisabled(True)
                return True
            else:
                return False
        else:
            return True

    def settings_changed(self, value: str, key="") -> None:
        self.apply_button.setEnabled(True)

    def apply_button_clicked(self) -> None:
        self.apply_button.setDisabled(True)

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

        dev.cam_corridor.change = True
        dev.cam_box.change = True

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
        self, row: int, column: int, s: Setting, type: Any
    ) -> None:
        label = self.create_and_add_label(
            s.key, row, column, 30, 2, "black", bold=False, description=s.description
        )
        label.setProperty("type", type)

        if s.key == "TOKEN":
            value = str(settings.get(s.key))
            line_edit = self.create_and_add_line_edit(
                value, row, column + 30, 64, 2, self.settings_changed
            )
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)
        elif s.value_type in (str, int, float):
            value = str(settings.get(s.key))
            if s.key.endswith("DIRECTORY"):
                width = 36
            else:
                width = 16
            line_edit = self.create_and_add_line_edit(
                value, row, column + 30, width, 2, self.settings_changed
            )
            if s.key in (
                "BPOD_TARGET_FIRMWARE",
                "APP_DIRECTORY",
                "DATA_DIRECTORY",
                "VIDEOS_DIRECTORY",
                "SESSIONS_DIRECTORY",
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
                    value, row, column + 30 + 13 * i, 13, 2, self.settings_changed
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
                    value, row, column + 30 + 8 * i, 8, 2, self.settings_changed
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
                    column + 30 + 8 * i,
                    8,
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
                column + 30,
                16,
                2,
                possible_values,
                index,
                self.toggle_button_changed,
                s.description,
            )

            toggle_button.setProperty("type", type)
            self.toggle_buttons.append(toggle_button)
            self.toggle_buttons_settings.append(s)

    def toggle_button_changed(self, value: str, key: str) -> None:
        modify = ""
        if value == "OFF" and key == "USE_SOUNDCARD":
            self.delete_optional_widgets("SOUND SETTINGS")
        elif value == "OFF":
            self.delete_optional_widgets("SCREEN SETTINGS")
            self.delete_optional_widgets("TOUCHSCREEN SETTINGS")
        elif value == "ON":
            modify = "SOUND SETTINGS"
        elif value == "SCREEN":
            self.delete_optional_widgets("TOUCHSCREEN SETTINGS")
            modify = "SCREEN SETTINGS"
        elif value == "TOUCHSCREEN":
            self.delete_optional_widgets("SCREEN SETTINGS")
            modify = "TOUCHSCREEN SETTINGS"
        elif value == "BPOD":
            self.delete_optional_widgets("HARP SETTINGS")
            modify = "BPOD SETTINGS"
        elif value == "HARP":
            self.delete_optional_widgets("BPOD SETTINGS")
            modify = "HARP SETTINGS"

        self.settings_changed(value, key)
        if modify != "":
            self.draw(all=False, modify=modify)

    def create_project_directory(self) -> None:
        # TODO: log the event in the previous project ?

        # define the rest of the directories
        for s in self.line_edits_settings:
            if s.key == "PROJECT_DIRECTORY":
                new_project_directory = self.line_edits[self.line_edits_settings.index(s)].text()
                print(new_project_directory)
                break
        
        # generate the new directory settings
        directory_settings = utils.generate_directory_paths(new_project_directory)
        
        # update the text in the gui
        for i, s in enumerate(self.line_edits_settings):
            if s.key.endswith("_DIRECTORY"):
                # find this setting in the new directory settings
                for new_s in directory_settings:
                    if new_s.key == s.key:
                        self.line_edits[i].setText(new_s.value)
                        break        
                
        self.apply_button_clicked()
        data.create_directories()
        # TODO: make also a dummy repo for the tasks
        # TODO: log the event in the new project