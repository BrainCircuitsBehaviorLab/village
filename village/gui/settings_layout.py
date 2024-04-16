from PyQt5.QtWidgets import QComboBox, QLabel, QLineEdit, QMessageBox, QPushButton

from village.gui.layout import Layout
from village.settings import settings


class ComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QComboBox {font-size: 10px}")

    def wheelEvent(self, event):
        event.ignore()

    def set_color(self):
        if self.currentText() in ["No", "No Screen"]:
            self.setStyleSheet("QComboBox {background-color: lightcoral}")
        else:
            self.setStyleSheet("QComboBox {background-color: lightgreen}")


class SettingsLayout(Layout):
    def __init__(self, window):
        super().__init__(window)

        self.draw(all=True, modify="")

    def draw(self, all, modify):
        self.first_column = 0
        self.second_column = 50
        self.third_column = 149

        self.first_row = 4
        self.first_optional_row = 26
        self.second_optional_row = 32
        self.bottom_row = 52
        self.advanced_optional_row = 26
        self.control_row = 26

        self.super_short_widget_width = 8
        self.short_widget_width = 13
        self.medium_widget_width = 16
        self.large_widget_width = 32
        self.super_large_widget_width = 64

        self.settings_button.setDisabled(True)
        self.settings_button.setStyleSheet("QPushButton {background-color: lightblue}")

        if all:
            self.labels_and_values = []
            row = self.first_row
            label = QLabel("Main Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Main")
            self.addWidget(
                label, row, self.first_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.main_settings:
                self.create_label_and_value(row, self.first_column, s, "Main")
                row += self.widget_height

            row += self.widget_height
            label = QLabel("Duration Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Duration")
            self.addWidget(
                label, row, self.first_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.duration_settings:
                self.create_label_and_value(row, self.first_column, s, "Duration")
                row += self.widget_height

        if (all and settings.get("USE_SOUNDCARD") == "Yes") or modify == "Sound":
            row = self.first_optional_row
            label = QLabel("Sound Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Sound")
            self.addWidget(
                label, row, self.first_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.sound_settings:
                self.create_label_and_value(row, self.first_column, s, "Sound")
                row += self.widget_height

        if (
            all and settings.get("USE_SCREEN") == "Touchscreen"
        ) or modify == "Touchscreen":
            row = self.second_optional_row
            label = QLabel("Touchscreen Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Touchscreen")
            self.addWidget(
                label, row, self.first_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.touchscreen_settings:
                self.create_label_and_value(row, self.first_column, s, "Touchscreen")
                row += self.widget_height
        elif (all and settings.get("USE_SCREEN") == "Screen") or modify == "Screen":
            row = self.second_optional_row
            label = QLabel("Screen Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Screen")
            self.addWidget(
                label, row, self.first_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.screen_settings:
                self.create_label_and_value(row, self.first_column, s, "Screen")
                row += self.widget_height

        if all:
            row = self.first_row
            label = QLabel("Alarm Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Alarm")
            self.addWidget(
                label, row, self.second_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.alarm_settings:
                self.create_label_and_value(row, self.second_column, s, "Alarm")
                row += self.widget_height

            row += self.widget_height
            label = QLabel("Telegram Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Telegram")
            self.addWidget(
                label, row, self.second_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.telegram_settings:
                self.create_label_and_value(row, self.second_column, s, "Telegram")
                row += self.widget_height

        if (all and settings.get("CONTROL_DEVICE") == "Bpod") or modify == "Bpod":
            row = self.control_row
            label = QLabel("Bpod Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Bpod")
            self.addWidget(
                label, row, self.second_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.bpod_settings:
                self.create_label_and_value(row, self.second_column, s, "Bpod")
                row += self.widget_height
        elif (all and settings.get("CONTROL_DEVICE") == "Harp") or modify == "Harp":
            row = self.control_row
            label = QLabel("Harp Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Harp")
            self.addWidget(
                label, row, self.second_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.harp_settings:
                self.create_label_and_value(row, self.second_column, s, "Harp")
                row += self.widget_height

        if all:
            row = self.first_row
            label = QLabel("Directory Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Directory")
            self.addWidget(
                label, row, self.third_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.directory_settings:
                self.create_label_and_value(row, self.third_column, s, "Directory")
                row += self.widget_height

            row += self.widget_height
            label = QLabel("Advanced Settings")
            label.setStyleSheet("font-weight: bold")
            label.setProperty("type", "Advanced")
            self.addWidget(
                label, row, self.third_column, self.widget_height, self.label_width
            )
            row += self.widget_height
            for s in settings.advanced_settings:
                self.create_label_and_value(row, self.third_column, s, "Advanced")
                row += self.widget_height

        row = self.advanced_optional_row
        if (all and settings.get("CONTROL_DEVICE") == "Bpod") or modify == "Bpod":
            for s in settings.bpod_advanced_settings:
                self.create_label_and_value(row, self.third_column, s, "Bpod")
                row += self.widget_height
        elif (all and settings.get("CONTROL_DEVICE") == "Harp") or modify == "Harp":
            for s in settings.harp_advanced_settings:
                self.create_label_and_value(row, self.third_column, s, "Harp")
                row += self.widget_height

        if all:
            self.apply_button = QPushButton("Apply changes")
            self.apply_button.clicked.connect(self.apply_button_clicked)
            self.apply_button.setDisabled(True)

            self.addWidget(
                self.apply_button,
                self.bottom_row - 4 * self.widget_height,
                self.last_menu_button,
                self.widget_height,
                self.button_width,
            )

            self.restore_button = QPushButton("Restore factory settings")
            self.restore_button.setStyleSheet(
                "QPushButton {background-color: lightcoral; font-size: 10px}"
            )

            self.restore_button.clicked.connect(self.restore_button_clicked)

            self.addWidget(
                self.restore_button,
                self.bottom_row - 2 * self.widget_height,
                self.last_menu_button,
                self.widget_height,
                self.button_width,
            )

    def change_layout(self):
        if self.apply_button.isEnabled():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText("Do you want to save the changes?")
            msg.setWindowTitle("Save changes")
            msg.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            msg.setDefaultButton(QMessageBox.Save)
            ret = msg.exec_()
            if ret == QMessageBox.Save:
                self.apply_button.setDisabled(True)
                self.apply_button_clicked()
                return True
            elif ret == QMessageBox.Discard:
                self.apply_button.setDisabled(True)
                return True
            elif ret == QMessageBox.Cancel:
                return False
        else:
            return True

    def settings_changed(self):
        self.apply_button.setEnabled(True)

    def apply_button_clicked(self):
        self.apply_button.setDisabled(True)
        for val in self.labels_and_values:
            row = val[0]
            s = val[1]

            if s.type == str:
                value = row.text()
                settings.set(s.name, value)
                row.setText(value)
            elif s.type == float:
                try:
                    value = float(row.text())
                    settings.set(s.name, value)
                except:  # noqa: E722
                    pass

            elif s.type == int:
                try:
                    value = round(float(row.text()))
                    settings.set(s.name, value)
                except:  # noqa: E722
                    pass
            elif s.type == list:
                try:
                    values = [field.currentText() for field in row]
                    settings.set(s.name, values)
                except:  # noqa: E722
                    values = [field.text() for field in row]
                    settings.set(s.name, values)
            elif s.type == tuple:
                values = [field.text() for field in row]
                try:
                    values = (int(values[0]), int(values[1]))
                    settings.set(s.name, values)
                except:  # noqa: E722
                    pass
            else:
                value = row.currentText()
                settings.set(s.name, value)

    def restore_button_clicked(self):
        reply = QMessageBox.question(
            self.window,
            "Restore factory settings",
            "Are you sure you want to restore to the factory settings?",
            QMessageBox.Yes,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            settings.restore_factory_settings()
            self.window.create_settings_layout()

    def create_label_and_value(self, row, column, s, type):
        label = QLabel(s.name)
        label.setStyleSheet("QToolTip {background-color: white; color: black}")
        label.setToolTip(s.description)
        label.setFixedWidth(self.label_width * self.column_width)
        label.setProperty("type", type)
        self.addWidget(label, row, column, self.widget_height, self.label_width)

        if s.name == "TOKEN":
            line_edit = QLineEdit()
            line_edit.setText(str(settings.get(s.name)))
            line_edit.textChanged.connect(self.settings_changed)
            line_edit.setFixedWidth(self.super_large_widget_width * self.column_width)
            line_edit.setProperty("type", type)
            self.addWidget(
                line_edit,
                row,
                column + self.label_width,
                self.widget_height,
                self.super_large_widget_width,
            )
            self.labels_and_values.append((line_edit, s))
        elif s.name.endswith("DIRECTORY") or s.name == "BPOD_TARGET_FIRMWARE":
            line_edit = QLineEdit()
            line_edit.setText(str(settings.get(s.name)))
            line_edit.textChanged.connect(self.settings_changed)
            line_edit.setFixedWidth(self.large_widget_width * self.column_width)
            line_edit.setReadOnly(True)
            line_edit.setDisabled(True)
            line_edit.setProperty("type", type)
            self.addWidget(
                line_edit,
                row,
                column + self.label_width,
                self.widget_height,
                self.large_widget_width,
            )
            self.labels_and_values.append((line_edit, s))
        elif s.type in [str, int, float]:
            line_edit = QLineEdit()
            line_edit.setText(str(settings.get(s.name)))
            line_edit.textChanged.connect(self.settings_changed)
            line_edit.setFixedWidth(self.medium_widget_width * self.column_width)
            line_edit.setProperty("type", type)
            self.addWidget(
                line_edit,
                row,
                column + self.label_width,
                self.widget_height,
                self.medium_widget_width,
            )
            self.labels_and_values.append((line_edit, s))
        elif s.name == "TELEGRAM_USERS":
            values = settings.get(s.name)
            list_of_line_edits = []
            for i, v in enumerate(values):
                line_edit = QLineEdit()
                line_edit.setText(str(v))
                line_edit.textChanged.connect(self.settings_changed)
                line_edit.setFixedWidth(self.short_widget_width * self.column_width)
                line_edit.setProperty("type", type)
                self.addWidget(
                    line_edit,
                    row,
                    column + self.label_width + self.short_widget_width * i,
                    self.widget_height,
                    self.short_widget_width,
                )
                list_of_line_edits.append(line_edit)
            self.labels_and_values.append((list_of_line_edits, s))

        elif s.type == list:
            values = settings.get(s.name)
            list_of_combos = []
            for i, v in enumerate(values):
                possible_values = ["No", "Yes"]
                combo_box = ComboBox()
                combo_box.addItems(possible_values)
                combo_box.setCurrentText(v)
                combo_box.currentTextChanged.connect(self.combo_changed_list)
                combo_box.setFixedWidth(
                    self.super_short_widget_width * self.column_width
                )
                combo_box.setProperty("type", type)
                combo_box.set_color()
                self.addWidget(
                    combo_box,
                    row,
                    column + self.label_width + self.super_short_widget_width * i,
                    self.widget_height,
                    self.super_short_widget_width,
                )

                list_of_combos.append(combo_box)
            self.labels_and_values.append((list_of_combos, s))
        elif s.type == tuple:
            values = settings.get(s.name)
            list_of_line_edits = []
            for i, v in enumerate(values):
                line_edit = QLineEdit()
                line_edit.setText(str(v))
                line_edit.textChanged.connect(self.settings_changed)
                line_edit.setFixedWidth(
                    self.super_short_widget_width * self.column_width
                )
                line_edit.setProperty("type", type)
                self.addWidget(
                    line_edit,
                    row,
                    column + self.label_width + self.super_short_widget_width * i,
                    self.widget_height,
                    self.super_short_widget_width,
                )
                list_of_line_edits.append(line_edit)
            self.labels_and_values.append((list_of_line_edits, s))
        else:
            my_enum = s.type
            possible_values_enum = [e.value for e in my_enum]
            combo_box = ComboBox()
            combo_box.addItems(possible_values_enum)
            combo_box.setCurrentText(settings.get(s.name))
            combo_box.currentTextChanged.connect(self.combo_changed)
            combo_box.setFixedWidth(self.medium_widget_width * self.column_width)
            combo_box.setProperty("type", type)
            combo_box.set_color()
            self.addWidget(
                combo_box,
                row,
                column + self.label_width,
                self.widget_height,
                self.medium_widget_width,
            )
            self.labels_and_values.append((combo_box, s))

    def combo_changed_list(self):
        for item in self.labels_and_values:
            if item[1].type == list and not item[1].name == "TELEGRAM_USERS":
                for combo_box in item[0]:
                    combo_box.set_color()
            if item[1].type not in [str, int, float, list, tuple]:
                item[0].set_color()
        self.settings_changed()

    def combo_changed(self, value):
        modify = ""
        for item in self.labels_and_values:
            if item[1].type == list and not item[1].name == "TELEGRAM_USERS":
                for combo_box in item[0]:
                    combo_box.set_color()
            if item[1].type not in [str, int, float, list, tuple]:
                item[0].set_color()
        if value == "No":
            self.delete_optional_widgets("Sound")
        elif value == "No Screen":
            self.delete_optional_widgets("Screen")
            self.delete_optional_widgets("Touchscreen")
        elif value == "Yes":
            modify = "Sound"
        elif value == "Screen":
            self.delete_optional_widgets("Touchscreen")
            modify = "Screen"
        elif value == "Touchscreen":
            self.delete_optional_widgets("Screen")
            modify = "Touchscreen"
        elif value == "Bpod":
            self.delete_optional_widgets("Harp")
            modify = "Bpod"
        elif value == "Harp":
            self.delete_optional_widgets("Bpod")
            modify = "Harp"

        self.settings_changed()
        if modify != "":
            self.draw(all=False, modify=modify)
