from __future__ import annotations

import json
import os
import traceback
from typing import TYPE_CHECKING, Any

import cv2
import pandas as pd
from classes.enums import State
from pandas import DataFrame
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from village.classes.enums import DataTable
from village.gui.layout import Layout
from village.log import log
from village.manager import manager
from village.plots.create_pixmap import create_pixmap
from village.plots.sound_calibration_plot import sound_calibration_plot
from village.plots.temperatures_plot import temperatures_plot
from village.plots.water_calibration_plot import water_calibration_plot
from village.scripts import time_utils, utils
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class TableView(QTableView):
    def __init__(self, model: Table) -> None:
        super().__init__()
        self.setModel(model)
        self.model_parent = model

    def mouseDoubleClickEvent(self, event) -> None:
        index: QModelIndex = self.indexAt(event.pos())
        if index.isValid():
            flags = self.model().flags(index)
            column = index.column()
            column_name = self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
            if manager.table == DataTable.SUBJECTS:
                if flags & Qt.ItemIsEditable and manager.state.can_edit_data():
                    self.searching = ""
                    self.model_parent.layout_parent.search_edit.setText("")
                    self.model_parent.layout_parent.update_gui()
                    if column_name == "next_settings":
                        manager.state = State.MANUAL_MODE
                        current_value = self.model().data(index, Qt.DisplayRole)
                        new_value = self.model_parent.layout_parent.edit_next_settings(
                            current_value
                        )
                        self.model().setData(index, new_value, Qt.EditRole)
                        self.save_changes_in_df()
                    elif column_name == "next_session_time":
                        manager.state = State.MANUAL_MODE
                        current_value = self.model().data(index, Qt.DisplayRole)
                        new_value = (
                            self.model_parent.layout_parent.edit_next_session_time(
                                current_value
                            )
                        )
                        self.model().setData(index, new_value, Qt.EditRole)
                        self.save_changes_in_df()
                    elif column_name == "active":
                        manager.state = State.MANUAL_MODE
                        current_value = self.model().data(index, Qt.DisplayRole)
                        self.openDaysSelectionDialog(index, current_value)
                    else:
                        manager.state = State.MANUAL_MODE
                        super().mouseDoubleClickEvent(event)
                elif flags & Qt.ItemIsEditable:
                    text = "Wait until the box is empty before editing the tables."
                    QMessageBox.information(self, "EDIT", text)
                else:
                    super().mouseDoubleClickEvent(event)

            elif manager.table == DataTable.SESSIONS_SUMMARY:
                if flags & Qt.ItemIsEditable:
                    if column_name == "settings":
                        manager.state = State.MANUAL_MODE
                        current_value = self.model().data(index, Qt.DisplayRole)
                        new_value = self.model_parent.layout_parent.edit_task_settings(
                            current_value, manager.state.can_edit_data()
                        )
                        self.model().setData(index, new_value, Qt.EditRole)
                        self.save_changes_in_df()

                        parent = self.model_parent.layout_parent

                        paths = parent.get_paths_from_sessions_summary_row(
                            parent.get_selected_row_series()
                        )

                        json_path = paths[2]
                        try:
                            with open(json_path, "w") as file:
                                json.dump(current_value, file)
                        except Exception:
                            log.error(
                                "Error trying to modify the json file",
                                exception=traceback.format_exc(),
                            )
                    else:
                        text = str(index.data())
                        text = text.replace("  |  ", "\n")
                        QMessageBox.information(self, "", text)
            else:
                text = str(index.data())
                text = text.replace("  |  ", "\n")
                QMessageBox.information(self, "", text)
        else:
            super().mouseDoubleClickEvent(event)

    def save_changes_in_df(self) -> None:
        if manager.table == DataTable.SUBJECTS:
            manager.subjects.df = self.model_parent.df
            manager.subjects.save_from_df(manager.training)
        elif manager.table == DataTable.TEMPERATURES:
            manager.temperatures.df = self.model_parent.df
            manager.temperatures.save_from_df()
        elif manager.table == DataTable.WATER_CALIBRATION:
            manager.water_calibration.df = self.model_parent.df
            manager.water_calibration.save_from_df()
        elif manager.table == DataTable.SOUND_CALIBRATION:
            manager.sound_calibration.df = self.model_parent.df
            manager.sound_calibration.save_from_df()
        elif manager.table == DataTable.SESSIONS_SUMMARY:
            manager.sessions_summary.df = self.model_parent.df
            manager.sessions_summary.save_from_df()
        manager.state = State.WAIT

    def openDaysSelectionDialog(self, index, current_value) -> None:
        dialog = DaysSelectionDialog(self, current_value)
        if dialog.exec_() == QDialog.Accepted:
            selected_days = dialog.getSelection()
            if selected_days:
                self.model().setData(index, selected_days, Qt.EditRole)
                self.save_changes_in_df()
                manager.state = State.WAIT


class DaysSelectionDialog(QDialog):
    def __init__(self, parent=None, current_value=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Days or On/Off")

        self.layout: QVBoxLayout = QVBoxLayout(self)

        self.days_checkboxes = {
            "Mon": QCheckBox("Monday"),
            "Tue": QCheckBox("Tuesday"),
            "Wed": QCheckBox("Wednesday"),
            "Thu": QCheckBox("Thursday"),
            "Fri": QCheckBox("Friday"),
            "Sat": QCheckBox("Saturday"),
            "Sun": QCheckBox("Sunday"),
        }

        for checkbox in self.days_checkboxes.values():
            self.layout.addWidget(checkbox)

        self.on_checkbox = QCheckBox("ON")
        self.off_checkbox = QCheckBox("OFF")
        self.layout.addWidget(self.on_checkbox)
        self.layout.addWidget(self.off_checkbox)

        self.on_checkbox.toggled.connect(self.toggle_on)
        self.off_checkbox.toggled.connect(self.toggle_off)

        for checkbox in self.days_checkboxes.values():
            checkbox.toggled.connect(self.toggle_days)

        if current_value:
            self.set_initial_values(current_value)
        else:
            self.off_checkbox.setChecked(True)

        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("SAVE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btns_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def set_initial_values(self, value) -> None:
        if value == "ON":
            self.on_checkbox.setChecked(True)
        elif value == "OFF" or value == "":
            self.off_checkbox.setChecked(True)
        else:
            days = value.split("-")
            for day in days:
                if day in self.days_checkboxes:
                    self.days_checkboxes[day].setChecked(True)

    def toggle_on(self) -> None:
        self.on_checkbox.blockSignals(True)
        self.off_checkbox.blockSignals(True)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(True)

        if self.on_checkbox.isChecked():
            self.off_checkbox.setChecked(False)
            for checkbox in self.days_checkboxes.values():
                checkbox.setChecked(False)
        elif any(checkbox.isChecked() for checkbox in self.days_checkboxes.values()):
            pass
        else:
            self.off_checkbox.setChecked(True)

        self.on_checkbox.blockSignals(False)
        self.off_checkbox.blockSignals(False)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(False)

    def toggle_off(self) -> None:
        self.on_checkbox.blockSignals(True)
        self.off_checkbox.blockSignals(True)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(True)

        if self.off_checkbox.isChecked():
            self.on_checkbox.setChecked(False)
            for checkbox in self.days_checkboxes.values():
                checkbox.setChecked(False)
        elif any(checkbox.isChecked() for checkbox in self.days_checkboxes.values()):
            pass
        else:
            self.on_checkbox.setChecked(True)

        self.on_checkbox.blockSignals(False)
        self.off_checkbox.blockSignals(False)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(False)

    def toggle_days(self) -> None:
        self.on_checkbox.blockSignals(True)
        self.off_checkbox.blockSignals(True)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(True)

        self.on_checkbox.setChecked(False)
        if any(checkbox.isChecked() for checkbox in self.days_checkboxes.values()):
            self.off_checkbox.setChecked(False)
        elif not self.on_checkbox.isChecked():
            self.off_checkbox.setChecked(True)

        self.on_checkbox.blockSignals(False)
        self.off_checkbox.blockSignals(False)
        for checkbox in self.days_checkboxes.values():
            checkbox.blockSignals(False)

    def getSelection(self) -> str | None:
        if self.on_checkbox.isChecked():
            return "ON"
        if self.off_checkbox.isChecked():
            return "OFF"

        selected_days = [
            day
            for day, checkbox in self.days_checkboxes.items()
            if checkbox.isChecked()
        ]
        if selected_days:
            return "-".join(selected_days)
        return None

    def accept(self) -> None:
        super().accept()


class Table(QAbstractTableModel):

    def __init__(
        self, df: pd.DataFrame, layout_parent: DataLayout, editable: bool = False
    ) -> None:
        super().__init__()
        self.df = df
        self.editable = editable
        self.layout_parent = layout_parent
        self.table_view = TableView(self)

    def rowCount(self, parent=None) -> int:
        return self.df.shape[0]

    def columnCount(self, parent=None) -> int:
        return self.df.shape[1]

    def data(self, index, role=Qt.DisplayRole) -> str | None:
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                return str(self.df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return str(self.df.columns[section])
        elif orientation == Qt.Vertical:
            if section < len(self.df.index):
                return str(self.df.index[section])
            else:
                return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole:
            column_dtype = self.df.dtypes.iloc[index.column()]
            try:
                if column_dtype == "int64" or column_dtype == "Int64":
                    value = int(value)
                elif column_dtype == "float64" or column_dtype == "float32":
                    value = float(value)
                elif column_dtype == "bool":
                    value = bool(value)
                elif column_dtype == "object" or column_dtype == "string":
                    value = str(value)
                elif column_dtype == "datetime64[ns]":
                    value = pd.to_datetime(value)
                elif column_dtype == "timedelta64[ns]":
                    value = pd.to_timedelta(value)

                self.df.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
            except (ValueError, TypeError):
                return False
        return False

    def flags(self, index) -> Any:
        if self.editable:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def insertRow(self, position, index=None) -> bool:
        self.beginInsertRows(index or QModelIndex(), position, position)
        new_row = pd.DataFrame([[""] * self.columnCount()], columns=self.df.columns)
        new_row = manager.subjects.df_from_df(new_row, manager.training)
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.df.reset_index(drop=True, inplace=True)
        self.endInsertRows()
        return True

    def add_rows(self, new_df: pd.DataFrame) -> None:
        scroll_position = self.table_view.verticalScrollBar().value()
        scroll_max = self.table_view.verticalScrollBar().maximum()
        rows_before = self.rowCount()
        move_to_bottom = True if scroll_position == scroll_max else False
        self.df = new_df
        if self.rowCount() > rows_before:
            self.beginInsertRows(QModelIndex(), rows_before, self.rowCount() - 1)
            self.endInsertRows()
        if move_to_bottom:
            self.table_view.scrollToBottom()


class DataLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)

        self.central_layout = QStackedLayout()
        self.addLayout(self.central_layout, 4, 0, 46, 210)
        self.page1 = QWidget()
        self.page1.setStyleSheet("background-color:white")
        self.page1Layout = DfLayout(self.window, 46, 210)
        self.page1.setLayout(self.page1Layout)
        self.page2 = QWidget()
        self.page2.setStyleSheet("background-color:white")
        self.page2Layout = VideoLayout(self.window, 46, 210)
        self.page2.setLayout(self.page2Layout)
        self.page3 = QWidget()
        self.page3.setStyleSheet("background-color:white")
        self.page3Layout = PlotLayout(self.window, 46, 210)
        self.page3.setLayout(self.page3Layout)

        self.central_layout.addWidget(self.page1)
        self.central_layout.addWidget(self.page2)
        self.central_layout.addWidget(self.page3)

        self.central_layout.setCurrentWidget(self.page1)

        self.page1Layout.video_change_requested.connect(self.change_to_video)
        self.page1Layout.plot_change_requested.connect(self.change_to_plot)
        self.page2Layout.data_from_video_change_requested.connect(self.change_to_df)
        self.page3Layout.data_from_plot_change_requested.connect(self.change_to_df)

        self.update_data()

    def change_to_video(self, path: str) -> None:
        self.central_layout.setCurrentWidget(self.page2)
        self.page2Layout.start_video(path)

    def change_to_plot(self, path: str) -> None:
        self.central_layout.setCurrentWidget(self.page3)
        pixmap = QPixmap()

        dpi = int(settings.get("MATPLOTLIB_DPI"))
        width = 210 * self.column_width / dpi
        height = 46 * self.row_height / dpi

        if manager.table == DataTable.SESSIONS_SUMMARY:
            try:
                paths = self.page1Layout.get_paths_from_sessions_summary_row(
                    self.page1Layout.get_selected_row_series()
                )
                df = pd.read_csv(paths[0], sep=";")
                df_raw = pd.read_csv(paths[1], sep=";")
                figure = manager.session_plot.create_plot(df, df_raw, width, height)
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create session plot", exception=traceback.format_exc()
                )
        elif manager.table == DataTable.SUBJECTS:
            path = self.page1Layout.get_path_from_subjects_row(
                self.page1Layout.get_selected_row_series()
            )
            try:
                df = pd.read_csv(path, sep=";")
                figure = manager.subject_plot.create_plot(df, width, height)
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create plot for file: " + path,
                    exception=traceback.format_exc(),
                )
        elif manager.table == DataTable.WATER_CALIBRATION:
            try:
                df = manager.water_calibration.get_last_water_df()
                figure = water_calibration_plot(df, width, height, None)
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create water calibration plot",
                    exception=traceback.format_exc(),
                )
        elif manager.table == DataTable.SOUND_CALIBRATION:
            try:
                df = manager.sound_calibration.get_last_sound_df()
                figure = sound_calibration_plot(df, width, height, None)
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create sound calibration plot",
                    exception=traceback.format_exc(),
                )
        elif manager.table == DataTable.TEMPERATURES:
            try:
                figure = temperatures_plot(
                    manager.temperatures.df.copy(), width, height
                )
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create temperatures plot",
                    exception=traceback.format_exc(),
                )
        elif manager.table == DataTable.SESSION:
            try:
                dfs = manager.get_both_sessions_dfs()
                # TODO: this needs to change to the online plot and
                # not use the session_plot
                figure = manager.session_plot.create_plot(dfs[1], dfs[0], width, height)
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create session plot", exception=traceback.format_exc()
                )
        elif manager.table in (DataTable.OLD_SESSION, DataTable.OLD_SESSION_RAW):
            try:
                figure = manager.session_plot.create_plot(
                    manager.old_session_df, manager.old_session_raw_df, width, height
                )
                pixmap = create_pixmap(figure)
            except Exception:
                log.error(
                    "Can not create session plot",
                    exception=traceback.format_exc(),
                )
        if not pixmap.isNull():
            self.page3Layout.plot_label.setPixmap(pixmap)
        else:
            self.page3Layout.plot_label.setText("Plot could not be generated")
            # TODO: should the figure be closed?

    def change_to_df(self) -> None:
        self.central_layout.setCurrentWidget(self.page1)

    def update_data(self) -> None:
        if self.central_layout.currentIndex() == 0:
            self.page1Layout.update_data()
            self.page1Layout.create_table()
        elif self.central_layout.currentIndex() == 1:
            self.page2Layout.update_data()
        elif self.central_layout.currentIndex() == 2:
            self.page3Layout.update_data()

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if self.central_layout.currentIndex() == 0:
            self.page1Layout.update_gui()
        elif self.central_layout.currentIndex() == 1:
            self.page2Layout.update_gui()
        elif self.central_layout.currentIndex() == 2:
            self.page3Layout.update_gui()


class DfLayout(Layout):
    plot_change_requested = pyqtSignal(str)
    video_change_requested = pyqtSignal(str)

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.df = DataFrame()
        self.complete_df = DataFrame()
        self.draw()

    def draw(self) -> None:
        self.searching = ""
        self.previous_searching = ""

        possible_values = DataTable.values()
        possible_values = possible_values[:-2]

        index = DataTable.get_index_from_value(manager.table)

        self.title = self.create_and_add_combo_box(
            "title", 0, 5, 35, 2, possible_values, index, self.change_data_table
        )

        self.back_button = self.create_and_add_button(
            "<-- BACK", 0, 5, 35, 2, self.back_button_clicked, "back"
        )
        self.back_button.hide()

        self.search_label = self.create_and_add_label("search", 0, 45, 10, 2, "Search")
        self.search_edit = self.create_and_add_line_edit("", 0, 55, 25, 2, self.search)

        self.first_button = self.create_and_add_button(
            "FIRST", 0, 85, 20, 2, self.button_clicked, "first"
        )
        self.second_button = self.create_and_add_button(
            "SECOND", 0, 110, 20, 2, self.button_clicked, "second"
        )
        self.third_button = self.create_and_add_button(
            "THIRD", 0, 135, 20, 2, self.button_clicked, "third"
        )
        self.fourth_button = self.create_and_add_button(
            "FOURTH", 0, 160, 20, 2, self.button_clicked, "fourth"
        )
        self.fifth_button = self.create_and_add_button(
            "FIFTH", 0, 185, 20, 2, self.button_clicked, "fifth"
        )

    def update_data(self) -> None:
        match manager.table:
            case DataTable.EVENTS:
                self.complete_df = manager.events.df
                self.widths = [20, 20, 20, 140]
            case DataTable.SESSIONS_SUMMARY:
                self.complete_df = manager.sessions_summary.df
                self.widths = [20, 20, 20, 20, 20, 20, 20, 20, 20]
            case DataTable.SUBJECTS:
                self.complete_df = manager.subjects.df
                self.widths = [20, 20, 20, 20, 20, 100]
            case DataTable.WATER_CALIBRATION:
                self.complete_df = manager.water_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.SOUND_CALIBRATION:
                self.complete_df = manager.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.TEMPERATURES:
                self.complete_df = manager.temperatures.df
                self.widths = [20, 20, 20]
            case DataTable.SESSION:
                self.complete_df = manager.update_session_df()
                self.widths = [20, 20, 20, 70, 70]
            case DataTable.OLD_SESSION:
                self.complete_df = manager.old_session_df
                self.widths = [20, 20, 20, 20, 20, 20]
                self.title.setCurrentIndex(-1)
                self.title.hide()
                self.back_button.show()
            case DataTable.OLD_SESSION_RAW:
                self.complete_df = manager.old_session_raw_df
                self.widths = [20, 20, 20, 60, 60]
                self.title.setCurrentIndex(-1)
                self.title.hide()
                self.back_button.show()
        self.df = self.obtain_searched_df()

    def back_button_clicked(self) -> None:
        self.back_button.hide()
        self.title.show()
        self.title.setCurrentText(DataTable.SESSIONS_SUMMARY.value)

    def create_table(self) -> None:
        editable = (
            True
            if manager.table in (DataTable.SUBJECTS, DataTable.SESSIONS_SUMMARY)
            else False
        )
        self.model = self.create_and_add_table(
            self.df, 4, 0, 210, 42, widths=self.widths, editable=editable
        )
        self.model.dataChanged.connect(self.on_data_changed)

        self.update_buttons()
        self.model.table_view.selectionModel().selectionChanged.connect(
            self.update_buttons
        )

    def create_and_add_table(
        self,
        df: pd.DataFrame,
        row: int,
        column: int,
        width: int,
        height: int,
        widths: list[int],
        editable: bool,
    ) -> Table:

        model = Table(df, self, editable)
        # model.table_view.setFixedSize(
        #     width * self.column_width, height * self.row_height
        # )

        model.table_view.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        model.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        model.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        model.table_view.setSelectionBehavior(QTableView.SelectRows)
        model.table_view.setSelectionMode(QTableView.SingleSelection)
        for i in range(len(widths)):
            model.table_view.setColumnWidth(i, widths[i] * self.column_width)

        model.table_view.scrollToBottom()

        self.addWidget(model.table_view, row, column, height, width)

        return model

    def change_data_table(self, value: str, key: str) -> None:
        if value != "":
            if manager.table != DataTable(value):
                manager.table = DataTable(value)
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

    def update_gui(self) -> None:
        self.update_data()
        if self.searching == self.previous_searching:
            self.model.add_rows(self.df)
        else:
            self.previous_searching = self.searching
            self.create_table()

    def connect_button_to_delete(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.delete_button_clicked)
        button.setText("DELETE")
        button.setToolTip("Delete the selected row")
        button.show()

    def connect_button_to_data_raw(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.data_raw_button_clicked)
        button.setText("DATA RAW")
        button.setToolTip("Show the raw data")
        button.show()

    def connect_button_to_data(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.data_button_clicked)
        button.setText("DATA")
        button.setToolTip("Show the data")
        button.show()

    def connect_button_to_video(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.video_button_clicked)
        button.setText("VIDEO")
        button.setToolTip("Watch the video")
        button.show()

    def connect_button_to_plot(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.plot_button_clicked)
        button.setText("PLOT")
        button.setToolTip("Plot the data")
        button.show()

    def connect_button_to_add(self, button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except TypeError:
            pass
        button.clicked.connect(self.add_button_clicked)
        button.setText("ADD")
        button.setToolTip("Add a new subject")
        button.show()

    def update_buttons(self) -> None:
        selected_indexes = self.model.table_view.selectionModel().selectedRows()
        match manager.table:
            case DataTable.EVENTS:
                self.first_button.hide()
                self.second_button.hide()
                self.third_button.hide()
                self.fourth_button.hide()
                self.connect_button_to_video(self.fifth_button)
                if selected_indexes:
                    self.fifth_button.setEnabled(True)
                else:
                    self.fifth_button.setEnabled(False)
            case DataTable.SESSIONS_SUMMARY:
                self.connect_button_to_delete(self.first_button)
                self.connect_button_to_data_raw(self.second_button)
                self.connect_button_to_data(self.third_button)
                self.connect_button_to_video(self.fourth_button)
                self.connect_button_to_plot(self.fifth_button)
                if selected_indexes:
                    self.first_button.setEnabled(True)
                    self.second_button.setEnabled(True)
                    self.third_button.setEnabled(True)
                    self.fourth_button.setEnabled(True)
                    self.fifth_button.setEnabled(True)
                else:
                    self.first_button.setEnabled(False)
                    self.second_button.setEnabled(False)
                    self.third_button.setEnabled(False)
                    self.fourth_button.setEnabled(False)
                    self.fifth_button.setEnabled(False)
            case DataTable.SUBJECTS:
                self.first_button.hide()
                self.second_button.hide()
                self.connect_button_to_add(self.third_button)
                self.connect_button_to_delete(self.fourth_button)
                self.connect_button_to_plot(self.fifth_button)
                self.second_button.setEnabled(True)
                if selected_indexes:
                    self.fourth_button.setEnabled(True)
                    self.fifth_button.setEnabled(True)
                else:
                    self.fourth_button.setEnabled(False)
                    self.fifth_button.setEnabled(False)
            case (
                DataTable.WATER_CALIBRATION
                | DataTable.SOUND_CALIBRATION
                | DataTable.TEMPERATURES
            ):
                self.first_button.hide()
                self.second_button.hide()
                self.third_button.hide()
                self.connect_button_to_delete(self.fourth_button)
                self.connect_button_to_plot(self.fifth_button)
                self.fifth_button.setEnabled(True)
                if selected_indexes:
                    self.fourth_button.setEnabled(True)
                else:
                    self.fourth_button.setEnabled(False)
            case DataTable.SESSION:
                self.first_button.hide()
                self.second_button.hide()
                self.third_button.hide()
                self.fourth_button.hide()
                self.connect_button_to_plot(self.fifth_button)
                self.fifth_button.setEnabled(True)
            case DataTable.OLD_SESSION | DataTable.OLD_SESSION_RAW:
                self.first_button.hide()
                self.second_button.hide()
                self.third_button.hide()
                self.connect_button_to_video(self.fourth_button)
                self.connect_button_to_plot(self.fifth_button)
                self.fourth_button.setEnabled(True)
                self.fifth_button.setEnabled(True)

    def search(self, value: str) -> None:
        self.searching = value

    def button_clicked(self) -> None:
        pass

    def data_button_clicked(self) -> None:
        p0 = self.get_paths_from_sessions_summary_row(self.get_selected_row_series())[0]
        p1 = self.get_paths_from_sessions_summary_row(self.get_selected_row_series())[1]
        message = "Can not read file: " + p0
        try:
            manager.old_session_df = pd.read_csv(p0, sep=";")
            message = "Can not read file: " + p1
            manager.old_session_raw_df = pd.read_csv(p1, sep=";")
            self.change_data_table("OLD_SESSION", "")
        except Exception:
            log.error(message, exception=traceback.format_exc())

    def data_raw_button_clicked(self) -> None:
        p0 = self.get_paths_from_sessions_summary_row(self.get_selected_row_series())[0]
        p1 = self.get_paths_from_sessions_summary_row(self.get_selected_row_series())[1]
        message = "Can not read file: " + p0
        try:
            manager.old_session_df = pd.read_csv(p0, sep=";")
            message = "Can not read file: " + p1
            manager.old_session_raw_df = pd.read_csv(p1, sep=";")
            self.change_data_table("OLD_SESSION_RAW", "")
        except Exception:
            log.error(message, exception=traceback.format_exc())

    def get_selected_row_series(self) -> pd.Series | None:
        selected_indexes = self.model.table_view.selectionModel().selectedRows()
        if selected_indexes:
            index = selected_indexes[0]
            return self.model.df.iloc[index.row()]
        else:
            return None

    def get_path_from_events_row(self, row: pd.Series) -> str:
        date_str = row["date"]
        date = time_utils.date_from_string(date_str)
        video_directory = settings.get("VIDEOS_DIRECTORY")
        return time_utils.find_closest_file(video_directory, "CORRIDOR", date)

    def get_path_from_subjects_row(self, row: pd.Series) -> str:
        subject = row["name"]
        sessions_directory = settings.get("SESSIONS_DIRECTORY")
        path = os.path.join(sessions_directory, subject, subject + ".csv")
        return path

    def get_paths_from_sessions_summary_row(self, row: pd.Series) -> list[str]:
        date_str = row["date"]
        task = row["task"]
        subject = row["subject"]
        date = time_utils.date_from_string(date_str)
        date_str = time_utils.filename_string_from_date(date)
        filename = subject + "_" + task + "_" + date_str
        sessions_directory = settings.get("SESSIONS_DIRECTORY")
        video_directory = settings.get("VIDEOS_DIRECTORY")
        session_path = os.path.join(sessions_directory, subject, filename + ".csv")
        session_raw_path = os.path.join(
            sessions_directory, subject, filename + "_RAW.csv"
        )
        session_settings_path = os.path.join(
            sessions_directory, subject, filename + ".json"
        )
        video_path = os.path.join(video_directory, subject, filename + ".mp4")
        video_data_path = os.path.join(video_directory, subject, filename + ".csv")

        paths = [
            session_path,
            session_raw_path,
            session_settings_path,
            video_path,
            video_data_path,
        ]

        return paths

    def video_button_clicked(self) -> None:
        path = ""
        selected_row = self.get_selected_row_series()
        if selected_row is not None:
            if manager.table == DataTable.EVENTS:
                path = self.get_path_from_events_row(selected_row)
            elif manager.table == DataTable.SESSIONS_SUMMARY:
                path = self.get_paths_from_sessions_summary_row(selected_row)[3]
        self.video_change_requested.emit(path)

    def plot_button_clicked(self) -> None:
        selected_row = self.get_selected_row_series()
        if selected_row is not None:
            self.plot_change_requested.emit("")
        elif manager.table in [
            DataTable.SESSION,
            DataTable.OLD_SESSION,
            DataTable.OLD_SESSION_RAW,
            DataTable.WATER_CALIBRATION,
            DataTable.SOUND_CALIBRATION,
            DataTable.TEMPERATURES,
        ]:
            self.plot_change_requested.emit("")

    def add_button_clicked(self) -> None:
        if manager.state.can_edit_data():
            self.searching = ""
            self.search_edit.setText("")
            self.update_gui()
            self.changes_made = True
            self.update_buttons()
            row_count = self.model.rowCount()
            self.model.insertRow(row_count)
            self.model.table_view.save_changes_in_df()
            self.update_buttons()
        else:
            text = "Wait until the box is empty before editing the subjects."
            QMessageBox.information(self.window, "EDIT", text)

    def delete_button_clicked(self) -> None:
        self.searching = ""
        self.search_edit.setText("")
        self.update_gui()
        selected_indexes = self.model.table_view.selectionModel().selectedRows()
        if selected_indexes:
            if manager.state.can_edit_data():
                if manager.table == DataTable.SUBJECTS:
                    text = (
                        "Do you want to delete the selected subject? "
                        + "This action cannot be undone."
                    )
                elif manager.table == DataTable.SESSIONS_SUMMARY:
                    text = (
                        "Do you want to delete the selected session? "
                        + "The session data and the video will be deleted. "
                        + "The session will be removed from the sessions_summary. "
                        + "This action cannot be undone."
                    )
                else:
                    text = (
                        "Do you want to delete the selected row? "
                        + "This action cannot be undone."
                    )
                reply = QMessageBox.question(
                    self.window,
                    "Delete",
                    text,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    row = self.get_selected_row_series()
                    if row is not None:
                        if manager.table == DataTable.SESSIONS_SUMMARY:
                            del_paths = self.get_paths_from_sessions_summary_row(row)
                            for path in del_paths:
                                if os.path.exists(path):
                                    os.remove(path)
                            subject = row["subject"]
                            directory = str(settings.get("SESSIONS_DIRECTORY"))
                            utils.create_global_csv_for_subject(subject, directory)

                        index = selected_indexes[0]
                        self.model.beginRemoveRows(
                            QModelIndex(), index.row(), index.row()
                        )
                        self.model.df.drop(index.row(), inplace=True)
                        self.model.df.reset_index(drop=True, inplace=True)
                        self.model.endRemoveRows()
                self.model.table_view.save_changes_in_df()
                self.model.table_view.selectionModel().clearSelection()
                self.update_buttons()
            else:
                text = "Wait until the box is empty before editing the subjects."
                QMessageBox.information(self.window, "EDIT", text)

    def cancel(self) -> None:
        manager.state = State.WAIT
        self.update_buttons()
        if manager.table == DataTable.SUBJECTS:
            self.model.beginResetModel()
            self.model.df = manager.subjects.df
            self.model.endResetModel()
            self.update_data()
            self.create_table()

    def edit_task_settings(self, current_value: str, can_edit: bool) -> str:
        try:
            new_dict = json.loads(current_value)
        except Exception:
            log.error(
                "Error reading settings",
                exception=traceback.format_exc(),
            )

        self.reply = QDialog()
        self.reply.setWindowTitle("Task settings")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        self.line_edits: list[QLineEdit] = []

        for name, value in new_dict.items():
            label = QLabel(name + ":")
            line_edit = QLineEdit()
            line_edit.setReadOnly(True)
            if name == "observations" and can_edit:
                line_edit.setReadOnly(False)
            line_edit.setPlaceholderText(str(value))
            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            content_layout.addLayout(h_layout)
            self.line_edits.append(line_edit)

        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("SAVE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        content_layout.addLayout(btns_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self.reply)
        main_layout.addWidget(scroll_area)

        self.btn_ok.clicked.connect(self.reply.accept)
        self.btn_cancel.clicked.connect(self.reply.reject)

        self.reply.adjustSize()
        current_height = self.reply.sizeHint().height()
        max_width = int(self.window.window_width * 0.5)
        max_height = min(
            current_height + int(self.window.window_height / 10),
            int(self.window.window_height * 0.8),
        )
        self.reply.setFixedWidth(max_width)
        self.reply.setFixedHeight(max_height)

        if self.reply.exec_():
            for index, line_edit in enumerate(self.line_edits):
                name = list(new_dict.keys())[index]
                if name == "observations":
                    value = (
                        line_edit.text()
                        if line_edit.text()
                        else line_edit.placeholderText()
                    )
                    new_dict[name] = value
        return json.dumps(new_dict)

    def edit_next_settings(self, current_value: str) -> str:
        manager.training.load_settings_from_jsonstring(current_value)
        new_dict = manager.training.get_dict()

        self.reply = QDialog()
        self.reply.setWindowTitle("Next settings")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        self.line_edits = []

        properties = manager.training.get_settings_names()
        for name in properties:
            value = new_dict.get(name, "")
            label = QLabel(name + ":")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(str(value))
            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            content_layout.addLayout(h_layout)
            self.line_edits.append(line_edit)

        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("SAVE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        content_layout.addLayout(btns_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self.reply)
        main_layout.addWidget(scroll_area)

        self.btn_ok.clicked.connect(self.reply.accept)
        self.btn_cancel.clicked.connect(self.reply.reject)

        self.reply.adjustSize()
        current_height = self.reply.sizeHint().height()
        max_width = int(self.window.window_width * 0.5)
        max_height = min(
            current_height + int(self.window.window_height / 10),
            int(self.window.window_height * 0.8),
        )
        self.reply.setFixedWidth(max_width)
        self.reply.setFixedHeight(max_height)

        if self.reply.exec_():
            for index, line_edit in enumerate(self.line_edits):
                name = properties[index]
                value = (
                    line_edit.text()
                    if line_edit.text()
                    else line_edit.placeholderText()
                )
                new_dict[name] = value
        _, new_dict = manager.training.correct_types_in_dict(new_dict)
        return json.dumps(new_dict)

    def edit_next_session_time(self, current_value: str) -> str:
        self.reply = QDialog()
        self.reply.setWindowTitle("Select Next Session Time")
        layout = QVBoxLayout()

        dateTimeEdit = QDateTimeEdit(self.reply)
        dateTimeEdit.setCalendarPopup(True)
        dateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        try:
            dateTimeEdit.setDateTime(time_utils.date_from_string(current_value))
        except Exception:
            dateTimeEdit.setDateTime(time_utils.now())

        okButton = QPushButton("OK", self.reply)
        okButton.clicked.connect(self.reply.accept)

        layout.addWidget(dateTimeEdit)
        layout.addWidget(okButton)

        self.reply.setLayout(layout)

        if self.reply.exec_():
            return dateTimeEdit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        else:
            return ""

    def on_data_changed(self) -> None:
        self.model.table_view.save_changes_in_df()


class PlotLayout(Layout):
    data_from_plot_change_requested = pyqtSignal(str)

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.draw()

    def draw(self) -> None:
        self.plot_label = QLabel()
        self.addWidget(self.plot_label, 0, 0, 46, 210)

        self.create_and_add_button("CLOSE", 0, 180, 20, 2, self.close, "Close the plot")

    def update_data(self) -> None:
        pass

    def close(self) -> None:
        self.data_from_plot_change_requested.emit("")


class VideoLayout(Layout):
    data_from_video_change_requested = pyqtSignal(str)

    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.draw()

    def draw(self) -> None:
        self.video_label = QLabel()
        self.addWidget(self.video_label, 0, 0, 46, 210)

        self.create_and_add_button(
            "CLOSE", 0, 180, 20, 2, self.close, "Close the video"
        )
        self.create_and_add_button(
            "PLAY/PAUSE", 4, 180, 20, 2, self.play_pause, "Play or pause the video"
        )

    def start_video(self, path: str) -> None:
        try:
            self.cap = cv2.VideoCapture(path)
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            self.timer = QTimer()
            millisecs = int(1000.0 / fps)
            self.timer.setTimerType(Qt.PreciseTimer)
            self.timer.timeout.connect(self.next_frame_slot)
            self.timer.start(millisecs)
        except Exception:
            pass

    def play_pause(self) -> None:
        try:
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start()
        except Exception:
            pass

    def stop_button_clicked(self) -> None:
        try:
            self.timer.stop()
            self.cap.release()
        except Exception:
            pass

    def close(self) -> None:
        self.stop_button_clicked()
        self.data_from_video_change_requested.emit("")

    def next_frame_slot(self) -> None:
        ret, frame = self.cap.read()
        if ret:
            img = QImage(
                frame.data,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                QImage.Format_BGR888,
            )

            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)

            pix = QPixmap.fromImage(img)
            self.video_label.setPixmap(pix)

    def update_data(self) -> None:
        pass
