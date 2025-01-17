from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Type

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout, QWidget

from village.classes.enums import State
from village.classes.subject import Subject
from village.classes.task import Task
from village.gui.layout import Layout
from village.manager import manager

if TYPE_CHECKING:
    from village.classes.task import Task
    from village.gui.gui_window import GuiWindow
    from village.gui.layout import LineEdit, PushButton


class ExtraLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)


class TasksLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.window = window
        self.selected = ""
        self.testing_training = False
        self.draw()

    def draw(self) -> None:
        self.line_edits: list[LineEdit] = []
        self.tasks_button.setDisabled(True)

        self.run_task_button = self.create_and_add_button(
            "RUN TASK",
            8,
            98,
            16,
            2,
            self.run_task_button_clicked,
            "Run the selected task",
            "powderblue",
        )

        self.task_buttons: list[PushButton] = []

        row = 8
        self.create_and_add_label("Training protocol", row, 4, 20, 2, "black")
        row += 2
        self.training_button = self.create_and_add_button(
            "Test the training protocol",
            row,
            4,
            30,
            2,
            self.test_training,
            "Test the training protocol to check that returns the correct values",
        )

        self.left_layout = QVBoxLayout()
        self.addLayout(self.left_layout, 14, 2, 34, 38)

        self.central_layout = QVBoxLayout()
        self.addLayout(self.central_layout, 14, 45, 34, 70)

        self.right_layout = QVBoxLayout()
        self.addLayout(self.right_layout, 13, 120, 35, 90)

        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.left_sub_widget = QWidget()

        self.central_scroll = QScrollArea()
        self.central_scroll.setWidgetResizable(True)
        self.central_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.central_sub_widget = QWidget()

        self.left_sub_layout = ExtraLayout(self.window, 30, 32)
        self.central_sub_layout = ExtraLayout(self.window, 30, 64)

        # Create a QTabWidget
        self.right_tabs = QTabWidget()
        self.right_layout.addWidget(self.right_tabs)

        # Create the General tab and its scroll area
        self.restart_tab_panel()

        row = 0
        self.left_sub_layout.create_and_add_label("Tasks", row, 0, 20, 2, "black")
        row += 2
        for key, value in manager.tasks.items():
            button = self.left_sub_layout.create_and_add_button(
                key,
                row,
                0,
                30,
                2,
                partial(self.select_task, value, key),
                "Select the task",
            )
            row += 2
            self.task_buttons.append(button)

        self.left_sub_widget.setLayout(self.left_sub_layout)
        self.left_scroll.setWidget(self.left_sub_widget)
        self.left_layout.addWidget(self.left_scroll)

        self.central_sub_widget.setLayout(self.central_sub_layout)
        self.central_scroll.setWidget(self.central_sub_widget)
        self.central_layout.addWidget(self.central_scroll)

        self.check_buttons()

    def create_tab_with_scroll_area(self, tab_name: str, layout: ExtraLayout) -> None:
        tab = QWidget()
        scroll_area = QScrollArea()
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
        self.right_layout_general = ExtraLayout(self.window, 30, 84)
        self.create_tab_with_scroll_area("General", self.right_layout_general)

    def check_buttons(self) -> None:
        if manager.state.can_stop_task():
            self.run_task_button.setEnabled(False)
            for button in self.task_buttons:
                button.setEnabled(False)
            for line_edit in self.line_edits:
                line_edit.setEnabled(False)
        elif self.testing_training:
            self.run_task_button.setText("TEST TRAINING")
            self.run_task_button.setEnabled(True)
            for button in self.task_buttons:
                button.setEnabled(True)
            for line_edit in self.line_edits:
                line_edit.setEnabled(True)
        elif self.selected != "":
            self.run_task_button.setText("RUN TASK")
            self.run_task_button.setEnabled(True)
            for button in self.task_buttons:
                if button.text() == self.selected:
                    button.setEnabled(False)
                else:
                    button.setEnabled(True)
            for line_edit in self.line_edits:
                line_edit.setEnabled(True)
        else:
            self.run_task_button.setEnabled(False)
            for button in self.task_buttons:
                button.setEnabled(True)
            for line_edit in self.line_edits:
                line_edit.setEnabled(True)

    def select_task(self, cls: Type, name: str) -> None:
        if issubclass(cls, Task):
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
            self.info_label = self.central_sub_layout.create_and_add_label(
                manager.task.info, 2, 2, 60, 40, "black"
            )
            self.info_label.setWordWrap(True)
            self.info_label.setProperty("type", "optional")
            self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.create_gui_properties_task()

    def test_training(self) -> None:
        self.testing_training = True
        self.central_sub_layout.delete_optional_widgets("optional")
        self.central_sub_layout.delete_optional_widgets("optional2")
        self.right_layout_general.delete_optional_widgets("optional")
        self.right_layout_general.delete_optional_widgets("optional2")
        self.check_buttons()
        manager.reset_subject_task_training()
        self.create_gui_properties_common(start_row_general=8)

    def create_gui_properties_common(self, start_row_general: int) -> None:
        self.line_edits = []
        self.central_sub_layout.delete_optional_widgets("optional2")
        self.right_layout_general.delete_optional_widgets("optional2")
        # remove all the tabs from the right_layout and recreate general
        self.restart_tab_panel()
        # restore subject selection
        self.subject_label = self.right_layout_general.create_and_add_label(
            "Subject", 0, 2, 20, 2, "black"
        )
        self.subject_label.setProperty("type", "optional")

        self.possible_subjects = ["None"] + manager.subjects.df["name"].tolist()
        self.subject_combo = self.right_layout_general.create_and_add_combo_box(
            "subject",
            0,
            32,
            30,
            2,
            self.possible_subjects,
            0,
            self.select_subject,
        )
        self.subject_combo.setProperty("type", "optional")
        remove_names = [
            "next_task",
            "minimum_duration",
            "refractary_period",
        ]
        properties = {
            k: v
            for k, v in manager.training.get_dict().items()
            if k not in remove_names
        }
        # sort the properties into the tabs
        for tab_name, properties_list in manager.training.gui_tabs.items():
            # create a tab
            tab_layout = ExtraLayout(self.window, 30, 84)
            self.create_tab_with_scroll_area(tab_name, tab_layout)
            row = 4
            for property in properties_list:
                if property in properties:
                    self.create_label_and_value(
                        tab_layout, row, 2, property, str(properties[property])
                    )
                    row += 2
                    properties.pop(property)
                else:
                    # log error
                    print(
                        f"Tab setting {property} not found in settings, check spelling"
                    )

        # add the rest to general tab
        for i, (k, v) in enumerate(properties.items()):
            self.create_label_and_value(
                self.right_layout_general, start_row_general, 2, k, str(v)
            )
            if i == 0:
                start_row_general += 4
            else:
                start_row_general += 2
        self.update_gui()

    def create_gui_properties_task(self) -> None:
        row = 4
        self.create_label_and_value(
            self.right_layout_general,
            row,
            2,
            "manual_number_of_trials",
            str(manager.task.manual_number_of_trials),
        )
        row += 4
        self.create_gui_properties_common(row)

    def select_subject(self, value: str, key: str) -> None:
        current_value = ""
        if value != "None":
            manager.subject.subject_series = manager.subjects.get_last_entry(
                "name", value
            )
            if manager.subject.create_from_subject_series(auto=False):
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
        if self.testing_training:
            self.create_gui_properties_common(start_row_general=8)
        else:
            self.create_gui_properties_task()

    def run_task_button_clicked(self) -> None:
        self.change_properties()
        manager.task.settings = manager.training.settings
        manager.task.training = manager.training
        if self.testing_training:
            try:
                manager.task.training.df = pd.read_csv(
                    manager.task.subject_path, sep=";"
                )
                manager.task.training.update_training_settings()
            except Exception:
                pass
        else:
            manager.state = State.LAUNCH_MANUAL
            self.monitor_button_clicked()
            self.update_gui()

    def create_label_and_value(
        self,
        layout: Layout,
        row: int,
        column: int,
        name: str,
        value: str,
        width: int = 30,
    ) -> None:
        label = layout.create_and_add_label(
            name, row, column, width, 2, "black", bold=True
        )
        label.setProperty("type", "optional2")
        if name in manager.training.gui_tabs_restricted:
            line_edit = layout.create_and_add_combo_box(
                name,
                row,
                column + width,
                52,
                2,
                manager.training.gui_tabs_restricted[name],
                0,
                self.change_combo,
            )
        else:
            line_edit = layout.create_and_add_line_edit(
                value, row, column + width, 52, 2, self.change_text
            )
        line_edit.setProperty("type", "optional2")
        self.line_edits.append(line_edit)

    def change_properties(self) -> None:
        properties = manager.training.get_dict()
        remove_names = [
            "next_task",
            "minimum_duration",
            "refractary_period",
        ]
        properties = {k: v for k, v in properties.items() if k not in remove_names}
        new_dict = {}

        try:
            manager.task.manual_number_of_trials = int(self.line_edits[0].text())
        except Exception:
            pass

        for i, (k, v) in enumerate(properties.items()):
            # TODO: discuss the i + 1 with Rafa.
            # Should we handle the settings changing through the actions?
            # Or make line_edits a dictionary so we can access it by key?
            new_dict[k] = self.line_edits[i + 1].text()
            # widget = self.line_edits[i]
            # if isinstance(widget, QLineEdit):
            #     new_dict[k] = widget.text()
            # elif isinstance(widget, QComboBox):
            #     new_dict[k] = widget.currentText()

        manager.training.load_settings_from_dict(new_dict)

    def change_text(self) -> None:
        pass

    def change_combo(self, value: str, key: str) -> None:
        # TODO: I need to do something here to change this in line_edits?
        pass

    def update_gui(self) -> None:
        self.update_status_label()
        self.check_buttons()
