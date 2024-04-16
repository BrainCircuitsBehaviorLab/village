from PyQt5.QtWidgets import QGridLayout, QMessageBox, QPushButton


class Layout(QGridLayout):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.width = window.width
        self.height = window.height
        self.num_of_columns = 212
        self.num_of_rows = 50
        self.column_width = int(self.width / self.num_of_columns)
        self.row_height = int(self.height / self.num_of_rows)
        self.widget_height = 2
        self.top_row = 0

        self.button_width = 20
        self.label_width = 30

        self.first_menu_button = 56
        self.last_menu_button = 192

        self.setHorizontalSpacing(0)
        self.setVerticalSpacing(0)

        for i in range(self.num_of_columns):
            self.setColumnMinimumWidth(i, self.column_width)

        for i in range(self.num_of_rows):
            self.setRowMinimumHeight(i, self.row_height)

        # self.delete_all_elements()
        self.create_common_elements()

    def create_common_elements(self):
        self.exit_button = QPushButton("Exit")
        self.exit_button.setStyleSheet("QPushButton {background-color: lightcoral}")
        self.exit_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.exit_button.clicked.connect(self.exit_button_clicked)

        self.main_button = QPushButton("Main")
        self.main_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.main_button.clicked.connect(self.main_button_clicked)

        self.monitor_button = QPushButton("Monitor")
        self.monitor_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.monitor_button.clicked.connect(self.monitor_button_clicked)

        self.tasks_button = QPushButton("Tasks")
        self.tasks_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.tasks_button.clicked.connect(self.tasks_button_clicked)

        self.data_button = QPushButton("Data")
        self.data_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.data_button.clicked.connect(self.data_button_clicked)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setFixedSize(
            self.button_width * self.column_width, self.widget_height * self.row_height
        )
        self.settings_button.clicked.connect(self.settings_button_clicked)

        self.addWidget(
            self.main_button,
            self.top_row,
            self.first_menu_button,
            self.widget_height,
            self.button_width,
        )
        self.addWidget(
            self.monitor_button,
            self.top_row,
            self.first_menu_button + self.button_width,
            self.widget_height,
            self.button_width,
        )
        self.addWidget(
            self.tasks_button,
            self.top_row,
            self.first_menu_button + 2 * self.button_width,
            self.widget_height,
            self.button_width,
        )
        self.addWidget(
            self.data_button,
            self.top_row,
            self.first_menu_button + 3 * self.button_width,
            self.widget_height,
            self.button_width,
        )
        self.addWidget(
            self.settings_button,
            self.top_row,
            self.first_menu_button + 4 * self.button_width,
            self.widget_height,
            self.button_width,
        )
        self.addWidget(
            self.exit_button,
            self.top_row,
            self.last_menu_button,
            self.widget_height,
            self.button_width,
        )

    def exit_button_clicked(self):
        reply = QMessageBox.question(
            self.window,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.window.exit_app()

    def change_layout(self):
        return True

    def main_button_clicked(self):
        if self.change_layout():
            self.window.create_main_layout()

    def monitor_button_clicked(self):
        if self.change_layout():
            self.window.create_monitor_layout()

    def tasks_button_clicked(self):
        if self.change_layout():
            self.window.create_tasks_layout()

    def data_button_clicked(self):
        if self.change_layout():
            self.window.create_data_layout()

    def settings_button_clicked(self):
        if self.change_layout():
            self.window.create_settings_layout()

    def closeEvent(self, event):
        event.ignore()

    def delete_optional_widgets(self, type):
        for i in reversed(range(self.count())):
            widget = self.itemAt(i).widget()
            if widget.property("type") == type:
                widget.hide()

    def delete_all_elements(self):
        for i in reversed(range(self.count())):
            layoutItem = self.itemAt(i)
            if layoutItem is not None:
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.deleteLater()
