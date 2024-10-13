from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Type

from village.classes.enums import State
from village.classes.task import Task
from village.data import data
from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.classes.task import Task
    from village.gui.gui_window import GuiWindow
    from village.gui.layout import PushButton


class TasksLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        self.tasks_button.setDisabled(True)

        self.stop_task_button = self.create_and_add_button(
            "STOP TASK",
            4,
            89,
            16,
            2,
            self.stop_task,
            "Stop a running task",
        )

        self.label = self.create_and_add_label("TASKS", 10, 10, 30, 2, "black")
        self.task_buttons: list[PushButton] = []

        for index, (key, value) in enumerate(data.tasks.items()):
            button = self.create_and_add_button(
                key,
                12 + 2 * index,
                40,
                30,
                2,
                partial(self.run_task, value),
                "Running the task",
            )
            self.task_buttons.append(button)

            self.check_buttons()

    def check_buttons(self) -> None:
        if data.state.can_stop_task():
            self.stop_task_button.setEnabled(True)
            for button in self.task_buttons:
                button.setEnabled(False)
        else:
            self.stop_task_button.setEnabled(False)
            for button in self.task_buttons:
                button.setEnabled(True)

    def run_task(self, cls: Type) -> None:
        if issubclass(cls, Task):
            data.task = cls()
            data.state = State.LAUNCH_MANUAL
            self.update_gui()

    def stop_task(self) -> None:
        data.state = State.SAVE_MANUAL
        self.update_gui()

    def update_gui(self) -> None:
        self.update_status_label()
        self.check_buttons()
