from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, List

from PyQt5.QtWidgets import QMessageBox

from village.settings import Setting, settings
from village.window.layout import Layout

if TYPE_CHECKING:
    from village.window.gui_window import GuiWindow


class SettingsLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw(all=True, modify="")

    def draw(self, all: bool, modify) -> None:
        self.disable(self.settings_button)

        if all:
            self.labels_and_values: List = []

            row = 6
            name = "MAIN SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.main_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2

            row += 2
            name = "DURATION SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.duration_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2

        if (
            all and settings.get("USE_SOUNDCARD") == "Yes"
        ) or modify == "SOUND SETTINGS":
            row = 28
            name = "SOUND SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.sound_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2

        if (
            all and settings.get("USE_SCREEN") == "Touchscreen"
        ) or modify == "TOUCHSCREEN SETTINGS":
            row = 34
            name = "TOUCHSCREEN SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.touchscreen_settings:
                self.create_label_and_value(row, 0, s, name)
                row += 2
        elif (
            all and settings.get("USE_SCREEN") == "Screen"
        ) or modify == "SCREEN SETTINGS":
            row = 34
            name = "SCREEN SETTINGS"
            label = self.create_and_add_label(name, row, 0, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.screen_settings:
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

            row += 2
            name = "TELEGRAM SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.telegram_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2

        if (
            all and settings.get("CONTROL_DEVICE") == "Bpod"
        ) or modify == "BPOD SETTINGS":
            row = 28
            name = "BPOD SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.bpod_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2
        elif (
            all and settings.get("CONTROL_DEVICE") == "Harp"
        ) or modify == "HARP SETTINGS":
            row = 28
            name = "HARP SETTINGS"
            label = self.create_and_add_label(name, row, 50, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.harp_settings:
                self.create_label_and_value(row, 50, s, name)
                row += 2

        if all:
            row = 6
            name = "DIRECTORY SETTINGS"
            label = self.create_and_add_label(name, row, 149, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.directory_settings:
                self.create_label_and_value(row, 149, s, name)
                row += 2

            row += 2
            name = "ADVANCED SETTINGS"
            label = self.create_and_add_label(name, row, 149, 30, 2, "black")
            label.setProperty("type", name)
            row += 2
            for s in settings.advanced_settings:
                self.create_label_and_value(row, 149, s, name)
                row += 2

        row = 30
        if (
            all and settings.get("CONTROL_DEVICE") == "Bpod"
        ) or modify == "BPOD SETTINGS":
            for s in settings.bpod_advanced_settings:
                self.create_label_and_value(row, 149, s, "BPOD SETTINGS")
                row += 2
        elif (
            all and settings.get("CONTROL_DEVICE") == "Harp"
        ) or modify == "HARP SETTINGS":
            for s in settings.harp_advanced_settings:
                self.create_label_and_value(row, 149, s, "HARP SETTINGS")
                row += 2

        if all:
            self.apply_button = self.create_and_add_button(
                "Apply changes", 44, 192, 20, 2, "lightgreen", self.apply_button_clicked
            )
            self.apply_button.setDisabled(True)

            self.restore_button = self.create_and_add_button(
                "Restore factory settings",
                48,
                192,
                20,
                2,
                "lightcoral",
                self.restore_button_clicked,
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

    def settings_changed(self) -> None:
        self.apply_button.setEnabled(True)

    def apply_button_clicked(self) -> None:
        self.apply_button.setDisabled(True)
        for val in self.labels_and_values:
            row = val[0]
            s = val[1]

            if s.type == str:
                value = row.text()
                settings.set(s.name, value)
                row.setText(value)
            elif s.type == float:
                with suppress(BaseException):
                    value = float(row.text())
                    settings.set(s.name, value)

            elif s.type == int:
                with suppress(BaseException):
                    value = round(float(row.text()))
                    settings.set(s.name, value)

            elif s.type == list:
                try:
                    values = [field.currentText() for field in row]
                    settings.set(s.name, values)
                except:  # noqa: E722
                    values = [field.text() for field in row]
                    settings.set(s.name, values)
            elif s.type == tuple:
                values = [field.text() for field in row]
                with suppress(BaseException):
                    values_tuple = (int(values[0]), int(values[1]))
                    settings.set(s.name, values_tuple)

            else:
                value = row.currentText()
                settings.set(s.name, value)

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

    def create_label_and_value(self, row: int, column: int, s: Setting, type: Any):
        label = self.create_and_add_label(
            s.name, row, column, 30, 2, "black", bold=False, description=s.description
        )
        label.setProperty("type", type)

        if s.name == "TOKEN":
            value = str(settings.get(s.name))
            line_edit = self.create_and_add_line_edit(
                value, row, column + 30, 64, 2, self.settings_changed
            )
            line_edit.setProperty("type", type)
            self.labels_and_values.append((line_edit, s))
        elif s.name.endswith("DIRECTORY") or s.name == "BPOD_TARGET_FIRMWARE":
            value = str(settings.get(s.name))
            line_edit = self.create_and_add_line_edit(
                value, row, column + 30, 32, 2, self.settings_changed
            )
            line_edit.setReadOnly(True)
            line_edit.setDisabled(True)
            line_edit.setProperty("type", type)
            self.labels_and_values.append((line_edit, s))
        elif s.type in (str, int, float):
            value = str(settings.get(s.name))
            line_edit = self.create_and_add_line_edit(
                value, row, column + 30, 16, 2, self.settings_changed
            )
            line_edit.setProperty("type", type)
            self.labels_and_values.append((line_edit, s))
        elif s.name == "TELEGRAM_USERS":
            values = settings.get(s.name)
            list_of_line_edits = []
            for i, v in enumerate(values):
                value = str(v)
                line_edit = self.create_and_add_line_edit(
                    value, row, column + 30 + 13 * i, 13, 2, self.settings_changed
                )
                line_edit.setProperty("type", type)
                list_of_line_edits.append(line_edit)
            self.labels_and_values.append((list_of_line_edits, s))

        elif s.type == list:
            values = settings.get(s.name)
            list_of_combo_boxes = []
            for i, v in enumerate(values):
                value = str(v)
                possible_values = ["No", "Yes"]
                combo_box = self.create_and_add_combo_box(
                    value,
                    possible_values,
                    row,
                    column + 30 + 8 * i,
                    8,
                    2,
                    self.settings_changed,
                )
                combo_box.setProperty("type", type)
                list_of_combo_boxes.append(combo_box)
            self.labels_and_values.append((list_of_combo_boxes, s))
        elif s.type == tuple:
            values = settings.get(s.name)
            list_of_line_edits = []
            for i, v in enumerate(values):
                value = str(v)
                line_edit = self.create_and_add_line_edit(
                    value, row, column + 30 + 8 * i, 8, 2, self.settings_changed
                )
                line_edit.setProperty("type", type)
                list_of_line_edits.append(line_edit)
            self.labels_and_values.append((list_of_line_edits, s))
        else:
            my_enum = s.type
            value = settings.get(s.name)
            possible_values = [e.value for e in my_enum]

            combo_box = self.create_and_add_combo_box(
                value,
                possible_values,
                row,
                column + 30,
                16,
                2,
                self.combo_changed,
            )
            combo_box.setProperty("type", type)
            self.labels_and_values.append((combo_box, s))

    def combo_changed(self, value: Any) -> None:
        modify = ""
        if value == "No":
            self.delete_optional_widgets("SOUND SETTINGS")
        elif value == "No Screen":
            self.delete_optional_widgets("SCREEN SETTINGS")
            self.delete_optional_widgets("TOUCHSCREEN SETTINGS")
        elif value == "Yes":
            modify = "SOUND SETTINGS"
        elif value == "Screen":
            self.delete_optional_widgets("TOUCHSCREEN SETTINGS")
            modify = "SCREEN SETTINGS"
        elif value == "Touchscreen":
            self.delete_optional_widgets("SCREEN SETTINGS")
            modify = "TOUCHSCREEN SETTINGS"
        elif value == "Bpod":
            self.delete_optional_widgets("HARP SETTINGS")
            modify = "BPOD SETTINGS"
        elif value == "Harp":
            self.delete_optional_widgets("BPOD SETTINGS")
            modify = "HARP SETTINGS"

        self.settings_changed()
        if modify != "":
            self.draw(all=False, modify=modify)
