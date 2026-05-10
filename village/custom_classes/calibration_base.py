"""
Override this class in your project to create a custom calibration.

Example:
    class MyCalibration(CalibrationBase):
        name = "MY CALIBRATION"
        col_name = "my_calibration"
        columns = ["date", "value"]
        types = [str, float]

        @classmethod
        def is_active(cls) -> bool:
            return True

        def draw(self) -> None:
            self.create_and_add_label("My Calibration", 0, 1, 20, 2, "black")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PyQt5.QtWidgets import QWidget

from village.classes.collection import Collection
from village.gui.layout import Layout

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow

# Content area dimensions (full window minus the left menu)
CAL_ROWS = 44
CAL_COLS = 172


class _Panel(Layout):
    """Internal Qt grid layout that holds the calibration widgets."""

    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window, stacked=True, rows=CAL_ROWS, columns=CAL_COLS)


class CalibrationBase(Collection):
    """Base class for all calibration panels.

    Inherits from Collection so data methods (df, save_from_df, get_valve_time…)
    are directly available on self. The Qt UI is handled by a _Panel instance
    stored in self._panel; unknown attribute lookups are proxied to it so
    create_and_add_label, addWidget, etc. work without prefixing.

    Class attributes to define in subclasses:
        name        - label shown in the left menu
        columns   - Collection column names
        types   - Collection column types
    """

    def __init__(self) -> None:
        """Initialises the Collection. Called once by import_all."""
        super().__init__()

    @classmethod
    def is_active(cls) -> bool:
        return True

    # ── Panel lifecycle ────────────────────────────────────────────────────────

    def init_panel(self, window: GuiWindow) -> None:
        """Creates (or recreates) the Qt panel and calls draw().

        Called by CalibrationLayout each time the CALIBRATION tab is opened.
        """
        from village.scripts import utils

        self.window = window
        if hasattr(self, "layout"):
            utils.delete_all_elements_from_layout(self.layout)
        self.layout: _Panel = _Panel(window)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.draw()

    def reset(self) -> None:
        """Clears and redraws the panel (used after save/delete)."""
        from village.scripts import utils

        utils.delete_all_elements_from_layout(self.layout)
        self.draw()

    # ── Interface methods ──────────────────────────────────────────────────────

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
