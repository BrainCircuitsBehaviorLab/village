"""
Override this class in your project to create a custom calibration.

Example:
    class MyCalibration(CalibrationBase):

        def __init__(self) -> None:
            super().__init__()
            # name: of the attribute in self.calibrations and of the csv file
            name = "my_calibration"
            columns = ["date", "value"]
            types = [str, float]
            self.create_data_collection(name=name, columns=columns, types=types)

        @classmethod
        def is_active(cls) -> bool:
            return True

        def draw(self) -> None:
            self.layout.create_and_add_label("My Calibration", 0, 0, 20, 2, "black")

From a task: self.calibrations.my_calibration
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pandas as pd
from PyQt5.QtWidgets import QWidget

from village.classes.collection import Collection
from village.gui.layout import Layout

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from village.custom_classes.calibration_task_base import CalibrationTaskBase
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

    Inherits from Collection, so the data methods (df, add_entry,
    save_from_df...) are directly available on self. The Qt UI is a _Panel
    (a 44 x 172 grid) stored in self.layout: draw() adds the widgets with
    self.layout.create_and_add_label, create_and_add_button, etc.

    To define in subclasses:
        __init__  - call create_data_collection(name, columns, types). name
                    is the attribute in self.calibrations and the csv file
                    name (it can also be a class attribute). The left menu
                    shows display_name, name in upper case by default.
        is_active - whether the calibration appears in the CALIBRATION tab.
        draw      - the widgets of the panel.

    If the calibration needs to drive the hardware while measuring, write a
    CalibrationTaskBase subclass and launch it with self.run_task(task);
    task_running() says when it has finished.
    """

    _instance: ClassVar[CalibrationBase | None] = None

    def __init__(self) -> None:
        """Initialises the Collection. Called once by import_all."""
        super().__init__()

    @property
    def display_name(self) -> str:
        return self.name.upper()

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
            try:
                utils.delete_all_elements_from_layout(self.layout)
            except RuntimeError:
                pass
        self.layout: _Panel = _Panel(window)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.draw()

    def reset(self) -> None:
        """Clears and redraws the panel (used after save/delete)."""
        from village.scripts import utils

        try:
            utils.delete_all_elements_from_layout(self.layout)
        except RuntimeError:
            pass
        self.draw()

    # ── Calibration tasks ──────────────────────────────────────────────────────

    def run_task(self, task: CalibrationTaskBase) -> bool:
        """Launches a calibration task (e.g. to open a valve while measuring).

        Returns:
            bool: False, without launching it, if a task is already running.
        """
        from village.classes.enums import State
        from village.manager import manager

        if self.task_running():
            return False
        manager.task = task
        manager.state = State.RUN_MANUAL
        manager.launch_task_calibration()
        return True

    def task_running(self) -> bool:
        """True from run_task until the task has finished and been closed.
        Check it in update_gui to know when the measurement can be entered."""
        from village.classes.enums import State
        from village.manager import manager

        return manager.state in (
            State.LAUNCH_MANUAL,
            State.RUN_MANUAL,
            State.SAVE_MANUAL,
        )

    def stop_task(self) -> None:
        """Stops the running calibration task, if any."""
        from village.classes.enums import State
        from village.manager import manager
        from village.scripts.log import log

        if manager.state == State.RUN_MANUAL:
            log.info("Calibration task manually stopped.")
            manager.task.stop_button_pressed = True
            manager.state = State.SAVE_MANUAL

    # ── Interface methods ──────────────────────────────────────────────────────

    def draw(self) -> None:
        """Draws the calibration UI. Override in subclasses."""

    def change_layout(self) -> bool:
        """Called before switching away from this calibration.

        Return False to prevent the switch (e.g. unsaved changes).
        """
        return True

    def update_status_label_buttons(self) -> None:
        """Delegates status bar update to the parent CalibrationLayout."""
        self.window.layout.update_status_label_buttons()

    def update_gui(self) -> None:
        """Called periodically to refresh the UI."""

    def create_plot(
        self,
        df: pd.DataFrame,
        width: float,
        height: float,
        point: tuple[float, float] | None = None,
    ) -> Figure | None:
        return None

    def get_last_calibration_df(self) -> pd.DataFrame:
        return self.df
