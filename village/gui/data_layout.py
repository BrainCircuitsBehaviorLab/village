from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame

from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class DataLayout(Layout):
    def __init__(self, window: GuiWindow, df: DataFrame) -> None:
        super().__init__(window)
        self.df = df
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)
        # self.label = self.create_and_add_label("DATA", 10, 10, 30, 2, "black")
        self.model = self.create_and_add_table(self.df, 10, 10, 200, 40)
