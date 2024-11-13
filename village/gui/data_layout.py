from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pandas as pd
from classes.enums import State
from pandas import DataFrame
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from village.classes.enums import DataTable
from village.gui.layout import Layout
from village.manager import manager
from village.time_utils import time_utils

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
            if flags & Qt.ItemIsEditable:
                self.searching = ""
                self.model_parent.layout_parent.search_edit.setText("")
                self.model_parent.layout_parent.update_gui()
                if column_name == "next_settings" and manager.state.can_edit_subjects():
                    manager.state = State.SETTINGS
                    current_value = self.model().data(index, Qt.DisplayRole)
                    new_value = self.model_parent.layout_parent.edit_next_settings(
                        current_value
                    )
                    self.model().setData(index, new_value, Qt.EditRole)
                    self.save_changes_in_df()
                elif (
                    column_name == "next_session_time"
                    and manager.state.can_edit_subjects()
                ):
                    manager.state = State.SETTINGS
                    current_value = self.model().data(index, Qt.DisplayRole)
                    new_value = self.model_parent.layout_parent.edit_next_session_time(
                        current_value
                    )
                    self.model().setData(index, new_value, Qt.EditRole)
                    self.save_changes_in_df()
                elif column_name == "active" and manager.state.can_edit_subjects():
                    manager.state = State.SETTINGS
                    current_value = self.model().data(index, Qt.DisplayRole)
                    self.openDaysSelectionDialog(index, current_value)
                elif manager.state.can_edit_subjects():
                    manager.state = State.SETTINGS
                    super().mouseDoubleClickEvent(event)
                else:
                    text = "Wait until the box is empty before editing the tables."
                    QMessageBox.information(self, "EDIT", text)
            else:
                super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def save_changes_in_df(self) -> None:
        if manager.table == DataTable.SUBJECTS:
            manager.subjects.df = self.model_parent.df
            manager.subjects.save_from_df(manager.training)
        elif manager.table == DataTable.TEMPERATURES:
            manager.temperatures.df = self.model_parent.df
            manager.temperatures.save_from_df(manager.training)
        elif manager.table == DataTable.WATER_CALIBRATION:
            manager.water_calibration.df = self.model_parent.df
            manager.water_calibration.save_from_df(manager.training)
        elif manager.table == DataTable.SOUND_CALIBRATION:
            manager.sound_calibration.df = self.model_parent.df
            manager.sound_calibration.save_from_df(manager.training)
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
        self.df = DataFrame()
        self.complete_df = DataFrame()
        self.window = window
        self.draw()

    def draw(self) -> None:
        self.data_button.setDisabled(True)

        self.searching = ""
        self.previous_searching = ""

        possible_values = DataTable.values()
        possible_values.pop()

        index = DataTable.get_index_from_value(manager.table)

        self.title = self.create_and_add_combo_box(
            "title", 5, 5, 35, 2, possible_values, index, self.change_data_table
        )

        self.search_label = self.create_and_add_label("search", 5, 45, 10, 2, "Search")
        self.search_edit = self.create_and_add_line_edit("", 5, 55, 25, 2, self.search)

        self.first_button = self.create_and_add_button(
            "FIRST", 5, 85, 20, 2, self.button_clicked, "first"
        )
        self.second_button = self.create_and_add_button(
            "SECOND", 5, 110, 20, 2, self.button_clicked, "second"
        )
        self.third_button = self.create_and_add_button(
            "THIRD", 5, 135, 20, 2, self.button_clicked, "third"
        )
        self.fourth_button = self.create_and_add_button(
            "FOURTH", 5, 160, 20, 2, self.button_clicked, "fourth"
        )
        self.fifth_button = self.create_and_add_button(
            "FIFTH", 5, 185, 20, 2, self.button_clicked, "fifth"
        )

        self.update_data()
        self.create_table()

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
                self.complete_df = manager.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
            case DataTable.OLD_SESSION:
                self.complete_df = manager.sound_calibration.df
                self.widths = [20, 20, 20, 20, 20, 20]
        self.df = self.obtain_searched_df()

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
        model.table_view.setFixedSize(
            width * self.column_width, height * self.row_height
        )
        model.table_view.setSelectionBehavior(QTableView.SelectRows)
        model.table_view.setSelectionMode(QTableView.SingleSelection)
        for i in range(len(widths)):
            model.table_view.setColumnWidth(i, widths[i] * self.column_width)

        model.table_view.scrollToBottom()

        self.addWidget(model.table_view, row, column, height, width)

        return model

    def change_data_table(self, value: str, key: str) -> None:
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

    def create_table(self) -> None:
        editable = True if manager.table == DataTable.SUBJECTS else False
        self.model = self.create_and_add_table(
            self.df, 8, 0, 210, 42, widths=self.widths, editable=editable
        )
        self.model.dataChanged.connect(self.on_data_changed)

        self.update_buttons()
        self.model.table_view.selectionModel().selectionChanged.connect(
            self.update_buttons
        )

    def update_gui(self) -> None:
        self.update_status_label()
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
            case DataTable.OLD_SESSION:
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

    def data_raw_button_clicked(self) -> None:
        pass

    def video_button_clicked(self) -> None:
        pass

    def plot_button_clicked(self) -> None:
        pass

    def data_button_clicked(self) -> None:
        pass

    def add_button_clicked(self) -> None:
        if manager.state.can_edit_subjects():
            self.searching = ""
            self.search_edit.setText("")
            self.update_gui()
            self.changes_made = True
            self.update_status_label()
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
            if manager.state.can_edit_subjects():
                reply = QMessageBox.question(
                    self.window,
                    "Delete",
                    """Do you want to delete the selected row?
                    This action cannot be undone.""",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    for index in selected_indexes:
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
        self.update_status_label()
        self.update_buttons()
        if manager.table == DataTable.SUBJECTS:
            self.model.beginResetModel()
            self.model.df = manager.subjects.df
            self.model.endResetModel()
            self.update_data()
            self.create_table()

    def edit_next_settings(self, current_value: str) -> str:
        manager.training.load_settings_from_jsonstring(current_value)
        dict_values = manager.training.get_dict()

        self.reply = QDialog()
        self.reply.setWindowTitle("Next settings")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        self.line_edits: list[QLineEdit] = []

        properties = manager.training.get_settings_names()
        for name in properties:
            value = dict_values.get(name, "")
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
                dict_values[name] = value

        return json.dumps(dict_values)

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
