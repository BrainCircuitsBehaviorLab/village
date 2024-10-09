from __future__ import annotations

from typing import TYPE_CHECKING

from village.data import data
from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class TasksLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        self.tasks_button.setDisabled(True)

        self.label = self.create_and_add_label("TASKS", 10, 10, 30, 2, "black")

        for index, task in enumerate(data.tasks):
            self.create_and_add_button(
                task.name,
                12 + 2 * index,
                40,
                30,
                2,
                (lambda _, t=task: t.test_run()),
                "Running the task",
            )
