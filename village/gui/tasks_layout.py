from PyQt5.QtWidgets import QLabel

from village.gui.layout import Layout


class TasksLayout(Layout):
    def __init__(self, window):
        super().__init__(window)
        self.draw()

    def draw(self):
        self.first_row = 10
        self.first_column = 10

        self.tasks_button.setDisabled(True)
        self.tasks_button.setStyleSheet("QPushButton {background-color: lightblue}")

        label = QLabel("Tasks")
        label.setStyleSheet("font-weight: bold")
        self.addWidget(
            label,
            self.first_row,
            self.first_column,
            self.widget_height,
            self.label_width,
        )
