from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer

from village.classes.enums import Table
from village.data import data
from village.gui.layout import Layout
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class DataLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.search)
        self.timer.start(settings.get("UPDATE_TIME_MS"))
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)

        self.searching = ""

        possible_values = Table.values()
        index = Table.get_index_from_value(data.table)

        self.title = self.create_and_add_combo_box(
            "title", 5, 10, 64, 2, possible_values, index, self.change_data_view
        )

        self.search_label = self.create_and_add_label("search", 5, 87, 8, 2, "Search")
        self.search_edit = self.create_and_add_line_edit("", 5, 95, 34, 2, self.search)

        self.change_data_view(data.table.value, "")

    def change_data_view(self, value: str, key: str) -> None:
        data.table = Table(value)
        match data.table:
            case Table.EVENTS:
                self.df = data.events.df
                self.widths = [20, 20, 20, 140]
            case Table.SESSIONS_SUMMARY:
                self.df = data.sessions_summary.df
                self.widths = [20, 20, 20, 20, 20, 20, 20, 20]
            case Table.SUBJECTS:
                self.df = data.subjects.df
                self.widths = [20, 20, 20, 20, 20, 100]
            case Table.WATER_CALIBRATION:
                self.df = data.water_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case Table.SOUND_CALIBRATION:
                self.df = data.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case Table.SESSION:
                self.df = data.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]

        self.change_table()

    def search(self, value: str | None = None, key: str = "") -> None:
        if value is not None:
            self.searching = value
        self.change_data_view(data.table.value, "")

    def change_table(self) -> None:
        if self.searching == "":
            df = self.df
        else:
            df = self.df.loc[
                self.df.apply(
                    lambda row: row.astype(str)
                    .str.contains(self.searching, case=False)
                    .any(),
                    axis=1,
                )
            ]
        self.model = self.create_and_add_table(df, 8, 0, 210, 42, widths=self.widths)
