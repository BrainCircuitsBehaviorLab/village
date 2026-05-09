"""
Override this class in your project to create a custom calibration.

Example:
    class MyCalibration(CalibrationBase):
        name = "MY CALIBRATION"

        @classmethod
        def is_active(cls) -> bool:
            return True

        def draw(self) -> None:
            row = 1
            self.create_and_add_label("My Calibration", row, 1, 20, 2, "black")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget

from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow

# Columns available in the content area (full width minus the left menu)
CAL_ROWS = 51
CAL_COLS = 172


class CalibrationBase(Layout):
    """Base class for all calibration panels.

    Subclass this to create a calibration. The class is instantiated by
    CalibrationLayout when the user selects it from the menu.
    """

    name: str = "CALIBRATION"

    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window, stacked=True, rows=CAL_ROWS, columns=CAL_COLS)
        self.container = QWidget()
        self.container.setLayout(self)
        self.draw()

    @classmethod
    def is_active(cls) -> bool:
        """Returns True if this calibration should appear in the menu."""
        return True

    def draw(self) -> None:
        """Draws the calibration UI. Override in subclasses."""

    def change_layout(self, auto: bool = False) -> bool:
        """Called before switching away from this calibration.

        Return False to prevent the switch (e.g. unsaved changes).
        """
        return True

    def update_status_label_buttons(self) -> None:
        """Delegates status bar update to the parent CalibrationLayout."""
        self.window.layout.update_status_label_buttons()

    def update_gui(self) -> None:
        """Called periodically to refresh the UI."""
