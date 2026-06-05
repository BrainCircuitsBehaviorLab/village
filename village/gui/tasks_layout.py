from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Type, Union

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from village.classes.enums import State
from village.classes.subject import Subject
from village.custom_classes.task import Task
from village.gui.layout import Layout
from village.manager import manager
from village.scripts.log import log
from village.settings import settings

if TYPE_CHECKING:
    from village.custom_classes.task import Task
    from village.gui.gui_window import GuiWindow
    from village.gui.layout import LineEdit


# ── Left menu panel ────────────────────────────────────────────────────────────
MENU_COL = 1
MENU_WIDTH = 22

# ── Right content panel ────────────────────────────────────────────────────────
C_COL = 25  # content start column
C_ROW = 7  # content start row

DESC_COLS = 62  # description area width in grid columns
SETTINGS_COL = C_COL + DESC_COLS + 2  # = 89

MENU_ITEM_TRAINING = "TEST TRAINING PROTOCOL"


class ExtraLayout(Layout):
    """Layout helper for task settings in scrollable areas."""

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)


class TasksLayout(Layout):
    """Layout for selecting and configuring tasks."""

    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self._highlight_nav_button(self.tasks_button)
        self.window = window
        self.selected = ""
        self.testing_training = False
        self.subject_index = 0
        self.draw()

    def draw(self) -> None:
        self.line_edits: dict[str, LineEdit] = {}
        self.tasks_button.setDisabled(True)

        # Centered between menu end (col 25) and right panel (col 89): (89-25-20)//2=22
        _btn_col = C_COL + (SETTINGS_COL - C_COL - 20) // 2  # = 47
        self.run_task_button = self.create_and_add_button(
            "RUN TASK",
            C_ROW,
            _btn_col,
            20,
            2,
            self.run_task_button_clicked,
            "Run the selected task",
            "powderblue",
        )

        self._draw_menu()
        self._draw_content_area()
        self.check_buttons()

    # ── Left menu ──────────────────────────────────────────────────────────────

    def _draw_menu(self) -> None:
        menu_font = QFont("DejaVu Sans Condensed", 9)
        menu_font.setBold(True)
        self.menu_list = QListWidget()
        self.menu_list.setFont(menu_font)
        self.menu_list.setStyleSheet(
            "QListWidget { background: #e8e8e8; border: none; outline: none; }"
            "QListWidget::item {"
            " background: #d0d0d0; color: black;"
            " padding: 6px 8px; margin-bottom: 2px;"
            " border: 1px solid #aaaaaa;"
            " border-radius: 3px; }"
            "QListWidget::item:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QListWidget::item:hover { background: #b0c4de; border-color: #b0c4de; }"
            "QToolTip { background-color: white; color: black;"
            " font-size: 10pt; padding: 4px }"
        )
        self.menu_list.setSpacing(1)

        training_item = QListWidgetItem(MENU_ITEM_TRAINING)
        training_item.setToolTip(
            "Test the training protocol to check that it returns the correct values"
        )
        self.menu_list.addItem(training_item)

        for key in manager.tasks:
            item = QListWidgetItem(key)
            item.setToolTip(f"Select the task {key}")
            self.menu_list.addItem(item)

        self.menu_list.currentRowChanged.connect(self._on_menu_changed)
        self.addWidget(self.menu_list, C_ROW, MENU_COL, 46, MENU_WIDTH + 2)

    def _menu_items(self) -> list[str]:
        return [MENU_ITEM_TRAINING] + list(manager.tasks.keys())

    def _on_menu_changed(self, row: int) -> None:
        items = self._menu_items()
        if row < 0 or row >= len(items):
            return
        name = items[row]
        if name == MENU_ITEM_TRAINING:
            self.training_button_clicked()
        else:
            cls = manager.tasks[name]
            self.select_task(cls, name)

    # ── Content area ───────────────────────────────────────────────────────────

    def _draw_content_area(self) -> None:
        self.central_layout = QVBoxLayout()
        self.addLayout(self.central_layout, C_ROW + 3, C_COL, 37, DESC_COLS)

        self.central_scroll = QScrollArea()
        self.central_scroll.setStyleSheet("QScrollArea { border: 0px }")
        self.central_scroll.setWidgetResizable(True)
        self.central_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.central_sub_widget = QWidget()
        self.central_sub_layout = ExtraLayout(self.window, 36, 59)
        self.central_sub_widget.setLayout(self.central_sub_layout)
        self.central_scroll.setWidget(self.central_sub_widget)
        self.central_layout.addWidget(self.central_scroll)

        self.right_layout = QVBoxLayout()
        self.addLayout(self.right_layout, C_ROW, SETTINGS_COL, 40, 109)

        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("QTabWidget { border: 0px }")
        self.right_layout.addWidget(self.right_tabs)

        self.restart_tab_panel()

    def create_tab_with_scroll_area(self, tab_name: str, layout: ExtraLayout) -> None:
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("QScrollArea { border: 0px }")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        widget = QWidget()
        scroll_area.setWidget(widget)
        tab_layout = QVBoxLayout(widget)
        widget.setLayout(tab_layout)
        tab_layout.addLayout(layout)
        tab.setLayout(QVBoxLayout())
        tab.layout().addWidget(scroll_area)
        self.right_tabs.addTab(tab, tab_name)

    def restart_tab_panel(self) -> None:
        self.right_tabs.clear()
        self.right_layout_general = ExtraLayout(self.window, 30, 79)
        self.create_tab_with_scroll_area("General", self.right_layout_general)

    # ── Button state management ────────────────────────────────────────────────

    def check_buttons(self) -> None:
        if manager.state.task_is_running():
            self.run_task_button.setEnabled(False)
            self.menu_list.setEnabled(False)
            for line_edit in self.line_edits.values():
                line_edit.setEnabled(False)
        elif self.testing_training:
            self.run_task_button.setText("TEST TRAINING")
            self.right_layout_general.delete_optional_widgets("optional2")
            self.menu_list.setEnabled(True)
            self.run_task_button.setEnabled(self.subject_index != 0)
        elif self.selected != "":
            self.run_task_button.setText("RUN TASK")
            self.run_task_button.setEnabled(True)
            self.menu_list.setEnabled(True)
            for line_edit in self.line_edits.values():
                line_edit.setEnabled(True)
        else:
            self.run_task_button.setEnabled(False)
            self.menu_list.setEnabled(True)
            for line_edit in self.line_edits.values():
                line_edit.setEnabled(True)

    # ── Task / training selection ──────────────────────────────────────────────

    def select_task(self, cls: Type, name: str) -> None:
        if issubclass(cls, Task):
            self.subject_index = 0
            self.testing_training = False
            self.selected = name
            self.central_sub_layout.delete_optional_widgets("optional")
            self.central_sub_layout.delete_optional_widgets("optional2")
            self.right_layout_general.delete_optional_widgets("optional")
            self.right_layout_general.delete_optional_widgets("optional2")
            self.check_buttons()
            manager.reset_subject_task_training()
            manager.task = cls()
            self.name_label = self.central_sub_layout.create_and_add_label(
                manager.task.name, 0, 2, 60, 2, "black"
            )
            self.name_label.setProperty("type", "optional")

            self.info_label = QLabel(manager.task.info)
            self.info_label.setStyleSheet(
                "QLabel { font-family: 'Courier New'; font-size: 8pt;"
                " font-weight: normal; color: black; }"
            )
            self.info_label.setWordWrap(True)
            self.info_label.setProperty("type", "optional")
            self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.info_scroll = QScrollArea()
            self.info_scroll.setWidget(self.info_label)
            self.info_scroll.setWidgetResizable(True)
            self.info_scroll.setProperty("type", "optional")
            col_w = self.central_sub_layout.column_width
            row_h = self.central_sub_layout.row_height
            self.info_scroll.setFixedSize(60 * col_w, 30 * row_h)
            self.central_sub_layout.addWidget(self.info_scroll, 2, 2, 30, 60)
            self.create_gui_properties(testing_training=False)

    def training_button_clicked(self) -> None:
        self.subject_index = 0
        self.testing_training = True
        self.selected = ""
        self.central_sub_layout.delete_optional_widgets("optional")
        self.central_sub_layout.delete_optional_widgets("optional2")
        self.right_layout_general.delete_optional_widgets("optional")
        self.right_layout_general.delete_optional_widgets("optional2")
        self.check_buttons()
        manager.reset_subject_task_training()
        self.create_gui_properties(testing_training=True)

    # ── GUI properties panel ───────────────────────────────────────────────────

    def create_gui_properties(self, testing_training: bool) -> None:
        self.line_edits = {}
        self.central_sub_layout.delete_optional_widgets("optional2")
        self.right_layout_general.delete_optional_widgets("optional2")
        self.restart_tab_panel()

        self.subject_label = self.right_layout_general.create_and_add_label(
            "Subject", 0, 2, 20, 2, "black"
        )
        self.subject_label.setProperty("type", "optional")

        mylist = ["None"] + manager.subjects.df["name"].tolist()
        self.possible_subjects = [
            x
            for x in mylist
            if not pd.isna(x) and not (isinstance(x, str) and x.strip() == "")
        ]
        self.subject_combo = self.right_layout_general.create_and_add_combo_box(
            "subject",
            0,
            32,
            30,
            2,
            self.possible_subjects,
            self.subject_index,
            self.select_subject,
        )
        self.subject_combo.setProperty("type", "optional")

        remove_names = [
            "next_task",
            "maximum_duration",
            "minimum_duration",
            "refractory_period",
        ]
        properties = {
            k: v
            for k, v in manager.training.get_dict().items()
            if k not in remove_names
        }

        for tab_name, properties_list in manager.training.gui_tabs.items():
            tab_layout = ExtraLayout(self.window, 30, 79)
            self.create_tab_with_scroll_area(tab_name, tab_layout)
            row = 0
            for property in properties_list:
                if property in properties:
                    self.create_label_and_value(
                        tab_layout, row, 2, property, str(properties[property])
                    )
                    row += 2
                    properties.pop(property)
                else:
                    log.error(
                        f"Tab setting {property} not found in settings, check spelling"
                    )

        row = 4
        if not testing_training:
            self.create_label_and_value(
                self.right_layout_general,
                row,
                2,
                "maximum_number_of_trials",
                str(manager.task.maximum_number_of_trials),
            )
            row += 2
            self.create_label_and_value(
                self.right_layout_general,
                row,
                2,
                "maximum_duration",
                str(manager.training.get_dict()["maximum_duration"]),
            )
            row += 4
        for i, (k, v) in enumerate(properties.items()):
            self.create_label_and_value(self.right_layout_general, row, 2, k, str(v))
            row += 2

        hide_tab = self.find_tab_by_label("Hide")
        if hide_tab:
            self.right_tabs.removeTab(self.right_tabs.indexOf(hide_tab))
        self.update_gui()

    def find_tab_by_label(self, label: str) -> Union[QWidget, None]:
        for index in range(self.right_tabs.count()):
            if self.right_tabs.tabText(index) == label:
                return self.right_tabs.widget(index)
        return None

    def select_subject(self, value: str, key: str) -> None:
        self.subject_index = self.subject_combo.currentIndex()
        current_value = ""
        if value != "None":
            manager.subject.subject_series = manager.subjects.get_last_entry(
                "name", value
            )
            if manager.subject.create_from_subject_series():
                manager.task.subject = value
            if manager.subject.subject_series is not None:
                try:
                    current_value = manager.subject.subject_series["next_settings"]
                except Exception:
                    pass
        else:
            manager.subject = Subject()
            manager.task.subject = "None"
        manager.training.load_settings_from_jsonstring(current_value)
        self.create_gui_properties(testing_training=self.testing_training)

    def run_task_button_clicked(self) -> None:
        wrong_keys = self.change_properties()
        if self.testing_training:
            if len(wrong_keys) <= 2:
                manager.task.settings = manager.training.settings
                manager.task.training = manager.training
                try:
                    subject = manager.task.subject
                    sessions_directory = settings.get("SESSIONS_DIRECTORY")
                    subject_path = str(
                        Path(sessions_directory, subject, subject + ".csv")
                    )
                    manager.task.training.df = pd.read_csv(subject_path, sep=";")
                    manager.task.training.subject = manager.task.subject
                    last_task = manager.task.training.df["task"].iloc[-1]
                    manager.task.training.last_task = last_task
                    manager.task.training.update_training_settings()
                    manager.training = manager.task.training

                    text = ""
                    manager.training.settings = manager.task.settings
                    settings_dict = manager.training.get_dict(exclude=["observations"])

                    for key, value in settings_dict.items():
                        text += f"{key}: {value}\n"
                    QMessageBox.information(self.window, "Next settings", text)

                except Exception:
                    text = log.clean_text(
                        traceback.format_exc(), "Error updating the training settings"
                    )
                    text = text.replace("  |  ", "\n")
                    QMessageBox.information(self.window, "ERROR", text)
            else:
                QMessageBox.information(
                    self.window,
                    "ERROR",
                    "The following settings are wrong:\n" + "\n".join(wrong_keys),
                )
        else:
            if len(wrong_keys) == 0:
                manager.task.settings = manager.training.settings
                manager.task.training = manager.training
                manager.state = State.LAUNCH_MANUAL
                self.monitor_button_clicked()
                self.update_gui()
            else:
                QMessageBox.information(
                    self.window,
                    "ERROR",
                    "The following settings are wrong:\n" + "\n".join(wrong_keys),
                )

    # ── Widget factory for a single setting ───────────────────────────────────

    def create_label_and_value(
        self,
        layout: Layout,
        row: int,
        column: int,
        name: str,
        value: str,
        width: int = 23,
    ) -> None:
        label = layout.create_and_add_label(
            name, row, column, width, 2, "black", bold=True
        )
        label.setProperty("type", "optional2")
        if name in manager.training.gui_tabs_restricted:
            optional_values = list(map(str, manager.training.gui_tabs_restricted[name]))
            try:
                default_index = optional_values.index(value)
            except Exception:
                try:
                    default_index = optional_values.index(str(int(float(value))))
                except Exception:
                    default_index = 0
                    text = "The value for the property " + name + " (" + value + ")"
                    text += " is not in the list of possible values "
                    text += str(optional_values)
                    log.error(text)
                    QMessageBox.information(self.window, "ERROR", text)
            line_edit = layout.create_and_add_combo_box(
                name,
                row,
                column + width,
                52,
                2,
                optional_values,
                default_index,
                self.change_combo,
            )
        else:
            line_edit = layout.create_and_add_line_edit(
                value, row, column + width, 52, 2, self.change_text
            )
        line_edit.setProperty("type", "optional2")
        self.line_edits[name] = line_edit

    def change_properties(self) -> list[str]:
        wrong_values: list[str] = []
        properties = manager.training.get_dict()
        remove_names = [
            "next_task",
            "maximum_duration",
            "minimum_duration",
            "refractory_period",
        ]
        properties = {k: v for k, v in properties.items() if k not in remove_names}
        new_dict = {}

        try:
            manager.task.maximum_number_of_trials = abs(
                int(self.line_edits["maximum_number_of_trials"].text())
            )
        except Exception:
            wrong_values.append("maximum_number_of_trials")

        try:
            new_dict["maximum_duration"] = abs(
                float(self.line_edits["maximum_duration"].text())
            )
        except Exception:
            new_dict["maximum_duration"] = manager.training.get_dict()[
                "maximum_duration"
            ]
            wrong_values.append("maximum_duration")

        for i, (k, v) in enumerate(properties.items()):
            widget = self.line_edits[k]
            if isinstance(widget, QLineEdit):
                new_dict[k] = widget.text()
            elif isinstance(widget, QComboBox):
                new_dict[k] = widget.currentText()

        wrong_keys = manager.training.load_settings_from_dict(new_dict)

        return wrong_values + wrong_keys

    def change_text(self) -> None:
        pass

    def change_combo(self, value: str, key: str) -> None:
        pass

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        self.check_buttons()
