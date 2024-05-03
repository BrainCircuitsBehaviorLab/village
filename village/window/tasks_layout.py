from __future__ import annotations

from typing import TYPE_CHECKING

from village.window.layout import Layout

if TYPE_CHECKING:
    from village.window.gui_window import GuiWindow


class TasksLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        self.disable(self.tasks_button)

        self.label = self.create_and_add_label("TASKS", 10, 10, 30, 2, "black")
