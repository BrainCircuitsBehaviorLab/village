from __future__ import annotations

from typing import TYPE_CHECKING

from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class MainLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self):
        self.main_button.setDisabled(True)

        self.image = self.create_and_add_image(10, 10, 192, 30, "mouse_village.png")
