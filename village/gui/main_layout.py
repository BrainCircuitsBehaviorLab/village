from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMessageBox

from village.gui.layout import Layout
from village.manager import manager

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


class MainLayout(Layout):
    """The initial layout displayed when the application starts or returns to main menu."""

    def __init__(self, window: GuiWindow, first_draw: bool = False) -> None:
        """Initializes the MainLayout.

        Args:
            window (GuiWindow): The parent window.
            first_draw (bool, optional): Whether this is the first time drawing on startup. Defaults to False.
        """
        super().__init__(window)
        self.first_draw = first_draw
        self.draw()

    def draw(self) -> None:
        """Draws the main menu elements, including the logo and status messages.

        Displays a warning messagebox if system initialization errors occurred.
        """
        self.main_button.setDisabled(True)

        self.image = self.create_and_add_image(10, 6, 180, 30, "village.png")

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
        """Updates the status line and buttons."""
        self.update_status_label_buttons()

