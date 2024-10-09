from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame
from PyQt5.QtWidgets import QMessageBox

from village.classes.enums import DataTable, State
from village.data import data
from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class DataLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.df = DataFrame()
        self.complete_df = DataFrame()
        self.editing = False
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)

        self.searching = ""
        self.previous_searching = ""

        possible_values = DataTable.values()
        index = DataTable.get_index_from_value(data.table)

        self.title = self.create_and_add_combo_box(
            "title", 5, 5, 35, 2, possible_values, index, self.change_data_table
        )

        self.search_label = self.create_and_add_label("search", 5, 45, 10, 2, "Search")
        self.search_edit = self.create_and_add_line_edit("", 5, 55, 25, 2, self.search)

        self.edit_button = self.create_and_add_button(
            "add/edit", 5, 85, 20, 2, self.edit, "Add or edit the table"
        )
        self.data_raw_button = self.create_and_add_button(
            "data_raw", 5, 110, 20, 2, self.data_raw, "View the raw data as a table"
        )
        self.data_button = self.create_and_add_button(
            "data", 5, 135, 20, 2, self.data, "View the data as a table"
        )
        self.video_button = self.create_and_add_button(
            "video", 5, 160, 20, 2, self.video, "Watch the corresponding video"
        )
        self.plot_button = self.create_and_add_button(
            "plot", 5, 185, 20, 2, self.plot, "Plot the corresponding data"
        )

        self.update_data()
        self.create_table()

    def update_data(self) -> None:
        match data.table:
            case DataTable.EVENTS:
                self.complete_df = data.events.df
                self.widths = [20, 20, 20, 140]
            case DataTable.SESSIONS_SUMMARY:
                self.complete_df = data.sessions_summary.df
                self.widths = [20, 20, 20, 20, 20, 20, 20, 20, 20]
            case DataTable.SUBJECTS:
                self.complete_df = data.subjects.df
                self.widths = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
            case DataTable.WATER_CALIBRATION:
                self.complete_df = data.water_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.SOUND_CALIBRATION:
                self.complete_df = data.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.TEMPERATURES:
                self.complete_df = data.temperatures.df
                self.widths = [20, 20, 20]
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
        self.update_buttons()
        self.model.table_view.selectionModel().selectionChanged.connect(
            self.update_buttons
        )

    def update_gui(self) -> None:
        self.update_status_label()
        if not self.editing:
            self.update_data()
            if self.searching == self.previous_searching:
                self.model.add_rows(self.df)
            else:
                self.previous_searching = self.searching
                self.create_table()

    def update_buttons(self) -> None:
        selected_indexes = self.model.table_view.selectionModel().selectedRows()
        if self.editing:
            # change the text for the edit button
            self.edit_button.setText("save changes")
        else:
            self.edit_button.setText("add/edit")
        match data.table:
            case DataTable.EVENTS:
                self.data_raw_button.setEnabled(False)
                self.data_button.setEnabled(False)
                self.plot_button.setEnabled(False)
                self.edit_button.setEnabled(False)
                if selected_indexes:
                    self.video_button.setEnabled(True)
                else:
                    self.video_button.setEnabled(False)
            case DataTable.SESSIONS_SUMMARY:
                self.edit_button.setEnabled(False)
                if selected_indexes:
                    self.data_raw_button.setEnabled(True)
                    self.data_button.setEnabled(True)
                    self.video_button.setEnabled(True)
                    self.plot_button.setEnabled(True)
                else:
                    self.data_raw_button.setEnabled(False)
                    self.data_button.setEnabled(False)
                    self.video_button.setEnabled(False)
                    self.plot_button.setEnabled(False)
            case DataTable.SUBJECTS:
                self.data_raw_button.setEnabled(False)
                self.data_button.setEnabled(False)
                self.video_button.setEnabled(False)
                self.edit_button.setEnabled(True)
                if self.editing:
                    self.plot_button.setEnabled(False)
                elif selected_indexes:
                    self.plot_button.setEnabled(True)
                else:
                    self.plot_button.setEnabled(False)
            case (
                DataTable.WATER_CALIBRATION
                | DataTable.SOUND_CALIBRATION
                | DataTable.TEMPERATURES
                | DataTable.SESSION
            ):
                self.data_raw_button.setEnabled(False)
                self.data_button.setEnabled(False)
                self.video_button.setEnabled(False)
                self.plot_button.setEnabled(True)
                self.edit_button.setEnabled(False)

    def search(self, value: str) -> None:
        self.searching = value

    def data_raw(self) -> None:
        pass

    def data(self) -> None:
        pass

    def video(self) -> None:
        pass

    def plot(self) -> None:
        pass

    def edit(self) -> None:
        self.searching = ""
        self.update_gui()
        if self.editing:
            self.editing = False
            self.model.editable = False
            data.state = State.WAIT
            data.changing_settings = False
            self.update_status_label()
            self.update_buttons()
            if data.table == DataTable.SUBJECTS:
                data.subjects.df = self.model.df
                data.subjects.save_from_df()
                self.create_table()
        else:
            match data.state:
                case State.WAIT:
                    # TODO disable plot
                    self.searching = ""
                    self.search_edit.setText("")
                    self.editing = True
                    self.model.editable = True
                    data.state = State.SETTINGS
                    data.changing_settings = True
                    self.update_status_label()
                    self.update_buttons()
                    row_count = self.model.rowCount()
                    self.model.insertRows(row_count, rows=50)

                case State.DETECTION | State.ACCESS:
                    text = "Wait until the box is empty before editing the subjects."
                    text = "Subject is being detected. " + text
                    QMessageBox.information(
                        self.window,
                        "EDIT",
                        text,
                    )
                case (
                    State.LAUNCH
                    | State.RUN_ACTION
                    | State.CLOSE_DOOR2
                    | State.RUN_CLOSED
                    | State.OPEN_DOOR2
                    | State.RUN_OPENED
                    | State.EXIT_UNSAVED
                    | State.SAVE_OUTSIDE
                    | State.SAVE_INSIDE
                    | State.WAIT_EXIT
                    | State.EXIT_SAVED
                    | State.OPEN_DOOR1
                    | State.CLOSE_DOOR1
                    | State.RUN_TRAPPED
                    | State.OPEN_DOOR2_STOP
                    | State.OPEN_DOORS_STOP
                    | State.MANUAL_RUN
                ):
                    QMessageBox.information(
                        self.window,
                        "EDIT",
                        "Wait until the box is empty before editing the subjects.",
                    )
                case State.EXIT_GUI | State.ERROR | State.SETTINGS:
                    pass

    def change_layout(self) -> bool:
        if self.edit_button.text() == "save changes":
            reply = QMessageBox.question(
                self.window,
                "Save changes",
                "Do you want to save the changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.edit()
                return True
            elif reply == QMessageBox.Discard:
                data.state = State.WAIT
                return True
            else:
                return False
        else:
            return True
