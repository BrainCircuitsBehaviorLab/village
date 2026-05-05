from __future__ import annotations

import os
import re
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QInputDialog, QListWidget, QListWidgetItem, QMessageBox

from village.classes.enums import (
    Active,
    ControllerEnum,
    ScreenActive,
    State,
    SyncType,
)
from village.devices.camera import cam_box, cam_corridor
from village.devices.sound_device import get_sound_devices
from village.gui.layout import Layout, LineEdit, TimeEdit, ToggleButton
from village.manager import manager
from village.scripts import utils
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import Setting, settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


# ── Left menu panel ────────────────────────────────────────────────────────────
MENU_COL = 1
MENU_WIDTH = 22

# ── Right content panel ────────────────────────────────────────────────────────
C_COL = 28  # content start column
C_ROW = 7  # content start row
C_LABEL_W = 23  # label width
C_VAL_OFF = 23  # offset from C_COL to value widget column

# ── Value widget size constants ────────────────────────────────────────────────
size1 = 14
size2 = 45
size3 = 14
size4 = 14
small_box = 7
mini_box = 7

MENU_SECTIONS = [
    "MAIN SETTINGS",
    "CONTROLLER SETTINGS",
    "SOUND SETTINGS",
    "SCREEN SETTINGS",
    "CAMERA SETTINGS",
    "CORRIDOR SETTINGS",
    "SYNC SETTINGS",
    "TELEGRAM SETTINGS",
    "ADVANCED SETTINGS",
    "DEVICE ADDRESSES",
]

MENU_TOOLTIPS: dict[str, str] = {
    "MAIN SETTINGS": ("Main settings and project configuration."),
    "CONTROLLER SETTINGS": ("Behavior controller type (Bpod, Arduino, Raspberry)."),
    "SOUND SETTINGS": "Soundcard and audio device configuration.",
    "SCREEN SETTINGS": ("Screen or touchscreen configuration for behavioral stimuli."),
    "CAMERA SETTINGS": ("Camera framerates, resolution and tracking settings."),
    "CORRIDOR SETTINGS": (
        "Detection thresholds, weight limits and timing for corridor access."
    ),
    "SYNC SETTINGS": "Data synchronization to external drive or remote server.",
    "TELEGRAM SETTINGS": ("Telegram and alarm settings for notifications."),
    "ADVANCED SETTINGS": ("Advanced and visual settings."),
    "DEVICE ADDRESSES": ("Addresses for connected hardware devices."),
}

# Keys whose toggle value affects what is shown within their section
_CONDITIONAL_KEYS: dict[str, str] = {
    "USE_SOUNDCARD": "SOUND SETTINGS",
    "USE_SCREEN": "SCREEN SETTINGS",
    "BEHAVIOR_CONTROLLER": "CONTROLLER SETTINGS",
    "SYNC_TYPE": "SYNC SETTINGS",
}


class SettingsLayout(Layout):
    """Layout for viewing and modifying application settings."""

    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        self._highlight_nav_button(self.settings_button)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.critical_changes = False
        self._current_section: str = MENU_SECTIONS[0]
        # Uncommitted UI values buffered across section switches
        self._pending: dict[str, Any] = {}
        self.draw(all=True, modify="")

    # ── Pending-aware value accessors ──────────────────────────────────────────

    def _get(self, key: str) -> Any:
        """Returns the pending value for key if present, else the stored setting."""
        if key in self._pending:
            val = self._pending[key]
            if isinstance(val, str):
                vtype = settings.get_type(key)
                if vtype is not None and vtype not in (str, int, float, list):
                    with suppress(Exception):
                        return vtype(val)
            return val
        return settings.get(key)

    def _get_index(self, key: str) -> int:
        """Returns the toggle index for key, checking _pending first."""
        if key in self._pending:
            val_str = str(self._pending[key])
            possible = settings.get_values(key)
            with suppress(Exception):
                return possible.index(val_str)
        return settings.get_index(key)

    def _get_indices(self, key: str) -> list[int]:
        """Returns toggle indices for a list[Active] key, checking _pending first."""
        if key in self._pending:
            vals = self._pending[key]
            possible = settings.get_values(key)
            with suppress(Exception):
                return [possible.index(str(v)) for v in vals]
        return settings.get_indices(key)

    # ── Tracking lists ─────────────────────────────────────────────────────────

    def _init_tracking_lists(self) -> None:
        self.line_edits: list[LineEdit] = []
        self.line_edits_settings: list[Setting] = []
        self.time_edits: list[TimeEdit] = []
        self.time_edits_settings: list[Setting] = []
        self.toggle_buttons: list[ToggleButton] = []
        self.toggle_buttons_settings: list[Setting] = []
        self.list_of_line_edits: list[list[LineEdit]] = []
        self.list_of_line_edits_settings: list[Setting] = []
        self.list_of_toggle_buttons: list[list[ToggleButton]] = []
        self.list_of_toggle_buttons_settings: list[Setting] = []

    # ── Pending buffer management ──────────────────────────────────────────────

    def _flush_to_pending(self) -> None:
        """Saves current section's widget values into _pending
        without writing to disk."""
        for i, le in enumerate(self.line_edits):
            self._pending[self.line_edits_settings[i].key] = le.text()
        for i, time_edit in enumerate(self.time_edits):
            self._pending[self.time_edits_settings[i].key] = time_edit.time().toString(
                "HH:mm"
            )
        for i, toggle_button in enumerate(self.toggle_buttons):
            self._pending[self.toggle_buttons_settings[i].key] = toggle_button.text()
        for i, list_line in enumerate(self.list_of_line_edits):
            self._pending[self.list_of_line_edits_settings[i].key] = [
                le.text() for le in list_line
            ]
        for i, list_tb in enumerate(self.list_of_toggle_buttons):
            self._pending[self.list_of_toggle_buttons_settings[i].key] = [
                tb.text() for tb in list_tb
            ]
        with suppress(AttributeError, RuntimeError):
            self._pending["SOUND_DEVICE"] = self.sound_device_combobox.currentText()
        with suppress(AttributeError, RuntimeError):
            self._pending["PROJECT_DIRECTORY"] = (
                self.project_directory_combobox.currentText()
            )

    # ── Content area lifecycle ─────────────────────────────────────────────────

    def _destroy_content(self) -> None:
        """Removes all content-area widgets from the layout
        and resets tracking lists."""
        for i in reversed(range(self.count())):
            item = self.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if w.property("content_area"):
                    self.removeWidget(w)
                    w.deleteLater()
        self._init_tracking_lists()

    def _tag_content_widgets(self, from_index: int) -> None:
        for i in range(from_index, self.count()):
            item = self.itemAt(i)
            if item and item.widget():
                item.widget().setProperty("content_area", True)

    # ── Top-level draw ─────────────────────────────────────────────────────────

    def draw(self, all: bool, modify: str) -> None:
        self.settings_button.setDisabled(True)
        if all:
            self._init_tracking_lists()
            self._pending.clear()
            self._draw_static_chrome()
            self._current_section = MENU_SECTIONS[0]
            self._highlight_menu(MENU_SECTIONS[0])
            self.draw_section(MENU_SECTIONS[0])
        else:
            self._destroy_content()
            self.draw_section(self._current_section)

    # ── Static chrome ──────────────────────────────────────────────────────────

    def _draw_static_chrome(self) -> None:
        self.menu_list = QListWidget()
        tab_font = QFont("DejaVu Sans Condensed", 9)
        tab_font.setBold(True)
        self.menu_list.setFont(tab_font)
        self.menu_list.setStyleSheet(
            "QListWidget { background: #e8e8e8; border: none; outline: none; }"
            "QListWidget::item {"
            " background: #d0d0d0; color: black;"
            " padding: 6px 8px; margin-bottom: 2px;"
            " border: 1px solid #aaaaaa;"
            " border-radius: 3px; }"
            "QListWidget::item:selected { background: steelblue; color: white;"
            " border-color: steelblue; }"
            "QListWidget::item:hover { background: #b0c4de; border-color: #b0c4de; }"
            "QToolTip { background-color: white; color: black; font-size: 9pt; }"
        )
        self.menu_list.setSpacing(1)
        for name in MENU_SECTIONS:
            item = QListWidgetItem(name)
            item.setToolTip(MENU_TOOLTIPS.get(name, name))
            self.menu_list.addItem(item)
        self.menu_list.currentRowChanged.connect(
            lambda i: self.select_section(MENU_SECTIONS[i])
        )
        self.addWidget(self.menu_list, C_ROW, MENU_COL, 46, MENU_WIDTH + 2)

        self.save_button = self.create_and_add_button(
            "SAVE THE SETTINGS",
            47,
            C_COL,
            30,
            2,
            self.save_button_clicked,
            "Apply and save the settings",
            "powderblue",
        )
        self.save_button.setDisabled(True)

        self.restore_button = self.create_and_add_button(
            "RESTORE FACTORY SETTINGS",
            47,
            C_COL + 31,
            30,
            2,
            self.restore_button_clicked,
            "Restore the factory settings",
            "lightcoral",
        )
        self.restore_button.clicked.connect(self.restore_button_clicked)

    def _highlight_menu(self, selected: str) -> None:
        idx = MENU_SECTIONS.index(selected)
        if self.menu_list.currentRow() != idx:
            self.menu_list.setCurrentRow(idx)

    # ── Section selection ──────────────────────────────────────────────────────

    def select_section(self, name: str) -> None:
        if name == self._current_section:
            return
        # Buffer current section's values so they survive the section switch
        self._flush_to_pending()
        self._destroy_content()
        self._current_section = name
        self._highlight_menu(name)
        self.draw_section(name)

    # ── Section content drawing ────────────────────────────────────────────────

    def draw_section(self, name: str) -> None:
        before = self.count()
        row = C_ROW

        title = self.create_and_add_label(name, row, C_COL, C_LABEL_W, 2, "black")
        title.setProperty("type", name)
        row += 2

        if name == "MAIN SETTINGS":
            for s in settings.main_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            row += 1
            sub = self.create_and_add_label(
                "PROJECT", row, C_COL, C_LABEL_W, 2, "black"
            )
            sub.setProperty("type", name)
            row += 2
            for s in settings.directory_settings:
                if s.key == "APP_DIRECTORY":
                    continue
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        elif name == "SOUND SETTINGS":
            s = settings.sound_settings[0]
            self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
            row += 2
            if self._get("USE_SOUNDCARD") == Active.ON:
                for s in settings.sound_settings[1:]:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2

        elif name == "SCREEN SETTINGS":
            s = settings.screen_settings[0]
            self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
            row += 2
            use_screen = self._get("USE_SCREEN")
            if use_screen != ScreenActive.OFF:
                for s in settings.screen_settings[1:]:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2
            if use_screen == ScreenActive.TOUCHSCREEN:
                row += 1
                sub = self.create_and_add_label(
                    "TOUCH SETTINGS", row, C_COL, C_LABEL_W, 2, "black"
                )
                sub.setProperty("type", name)
                row += 2
                for s in settings.touchscreen_settings:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2

        elif name == "CAMERA SETTINGS":
            for s in settings.cam_framerate_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        elif name == "CORRIDOR SETTINGS":
            for s in settings.corridor_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        elif name == "CONTROLLER SETTINGS":
            for s in settings.controller_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            if self._get("BEHAVIOR_CONTROLLER") == ControllerEnum.BPOD:
                row += 1
                sub = self.create_and_add_label(
                    "BPOD SETTINGS", row, C_COL, C_LABEL_W, 2, "black"
                )
                sub.setProperty("type", name)
                row += 2
                for s in settings.bpod_settings:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2

        elif name == "SYNC SETTINGS":
            s = settings.sync_settings[0]
            self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
            row += 2
            sync_type = self._get("SYNC_TYPE")
            if sync_type != SyncType.OFF:
                for s in settings.sync_settings[1:]:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2
            if sync_type == SyncType.SERVER:
                row += 1
                sub = self.create_and_add_label(
                    "SERVER SETTINGS", row, C_COL, C_LABEL_W, 2, "black"
                )
                sub.setProperty("type", name)
                row += 2
                for s in settings.server_settings:
                    self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                    row += 2

        elif name == "TELEGRAM SETTINGS":
            for s in settings.telegram_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            row += 1
            sub = self.create_and_add_label(
                "HOURLY ALARMS", row, C_COL, C_LABEL_W, 2, "black"
            )
            sub.setProperty("type", name)
            row += 2
            for s in settings.hourly_alarm_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            row += 1
            sub = self.create_and_add_label(
                "TWICE-DAILY ALARMS", row, C_COL, C_LABEL_W, 2, "black"
            )
            sub.setProperty("type", name)
            row += 2
            for s in settings.cycle_alarm_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            row += 1
            sub = self.create_and_add_label(
                "END-SESSION ALARMS", row, C_COL, C_LABEL_W, 2, "black"
            )
            sub.setProperty("type", name)
            row += 2
            for s in settings.session_alarm_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        elif name == "DEVICE ADDRESSES":
            for s in settings.device_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        elif name == "ADVANCED SETTINGS":
            for s in settings.extra_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2
            row += 1
            sub = self.create_and_add_label(
                "VISUAL SETTINGS", row, C_COL, C_LABEL_W, 2, "black"
            )
            sub.setProperty("type", name)
            row += 2
            for s in settings.visual_settings:
                self.create_label_and_value(row, C_COL, s, name, width=C_VAL_OFF)
                row += 2

        self._tag_content_widgets(before)

    # ── Layout change guard ────────────────────────────────────────────────────

    def change_layout(self, auto: bool = False) -> bool:
        if auto:
            return True
        elif self.save_button.isEnabled():
            reply = QMessageBox.question(
                self.window,
                "Save changes",
                "Do you want to save the changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                self.save_button.setDisabled(True)
                self.save_button_clicked()
                return True
            elif reply == QMessageBox.Discard:
                self.save_button.setDisabled(True)
                self._pending.clear()
                return True
            else:
                return False
        else:
            return True

    # ── Settings changed / save / restore ─────────────────────────────────────

    def settings_changed(self, value: str = "", key: str = "") -> None:
        manager.changing_settings = True
        self.update_status_label_buttons()
        self.save_button.setEnabled(True)

    def save_button_clicked(self) -> None:
        self.save(changing_project=False)

    def save(self, changing_project: bool) -> None:
        # Flush current section's widgets into _pending so save() sees everything
        self._flush_to_pending()

        sync_directory = self.create_sync_directory()
        self.save_button.setDisabled(True)
        manager.changing_settings = False

        critical_keys = [
            "USE_SOUNDCARD",
            "SOUND_DEVICE",
            "SAMPLERATE",
            "USE_SCREEN",
            "SCREEN_SIZE_MM",
            "TOUCH_RESOLUTION",
            "TOUCH_INTERVAL",
            "TELEGRAM_TOKEN",
            "TELEGRAM_CHAT",
            "HEALTHCHECKS_URL",
            "PROJECT_DIRECTORY",
            "CONTROLLER_PORT",
            "MOTOR1_CORRIDOR_INDEX",
            "MOTOR2_CORRIDOR_INDEX",
            "MOTOR1_BOX_INDEX",
            "MOTOR2_BOX_INDEX",
            "VISIBLE_LIGHT_CORRIDOR_INDEX",
            "IR_LIGHT_CORRIDOR_INDEX",
            "VISIBLE_LIGHT_BOX_INDEX",
            "IR_LIGHT_BOX_INDEX",
            "SCALE_ADDRESS",
            "TEMP_SENSOR_ADDRESS",
            "CAM_BOX_INDEX",
            "CAM_CORRIDOR_INDEX",
            "NO_DETECTION_HOURS",
            "NO_SESSION_HOURS",
            "CAM_CORRIDOR_FRAMERATE",
            "CAM_BOX_FRAMERATE",
            "CAM_BOX_RESOLUTION",
            "DETECTION_DURATION",
            "TIME_BETWEEN_DETECTIONS",
            "MIN_WEIGHT_THRESHOLD",
            "MAX_WEIGHT_THRESHOLD",
            "REPEAT_TARE_TIME",
            "UPDATE_TIME_TABLE",
            "SCREENSAVE_TIME",
            "CORRIDOR_VIDEO_DURATION",
            "BPOD_NET_PORT",
            "BPOD_BAUDRATE",
            "BPOD_SYNC_CHANNEL",
            "BPOD_SYNC_MODE",
            "BEHAVIOR_CONTROLLER",
            "SYNC_TYPE",
            "SAFE_DELETE",
            "MAXIMUM_SYNC_TIME",
            "SYNC_DESTINATION",
            "SYNC_DIRECTORY",
            "SERVER_USER",
            "SERVER_HOST",
            "SERVER_PORT",
            "OLD_VERSION",
            "CHIP_CORRIDOR_ADDRESS",
            "CHIP_BOX_ADDRESS",
            "SCALE_ADDRESS",
            "TEMP_SENSOR_ADDRESS",
        ]

        # Keys in the current section's tracking lists (will be processed with
        # full validation below — skip them from the simple pending pass)
        tracked_keys = {s.key for s in self.line_edits_settings}
        tracked_keys |= {s.key for s in self.time_edits_settings}
        tracked_keys |= {s.key for s in self.toggle_buttons_settings}
        tracked_keys |= {s.key for s in self.list_of_line_edits_settings}
        tracked_keys |= {s.key for s in self.list_of_toggle_buttons_settings}
        tracked_keys.add("SOUND_DEVICE")
        tracked_keys.add("PROJECT_DIRECTORY")

        # Apply values from previously-visited sections (no full validation)
        for key, val in self._pending.items():
            if key in tracked_keys:
                continue
            if key in critical_keys and str(val) != str(settings.get(key)):
                self.critical_changes = True
            if key == "SYNC_DIRECTORY":
                settings.set(key, sync_directory)
            else:
                settings.set(key, val)

        # Apply current section's widgets with full validation
        for i, line_edit in enumerate(self.line_edits):
            s = self.line_edits_settings[i]

            if s.key == "SYNC_DIRECTORY":
                line_edit.setText(sync_directory)

            if s.key in critical_keys and line_edit.text() != str(settings.get(s.key)):
                self.critical_changes = True

            if s.value_type == str:
                value = line_edit.text()
                old_value = str(settings.get("SYSTEM_NAME"))

                if s.key == "SYSTEM_NAME" and value != old_value:
                    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
                        text = (
                            "Are you sure you want to change the system name?\n"
                            + "It is not recommended to do this if you have "
                            + "already started collecting data for an experiment.\n"
                            + "Although the system's data directory will "
                            + " be renamed automatically, some data may already have "
                            + "been saved in CSV files using the previous "
                            + "system name."
                        )
                        if not changing_project:
                            reply = QMessageBox.question(
                                self.window,
                                "SYSTEM_NAME",
                                text,
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No,
                            )
                            if reply == QMessageBox.Yes:
                                settings.set(s.key, value)
                                utils.change_system_directory_settings()
                                self._destroy_content()
                                self.draw_section("DIRECTORY SETTINGS")
                                self.critical_changes = True
                            else:
                                line_edit.setText(old_value)
                        else:
                            settings.set(s.key, value)
                            utils.change_system_directory_settings()
                            self._destroy_content()
                            self.draw_section("DIRECTORY SETTINGS")
                    else:
                        text = "Invalid system name. "
                        text += "It must not contain spaces or special characters."
                        QMessageBox.warning(self.window, "SYSTEM_NAME", text)
                        line_edit.setText(old_value)
                    continue
                settings.set(s.key, value)
            elif s.value_type == float:
                try:
                    value_float = float(line_edit.text())
                    settings.set(s.key, value_float)
                    line_edit.setText(str(value_float))
                except ValueError:
                    line_edit.setText(str(settings.get(s.key)))
            elif s.value_type == int:
                try:
                    value_int = round(float(line_edit.text()))
                    settings.set(s.key, value_int)
                    line_edit.setText(str(value_int))
                except ValueError:
                    line_edit.setText(str(settings.get(s.key)))

        for i, time_edit in enumerate(self.time_edits):
            s = self.time_edits_settings[i]
            value = time_edit.time().toString("HH:mm")
            settings.set(s.key, value)
            manager.cycle_change_detector = time_utils.CycleChangeDetector(
                settings.get("DAYTIME"), settings.get("NIGHTTIME")
            )
            manager.update_cycle()

        for i, toggle_button in enumerate(self.toggle_buttons):
            s = self.toggle_buttons_settings[i]
            if (
                s.key in critical_keys
                and toggle_button.text() != settings.get(s.key).name
            ):
                self.critical_changes = True
            settings.set(s.key, toggle_button.text())

        for i, list_line in enumerate(self.list_of_line_edits):
            s = self.list_of_line_edits_settings[i]
            if s.key in critical_keys:
                for j in range(len(list_line)):
                    if list_line[j].text() != str(settings.get(s.key)[j]):
                        self.critical_changes = True
            if s.value_type == list[int]:
                values = [field.text() for field in list_line]
                with suppress(BaseException):
                    settings.set(s.key, [int(v) for v in values])
            else:
                settings.set(s.key, [field.text() for field in list_line])

        for i, list_toggle in enumerate(self.list_of_toggle_buttons):
            s = self.list_of_toggle_buttons_settings[i]
            settings.set(s.key, [tb.text() for tb in list_toggle])

        try:
            val = self.sound_device_combobox.currentText()
            if val != settings.get("SOUND_DEVICE"):
                self.critical_changes = True
            settings.set("SOUND_DEVICE", val)
        except Exception:
            pass

        cam_corridor.change = True
        cam_box.change = True

        try:
            log.info("Settings modified.")
        except Exception:
            pass

        self._pending.clear()

        if self.critical_changes and not changing_project:
            text = (
                "Some of the setting changes require a system restart to take effect."
            )
            QMessageBox.information(self.window, "Restart", text)
            self.window.reload_app()

        self.critical_changes = False

    def restore_button_clicked(self) -> None:
        reply = QMessageBox.question(
            self.window,
            "Restore factory settings",
            "Are you sure you want to restore to the factory settings?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            log.info("Restoring factory settings.")
            settings.restore_factory_settings()
            self.window.create_settings_layout()

    # ── Widget factory for a single setting ───────────────────────────────────

    def create_label_and_value(
        self, row: int, column: int, s: Setting, type: Any, width: int = 0
    ) -> None:
        label = self.create_and_add_label(
            s.key,
            row,
            column,
            C_LABEL_W,
            2,
            "black",
            bold=False,
            description=s.description,
        )
        label.setProperty("type", type)

        if s.key in ("DAYTIME", "NIGHTTIME"):
            value = self._get(s.key)
            time_edit = self.create_and_add_time_edit(
                value, row, column + width, size4, 2, self.settings_changed
            )
            self.time_edits.append(time_edit)
            self.time_edits_settings.append(s)

        elif s.key == "PROJECT_DIRECTORY":
            value = self._get(s.key)
            path = os.path.dirname(value)
            if not os.path.exists(path):
                utils.create_directories_from_path(path)
            possible_values = [os.path.join(path, name) for name in os.listdir(path)]
            possible_values += ["NEW"]
            index = possible_values.index(value) if value in possible_values else 0
            self.project_directory_combobox = self.create_and_add_combo_box(
                s.key,
                row,
                column + width,
                size2,
                2,
                possible_values,
                index,
                self.change_project_directory,
            )

        elif s.key == "TELEGRAM_TOKEN":
            value = str(self._get(s.key))
            line_edit = self.create_and_add_line_edit(
                value, row, column + width, size2, 2, self.settings_changed
            )
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)

        elif s.key == "SOUND_DEVICE":
            possible_values = get_sound_devices()
            value = self._get(s.key)
            index = possible_values.index(value) if value in possible_values else 0
            self.sound_device_combobox = self.create_and_add_combo_box(
                s.key,
                row,
                column + width,
                size2,
                2,
                possible_values,
                index,
                self.change_sound_device,
            )
            self.sound_device_combobox.setProperty("type", type)

        elif s.value_type in (str, int, float):
            project_dir = self._get("PROJECT_DIRECTORY")
            value = str(self._get(s.key))
            if s.key == "DATA_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    os.path.join(project_dir, "data"),
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "VIDEOS_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    os.path.join(project_dir, "data", "videos"),
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "SESSIONS_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "SYSTEM_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "CODE_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    os.path.join(project_dir, "code"),
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "MEDIA_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    os.path.join(project_dir, "media"),
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "SYNC_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    self.create_sync_directory(),
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "APP_DIRECTORY":
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key in [
                "SERVER_USER",
                "SERVER_HOST",
                "SERVER_PORT",
                "SYNC_DESTINATION",
                "TELEGRAM_CHAT",
                "HEALTHCHECKS_URL",
                "MAXIMUM_SYNC_TIME",
            ]:
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size2,
                    2,
                    self.settings_changed,
                )
            elif s.key == "CONTROLLER_PORT":
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size3,
                    2,
                    self.settings_changed,
                )
            elif s.key in ("SYSTEM_NAME", "SAMPLERATE", "TOUCH_INTERVAL"):
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size4,
                    2,
                    self.settings_changed,
                )
            else:
                line_edit = self.create_and_add_line_edit(
                    value,
                    row,
                    column + width,
                    size1,
                    2,
                    self.settings_changed,
                )
            if s.key in (
                "APP_DIRECTORY",
                "DATA_DIRECTORY",
                "VIDEOS_DIRECTORY",
                "SESSIONS_DIRECTORY",
                "SYSTEM_DIRECTORY",
                "CODE_DIRECTORY",
                "MEDIA_DIRECTORY",
                "SYNC_DIRECTORY",
            ):
                line_edit.setReadOnly(True)
                line_edit.setDisabled(True)
            line_edit.setProperty("type", type)
            self.line_edits.append(line_edit)
            self.line_edits_settings.append(s)

        elif s.value_type == list[int]:
            values = self._get(s.key)
            line_edits = []
            for i, v in enumerate(values):
                line_edit = self.create_and_add_line_edit(
                    str(v),
                    row,
                    column + width + small_box * i,
                    small_box,
                    2,
                    self.settings_changed,
                )
                if s.key in ("SCREEN_RESOLUTION", "BPOD_TARGET_FIRMWARE"):
                    line_edit.setReadOnly(True)
                    line_edit.setDisabled(True)
                line_edit.setProperty("type", type)
                line_edits.append(line_edit)
            self.list_of_line_edits.append(line_edits)
            self.list_of_line_edits_settings.append(s)

        elif s.value_type == list[Active]:
            values_list: list[Active] = self._get(s.key)
            toggle_buttons = []
            for i, v in enumerate(values_list):
                possible_values = settings.get_values(s.key)
                index = self._get_indices(s.key)[i]
                toggle_button = self.create_and_add_toggle_button(
                    s.key,
                    row,
                    column + width + mini_box * i,
                    mini_box,
                    2,
                    possible_values,
                    index,
                    self.settings_changed,
                    s.description,
                )
                toggle_button.setProperty("type", type)
                toggle_buttons.append(toggle_button)
            self.list_of_toggle_buttons.append(toggle_buttons)
            self.list_of_toggle_buttons_settings.append(s)

        else:
            possible_values = settings.get_values(s.key)
            index = self._get_index(s.key)
            size_to_use = (
                size4
                if s.key
                in (
                    "DETECTION_COLOR",
                    "USE_SOUNDCARD",
                    "USE_SCREEN",
                    "BEHAVIOR_CONTROLLER",
                )
                else size1
            )
            toggle_button = self.create_and_add_toggle_button(
                s.key,
                row,
                column + width,
                size_to_use,
                2,
                possible_values,
                index,
                self.toggle_button_changed,
                s.description,
            )
            toggle_button.setProperty("type", type)
            self.toggle_buttons.append(toggle_button)
            self.toggle_buttons_settings.append(s)

    # ── Toggle button handler ──────────────────────────────────────────────────

    def toggle_button_changed(self, value: str, key: str) -> None:
        self._pending[key] = value
        self.settings_changed(value, key)
        if _CONDITIONAL_KEYS.get(key) == self._current_section:
            self._destroy_content()
            self.draw_section(self._current_section)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def create_sync_directory(self) -> str:
        directory = os.path.basename(
            self._pending.get("PROJECT_DIRECTORY", settings.get("PROJECT_DIRECTORY"))
        )
        sync_dest = self._pending.get(
            "SYNC_DESTINATION", settings.get("SYNC_DESTINATION")
        )
        # Also check current section's line_edits for SYNC_DESTINATION
        for i, s in enumerate(self.line_edits_settings):
            if s.key == "SYNC_DESTINATION":
                sync_dest = self.line_edits[i].text()
                break
        return os.path.join(sync_dest, directory + "_data")

    def change_sound_device(self, value: str, key: str) -> None:
        self.settings_changed(value, key)

    def remove(self, name: str) -> None:
        """Legacy remove — kept for compatibility."""
        for i in reversed(range(len(self.line_edits))):
            if self.line_edits[i].property("type") == name:
                self.line_edits.pop(i)
                self.line_edits_settings.pop(i)
        for i in reversed(range(len(self.time_edits))):
            if self.time_edits[i].property("type") == name:
                self.time_edits.pop(i)
                self.time_edits_settings.pop(i)
        for i in reversed(range(len(self.toggle_buttons))):
            if self.toggle_buttons[i].property("type") == name:
                self.toggle_buttons.pop(i)
                self.toggle_buttons_settings.pop(i)
        for i in reversed(range(len(self.list_of_line_edits))):
            if self.list_of_line_edits[i][0].property("type") == name:
                self.list_of_line_edits.pop(i)
                self.list_of_line_edits_settings.pop(i)
        for i in reversed(range(len(self.list_of_toggle_buttons))):
            if self.list_of_toggle_buttons[i][0].property("type") == name:
                self.list_of_toggle_buttons.pop(i)
                self.list_of_toggle_buttons_settings.pop(i)
        self.delete_optional_widgets(name)

    def change_project_directory(self, value: str, key: str) -> None:
        if value == "NEW":
            text, ok = QInputDialog.getText(
                self.window,
                "NEW",
                "Enter the name of the new project. The system will restart.",
            )
            if ok and text:
                old_project = self._get("PROJECT_DIRECTORY")
                project_dir = os.path.dirname(old_project)
                path = os.path.join(project_dir, text)
                self.save(changing_project=True)
                if self.create_project_directory(path):
                    utils.change_directory_settings(path)
                    self.window.reload_app()
                    return
            self.project_directory_combobox.blockSignals(True)
            self.project_directory_combobox.setCurrentText(
                self._get("PROJECT_DIRECTORY")
            )
            self.project_directory_combobox.blockSignals(False)
        else:
            text = (
                "Are you sure you want to change the project directory? The system "
                + "will restart."
            )
            reply = QMessageBox.question(
                self.window,
                "Change project directory",
                text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.save(changing_project=True)
                utils.change_directory_settings(value)
                self.window.reload_app()
            else:
                self.project_directory_combobox.blockSignals(True)
                self.project_directory_combobox.setCurrentText(
                    self._get("PROJECT_DIRECTORY")
                )
                self.project_directory_combobox.blockSignals(False)

    def create_project_directory(self, path: str) -> bool:
        return utils.create_directories_from_path(path)

    def update_gui(self) -> None:
        self.update_status_label_buttons()
