from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pandas as pd
from classes.enums import State
from pandas import DataFrame
from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from village.classes.enums import DataTable
from village.data import data
from village.gui.layout import Layout
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
                if column_name == "next_settings":
                    current_value = self.model().data(index, Qt.DisplayRole)
                    new_value = self.model_parent.layout_parent.edit_next_settings(
                        current_value
                    )
                    self.model().setData(index, new_value, Qt.EditRole)
                elif column_name == "next_session_time":
                    current_value = self.model().data(index, Qt.DisplayRole)
                    new_value = self.model_parent.layout_parent.edit_next_session_time(
                        current_value
                    )
                    self.model().setData(index, new_value, Qt.EditRole)

                elif column_name == "active":
                    current_value = self.model().data(index, Qt.DisplayRole)
                    self.openDaysSelectionDialog(index, current_value)

                else:
                    super().mouseDoubleClickEvent(event)
            else:
                if column_name == "next_settings":
                    current_value = self.model().data(index, Qt.DisplayRole)
                    self.model_parent.layout_parent.show_next_settings(current_value)
                else:
                    super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def openDaysSelectionDialog(self, index, current_value) -> None:
        dialog = DaysSelectionDialog(self, current_value)
        if dialog.exec_() == QDialog.Accepted:
            selected_days = dialog.getSelection()
            if selected_days:
                self.model().setData(index, selected_days, Qt.EditRole)


class DaysSelectionDialog(QDialog):
    def __init__(self, parent=None, current_value=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Days or On/Off")

        self.layout = QVBoxLayout(self)

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

        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.okButton)
        self.layout.addLayout(self.buttonLayout)

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

    def __init__(self, df: pd.DataFrame, layout_parent: DataLayout) -> None:
        super().__init__()
        self.df = df
        self.editable = False
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

    def headerData(self, section: int, orientation: Any, role: int) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.df.columns[section])
            elif orientation == Qt.Vertical:
                return str(self.df.index[section])
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole:
            self.df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index) -> Any:
        if self.editable:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def insertRows(self, position, rows=1, index=None) -> bool:
        self.beginInsertRows(index or QModelIndex(), position, position + rows - 1)
        for _ in range(rows):
            new_row = pd.DataFrame([[""] * self.columnCount()], columns=self.df.columns)
            self.df = pd.concat([self.df, new_row], ignore_index=True)
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

        self.delete_button = self.create_and_add_button(
            "DELETE",
            5,
            85,
            20,
            2,
            self.delete_button_clicked,
            "Delete the selected row",
        )
        self.data_button = self.create_and_add_button(
            "DATA", 5, 110, 20, 2, self.data_button_clicked, "View the data as a table"
        )
        self.data_raw_button = self.create_and_add_button(
            "DATA_RAW",
            5,
            135,
            20,
            2,
            self.data_raw_button_clicked,
            "View the raw data as a table",
        )
        self.video_button = self.create_and_add_button(
            "VIDEO",
            5,
            160,
            20,
            2,
            self.video_button_clicked,
            "Watch the corresponding video",
        )
        self.plot_button = self.create_and_add_button(
            "PLOT",
            5,
            185,
            20,
            2,
            self.plot_button_clicked,
            "Plot the corresponding data",
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
                self.widths = [20, 20, 20, 20, 20, 100]
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

    def create_and_add_table(
        self,
        df: pd.DataFrame,
        row: int,
        column: int,
        width: int,
        height: int,
        widths: list[int] = [],
    ) -> Table:

        model = Table(df, self)
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
        self.data_button.setText("DATA")
        self.data_button.setToolTip("View the data as a table")
        self.delete_button.setText("DELETE")
        self.delete_button.setToolTip("Delete the selected row")
        match data.table:
            case DataTable.EVENTS:
                self.delete_button.setEnabled(False)
                self.data_button.setEnabled(False)
                self.data_raw_button.setEnabled(False)
                self.plot_button.setEnabled(False)
                if selected_indexes:
                    self.video_button.setEnabled(True)
                else:
                    self.video_button.setEnabled(False)
            case DataTable.SESSIONS_SUMMARY:
                if selected_indexes:
                    self.delete_button.setEnabled(True)
                    self.data_button.setEnabled(True)
                    self.data_raw_button.setEnabled(True)
                    self.video_button.setEnabled(True)
                    self.plot_button.setEnabled(True)
                else:
                    self.delete_button.setEnabled(False)
                    self.data_button.setEnabled(False)
                    self.data_raw_button.setEnabled(False)
                    self.video_button.setEnabled(False)
                    self.plot_button.setEnabled(False)
            case DataTable.SUBJECTS:
                self.data_button.setEnabled(True)
                self.data_raw_button.setEnabled(False)
                self.video_button.setEnabled(False)

                if self.editing:
                    self.data_button.setText("SAVE CHANGES")
                    self.data_button.setToolTip("Save the current changes")
                    self.delete_button.setText("CANCEL")
                    self.delete_button.setToolTip("Cancel the current changes")
                    self.delete_button.setEnabled(True)
                    self.plot_button.setEnabled(False)
                elif selected_indexes:
                    self.data_button.setText("ADD/EDIT")
                    self.data_button.setToolTip("Add or edit a subject")
                    self.delete_button.setEnabled(True)
                    self.plot_button.setEnabled(True)
                else:
                    self.data_button.setText("ADD/EDIT")
                    self.data_button.setToolTip("Add or edit a subject")
                    self.delete_button.setEnabled(False)
                    self.plot_button.setEnabled(False)
            case (
                DataTable.WATER_CALIBRATION
                | DataTable.SOUND_CALIBRATION
                | DataTable.TEMPERATURES
            ):
                self.data_button.setEnabled(False)
                self.data_raw_button.setEnabled(False)
                self.video_button.setEnabled(False)
                self.plot_button.setEnabled(True)
                if selected_indexes:
                    self.delete_button.setEnabled(True)
                else:
                    self.delete_button.setEnabled(False)
            case DataTable.SESSION:
                self.delete_button.setEnabled(False)
                self.data_button.setEnabled(False)
                self.data_raw_button.setEnabled(False)
                self.video_button.setEnabled(True)
                self.plot_button.setEnabled(True)

    def search(self, value: str) -> None:
        self.searching = value

    def data_raw_button_clicked(self) -> None:
        pass

    def delete_button_clicked(self) -> None:
        match data.table:
            case DataTable.EVENTS | DataTable.SESSION:
                pass
            case DataTable.WATER_CALIBRATION:
                pass
            case DataTable.SOUND_CALIBRATION:
                pass
            case DataTable.TEMPERATURES:
                pass
            case DataTable.SESSIONS_SUMMARY:
                pass
            case DataTable.SUBJECTS:
                if self.editing:
                    self.cancel()
                else:
                    self.delete()

    def video_button_clicked(self) -> None:
        pass

    def plot_button_clicked(self) -> None:
        pass

    def data_button_clicked(self) -> None:
        match data.table:
            case (
                DataTable.EVENTS
                | DataTable.WATER_CALIBRATION
                | DataTable.SOUND_CALIBRATION
                | DataTable.TEMPERATURES
                | DataTable.SESSION
            ):
                pass
            case DataTable.SESSIONS_SUMMARY:
                self.show_data()
            case DataTable.SUBJECTS:
                self.edit()

    def show_data(self) -> None:
        pass

    def cancel(self) -> None:
        self.editing = False
        self.model.editable = False
        data.state = State.WAIT
        data.changing_settings = False
        self.update_status_label()
        self.update_buttons()
        if data.table == DataTable.SUBJECTS:
            self.model.beginResetModel()
            self.model.df = data.subjects.df
            self.model.endResetModel()
            self.update_data()
            self.create_table()

    def delete(self) -> None:
        selected_indexes = self.model.table_view.selectionModel().selectedRows()
        if selected_indexes:
            reply = QMessageBox.question(
                self.window,
                "Delete",
                "Do you want to delete the selected row? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                for index in selected_indexes:
                    self.model.beginRemoveRows(QModelIndex(), index.row(), index.row())
                    self.model.df.drop(index.row(), inplace=True)
                    self.model.endRemoveRows()
                data.subjects.df = self.model.df
                data.subjects.save_from_df(data.training)

            self.model.table_view.selectionModel().clearSelection()
            self.update_buttons

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
                data.subjects.save_from_df(data.training)
                self.update_data()
                self.create_table()
        elif data.state.can_edit_subjects():
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
        else:
            text = "Wait until the box is empty before editing the subjects."
            QMessageBox.information(self.window, "EDIT", text)

    def change_layout(self) -> bool:
        if self.data_button.text() == "SAVE CHANGES":
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

    def edit_next_settings(self, current_value: str) -> str:
        dict_values = data.training.get_dict_from_jsonstring(current_value)

        self.reply = QDialog()
        self.reply.setWindowTitle("Next settings")
        self.reply.setFixedWidth(600)
        layout = QVBoxLayout()
        self.line_edits: list[QLineEdit] = []

        properties = data.training.get_settings_names()
        for name in properties:
            value = dict_values.get(name)
            value = value if value is not None else ""
            label = QLabel(name + ":")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(str(value))
            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            layout.addLayout(h_layout)
            self.line_edits.append(line_edit)

        btns_layout = QHBoxLayout()
        self.btn_ok = QPushButton("SAVE")
        self.btn_cancel = QPushButton("CANCEL")
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        layout.addLayout(btns_layout)
        self.reply.setLayout(layout)

        self.btn_ok.clicked.connect(self.reply.accept)
        self.btn_cancel.clicked.connect(self.reply.reject)

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

    def show_next_settings(self, current_value: str) -> None:
        dict_values = data.training.get_dict_from_jsonstring(current_value)

        self.reply = QDialog()
        self.reply.setWindowTitle("Next settings")
        self.reply.setFixedWidth(600)
        layout = QVBoxLayout()
        self.line_edits = []

        properties = data.training.get_settings_names()
        for name in properties:
            value = dict_values.get(name)
            value = value if value is not None else ""
            label = QLabel(name + ":")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(str(value))
            line_edit.setReadOnly(True)
            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            layout.addLayout(h_layout)
            self.line_edits.append(line_edit)

        self.btn_ok = QPushButton("CLOSE")
        layout.addWidget(self.btn_ok)
        self.reply.setLayout(layout)

        self.btn_ok.clicked.connect(self.reply.accept)

        if self.reply.exec_():
            return
