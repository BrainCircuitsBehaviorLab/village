from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Type

from PyQt5.QtCore import Qt

from village.classes.enums import State
from village.classes.task import Task
from village.data import data
from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.classes.task import Task
    from village.gui.gui_window import GuiWindow
    from village.gui.layout import LineEdit, PushButton


class TasksLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.selected = ""
        self.draw()

    def draw(self) -> None:
        self.line_edits: list[LineEdit] = []
        self.tasks_button.setDisabled(True)

        self.run_task_button = self.create_and_add_button(
            "RUN TASK",
            6,
            98,
            16,
            2,
            self.run_task,
            "Run the selected task",
        )

        self.task_buttons: list[PushButton] = []

        self.create_and_add_label("Tasks", 8, 2, 20, 2, "black")
        for index, (key, value) in enumerate(data.tasks.items()):
            button = self.create_and_add_button(
                key,
                10 + 2 * index,
                2,
                30,
                2,
                partial(self.select_task, value, key),
                "Select the task",
            )
            self.task_buttons.append(button)

            self.check_buttons()

    def check_buttons(self) -> None:
        if data.state.can_stop_task():
            self.run_task_button.setEnabled(False)
            for button in self.task_buttons:
                button.setEnabled(False)
            for line_edit in self.line_edits:
                line_edit.setEnabled(False)
        elif self.selected != "":
            self.run_task_button.setEnabled(True)
            for button in self.task_buttons:
                if button.text() == self.selected:
                    button.setEnabled(False)
                else:
                    button.setEnabled(True)
            for line_edit in self.line_edits:
                line_edit.setEnabled(False)
        else:
            self.run_task_button.setEnabled(False)
            for button in self.task_buttons:
                button.setEnabled(True)
            for line_edit in self.line_edits:
                line_edit.setEnabled(False)

    def select_task(self, cls: Type, name: str) -> None:
        if issubclass(cls, Task):
            self.selected = name
            self.delete_optional_widgets("optional")
            self.delete_optional_widgets("optional2")
            self.check_buttons()
            data.reset_subject_and_task()
            data.task = cls()
            data.task.settings = data.training.get_dictionary()
            self.name_label = self.create_and_add_label(
                data.task.name, 10, 37, 75, 2, "black"
            )
            self.name_label.setProperty("type", "optional")
            self.info_label = self.create_and_add_label(
                data.task.info, 12, 37, 65, 40, "black"
            )
            self.info_label.setWordWrap(True)
            self.info_label.setProperty("type", "optional")
            self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            self.subject_label = self.create_and_add_label(
                "Subject", 10, 110, 20, 2, "black"
            )
            self.subject_label.setProperty("type", "optional")

            self.possible_subjects = ["None"] + data.subjects.df.name.tolist()
            self.subject_combo = self.create_and_add_combo_box(
                "subject",
                10,
                140,
                30,
                2,
                self.possible_subjects,
                0,
                self.subject_selected,
            )
            self.subject_combo.setProperty("type", "optional")
            self.create_properties()

    def create_properties(self) -> None:
        self.delete_optional_widgets("optional2")
        row = 14
        properties = list(data.task.settings.keys())
        properties = [
            p
            for p in properties
            if p not in ["next_task", "minimum_duration", "refractary_period"]
        ]
        for i, p in enumerate(properties):
            v = str(data.task.settings[p])
            self.create_label_and_value(row, 110, p, v)
            if i == 1:
                row += 4
            else:
                row += 2
        self.update_gui()

    def subject_selected(self, value: str, key: str) -> None:
        data.subject.subject_series = data.subjects.get_last_entry("name", value)
        if data.subject.get_data_from_subject_series():
            data.task.subject = value
        if data.subject.subject_series is not None:
            try:
                current_value = data.subject.subject_series["next_settings"]
            except Exception:
                current_value = ""
        else:
            current_value = ""
        data.task.settings = data.training.get_dict_from_jsonstring(current_value)
        self.create_properties()

    def run_task(self) -> None:
        data.state = State.LAUNCH_MANUAL
        self.monitor_button_clicked()
        self.update_gui()

    def create_label_and_value(
        self, row: int, column: int, name: str, value: str, width: int = 30
    ) -> None:
        label = self.create_and_add_label(name, row, column, 30, 2, "black", bold=True)
        label.setProperty("type", "optional2")
        line_edit = self.create_and_add_line_edit(
            value, row, column + width, 64, 2, self.change_properties
        )
        line_edit.setProperty("type", "optional2")
        self.line_edits.append(line_edit)

    def change_properties(self) -> None:
        print("changing")

    def update_gui(self) -> None:
        self.update_status_label()
        self.check_buttons()
