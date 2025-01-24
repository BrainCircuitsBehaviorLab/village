from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMessageBox

from village.gui.layout import Layout
from village.manager import manager

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


# from PyQt5.QtCore import (
#     qInstallMessageHandler,
# )

# def qt_message_handler(mode, context, message) -> None:
#     pass
#     # if mode == QtWarningMsg:
#     # if True:
#     #     print(f"Qt Warning: {message}")
#     #     print(f"  File: {context.file}")
#     #     print(f"  Line: {context.line}")

# qInstallMessageHandler(qt_message_handler)


class MainLayout(Layout):
    def __init__(self, window: GuiWindow, first_draw: bool = False) -> None:
        super().__init__(window)
        self.first_draw = first_draw
        self.draw()

    def draw(self) -> None:
        self.main_button.setDisabled(True)

        self.image = self.create_and_add_image(10, 10, 192, 30, "village.png")

        text = "Error initializing the system, please check the logs. "
        text += "System running in debug mode. "
        text += manager.errors
        if manager.errors != "" and self.first_draw:
            QMessageBox.information(
                self.window,
                "DEBUG",
                text,
            )

    def update_gui(self) -> None:
        self.update_status_label_buttons()
