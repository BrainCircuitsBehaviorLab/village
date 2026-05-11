from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidget, QListWidgetItem

from village.classes.enums import State
from village.custom_classes.calibration_base import CalibrationBase
from village.gui.layout import Layout
from village.manager import manager

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow

_MENU_COL = 1
_MENU_WIDTH = 24
_C_ROW = 7
_CAL_COL = 27  # content starts at column 27


class CalibrationLayout(Layout):
    """Main calibration tab layout with a left menu and per-calibration panels."""

    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self._highlight_nav_button(self.calibration_button)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self._current_idx: int = 0
        self._calibrations: list[CalibrationBase] = []
        self._draw()

    def _draw(self) -> None:
        for cal in vars(manager.calibrations).values():
            if isinstance(cal, CalibrationBase) and cal.is_active():
                cal.init_panel(self.window)
                self._calibrations.append(cal)

        if not self._calibrations:
            self.create_and_add_label(
                "No calibrations available.", _C_ROW, _CAL_COL, 40, 2, "black"
            )
            return

        # ── left menu ──────────────────────────────────────────────────────────
        tab_font = QFont("DejaVu Sans Condensed", 9)
        tab_font.setBold(True)
        self.menu_list = QListWidget()
        self.menu_list.setFont(tab_font)
        self.menu_list.setStyleSheet(
            "QListWidget { background: #e8e8e8; border: none; outline: none; }"
            "QListWidget::item {"
            " background: #d0d0d0; color: black;"
            " padding: 6px 8px; margin-bottom: 2px;"
            " border: 1px solid #aaaaaa; border-radius: 3px; }"
            "QListWidget::item:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QListWidget::item:hover { background: #b0c4de; border-color: #b0c4de; }"
        )
        self.menu_list.setSpacing(1)
        for cal in self._calibrations:
            self.menu_list.addItem(QListWidgetItem(cal.display_name))
        self.menu_list.currentRowChanged.connect(self._on_menu_changed)
        self.addWidget(self.menu_list, _C_ROW, _MENU_COL, 44, _MENU_WIDTH + 2)

        # ── calibration panels ─────────────────────────────────────────────────
        # Each stacked_widget spans the full right content area (row 0, full height)
        # so the calibration's internal row references (7-48) align with the window.
        for cal in self._calibrations:
            self.addWidget(cal.container, _C_ROW, _CAL_COL, 44, 173)
            cal.container.hide()

        self._calibrations[0].container.show()
        self.menu_list.setCurrentRow(0)

    # ── menu selection ─────────────────────────────────────────────────────────

    def _on_menu_changed(self, new_idx: int) -> None:
        if new_idx == self._current_idx or not self._calibrations:
            return
        if not self._calibrations[self._current_idx].change_layout():
            self.menu_list.blockSignals(True)
            self.menu_list.setCurrentRow(self._current_idx)
            self.menu_list.blockSignals(False)
            return
        self._calibrations[self._current_idx].container.hide()
        self._current_idx = new_idx
        self._calibrations[new_idx].container.show()

    # ── Layout interface ───────────────────────────────────────────────────────

    def change_layout(self, auto: bool = False) -> bool:
        if self._calibrations:
            return self._calibrations[self._current_idx].change_layout(auto)
        return True

    def update_gui(self) -> None:
        self.update_status_label_buttons()
        if self._calibrations:
            self._calibrations[self._current_idx].update_gui()

    def stop_button_clicked(self) -> None:
        if self._calibrations:
            cal = self._calibrations[self._current_idx]
            if hasattr(cal, "stop_button_clicked"):
                cal.stop_button_clicked()
