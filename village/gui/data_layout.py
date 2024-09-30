from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame
from PyQt5.QtCore import QTimer

from village.classes.enums import DataTable
from village.data import data
from village.gui.layout import Layout
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class DataLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.add_rows_to_table)
        self.timer.start(settings.get("UPDATE_TIME_MS"))
        self.df = DataFrame()
        self.complete_df = DataFrame()
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)

        self.searching = ""
        self.previous_searching = ""

        possible_values = DataTable.values()
        index = DataTable.get_index_from_value(data.table)

        self.title = self.create_and_add_combo_box(
            "title", 5, 10, 64, 2, possible_values, index, self.change_data_table
        )

        self.search_label = self.create_and_add_label("search", 5, 87, 8, 2, "Search")
        self.search_edit = self.create_and_add_line_edit("", 5, 95, 34, 2, self.search)

        self.update_data()
        self.create_table()

    def update_data(self) -> None:
        match data.table:
            case DataTable.EVENTS:
                self.complete_df = data.events.df
                self.widths = [20, 20, 20, 140]
            case DataTable.SESSIONS_SUMMARY:
                self.complete_df = data.sessions_summary.df
                self.widths = [20, 20, 20, 20, 20, 20, 20, 20]
            case DataTable.SUBJECTS:
                self.complete_df = data.subjects.df
                self.widths = [20, 20, 20, 20, 20, 100]
            case DataTable.WATER_CALIBRATION:
                self.complete_df = data.water_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.SOUND_CALIBRATION:
                self.complete_df = data.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.SESSION:
                self.complete_df = data.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
        self.df = self.obtain_searched_df()

    def change_data_table(self, value: str, key: str) -> None:
        if data.table != DataTable(value):
            data.table = DataTable(value)
            self.update_data()
            self.create_table()

    def obtain_searched_df(self) -> DataFrame:
        if self.searching == "":
            return self.complete_df
        else:
            return self.complete_df.loc[
                self.complete_df.apply(
                    lambda row: row.astype(str)
                    .str.contains(self.searching, case=False)
                    .any(),
                    axis=1,
                )
            ]

    def create_table(self) -> None:
        self.model = self.create_and_add_table(
            self.df, 8, 0, 210, 42, widths=self.widths
        )

    def add_rows_to_table(self) -> None:
        self.update_data()
        if self.searching == self.previous_searching:
            self.model.add_rows(self.df)
        else:
            self.previous_searching = self.searching
            self.create_table()

    def search(self, value: str) -> None:
        self.searching = value
