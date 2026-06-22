from __future__ import annotations

import asyncio
import os
import threading
from functools import partial
from typing import Optional

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from village.custom_classes.calibration_base import CalibrationBase

try:
    from bleak import BleakScanner

    _BLEAK_AVAILABLE = True
except Exception:
    _BLEAK_AVAILABLE = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_BRAIN_MAP_PATH = os.path.join(_HERE, "brainmap.png")

_PARAM_LABELS: dict[str, tuple[str, str]] = {
    "sequence_length": ("Sequence Length", "count"),
    "led_selection": ("LED Selection", "bitmap"),
    "duration": ("Duration", "ms"),
    "period": ("Period", "ms"),
    "pulse_width": ("Pulse Width", "ms"),
    "amplitude": ("Amplitude", "%"),
    "pwm_frequency": ("PWM Frequency", "Hz"),
    "ramp_up": ("Ramp Up", "ms"),
    "ramp_down": ("Ramp Down", "ms"),
}


# --------------------------------------------------------------------------- #
# Brain-map widget
# --------------------------------------------------------------------------- #


class _BrainMapWidget(QWidget):
    """Interactive 64-LED grid over a brain map image.

    Click or drag to toggle LEDs. Calls on_changed(selection_int) on each
    change, where selection_int is the uint64 LED Selection value.
    """

    def __init__(self, on_changed, parent=None):
        super().__init__(parent)
        self.selection: int = 0
        self._on_changed = on_changed
        self._bg: Optional[QPixmap] = None
        if os.path.exists(_BRAIN_MAP_PATH):
            px = QPixmap(_BRAIN_MAP_PATH)
            if not px.isNull():
                self._bg = px
        self.setMinimumSize(220, 180)
        self.setCursor(Qt.CrossCursor)

    # ── LED geometry ────────────────────────────────────────────────────────

    def _led_rects(self) -> list[tuple[int, int, int, int, int]]:
        """Return [(x, y, w, h, bit), ...] scaled to current widget size."""
        W, H = self.width(), self.height()
        sx = W / 358
        sy = H / 300
        xs = int(14 * sx)
        ys = int(40 * sy)
        cx = int(172 * sx)
        cy = int(10 * sy) - 1
        lw = max(6, int(12 * sx))
        lh = max(9, int(23 * sy))

        # Port the JS ledPixelMap exactly
        pm: dict[int, tuple[int, int]] = {
            0: (cx - 11 * xs + int(14 * sx) + 4, cy + 5 * ys),
            1: (cx - 5 * xs + int(2 * sx) + 3, cy),
            2: (cx - 3 * xs + int(1 * sx) + 2, cy),
            3: (cx - 1 * xs + 1, cy),
            4: (cx + 1 * xs, cy),
            5: (cx + 3 * xs - int(1 * sx) - 1, cy),
            6: (cx + 5 * xs - int(2 * sx) - 2, cy),
            7: (cx + 11 * xs - int(14 * sx) - 3, cy + 5 * ys),
        }
        for r in range(1, 7):
            b = 8 * r
            pm[b + 0] = (cx - 7 * xs + int(5 * sx) + 4, cy + r * ys)
            pm[b + 1] = (cx - 5 * xs + int(2 * sx) + 3, cy + r * ys)
            pm[b + 2] = (cx - 3 * xs + int(1 * sx) + 2, cy + r * ys)
            pm[b + 3] = (cx - 1 * xs + 1, cy + r * ys)
            pm[b + 4] = (cx + 1 * xs, cy + r * ys)
            pm[b + 5] = (cx + 3 * xs - int(1 * sx) - 1, cy + r * ys)
            pm[b + 6] = (cx + 5 * xs - int(2 * sx) - 2, cy + r * ys)
            pm[b + 7] = (cx + 7 * xs - int(5 * sx) - 3, cy + r * ys)
        xl = cx - 9 * xs + int(8 * sx) + 4
        xr = cx + 9 * xs - int(8 * sx) - 3
        for i, yo in enumerate([6, 5, 4, 3]):
            pm[56 + i] = (xl, cy + yo * ys)
        for i, yo in enumerate([3, 4, 5, 6]):
            pm[60 + i] = (xr, cy + yo * ys)

        return [(x, y, lw, lh, bit) for bit, (x, y) in pm.items()]

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        if self._bg and not self._bg.isNull():
            scaled = self._bg.scaled(
                self.width(),
                self.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            p.drawPixmap(
                (self.width() - scaled.width()) // 2,
                (self.height() - scaled.height()) // 2,
                scaled,
            )
        else:
            p.fillRect(self.rect(), QColor("#ccdece"))

        font = QFont("Arial", max(6, int(8 * self.width() / 358)))
        font.setBold(True)
        p.setFont(font)

        for x, y, lw, lh, bit in self._led_rects():
            selected = bool(self.selection & (1 << bit))
            if selected:
                p.fillRect(x, y, lw, lh, QColor(0, 190, 255, 200))
            p.setPen(QColor(0, 150, 210))
            p.drawRect(x, y, lw, lh)
            p.setPen(QColor(0, 0, 0))
            p.drawText(QRect(x, y, lw, lh), Qt.AlignCenter, str(bit + 1))

        p.end()

    # ── Mouse ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        mx, my = event.x(), event.y()
        for x, y, lw, lh, bit in self._led_rects():
            if x <= mx <= x + lw and y <= my <= y + lh:
                self.selection ^= 1 << bit
                self.update()
                self._on_changed(self.selection)
                return

    def set_selection(self, value: int) -> None:
        self.selection = value
        self.update()


# --------------------------------------------------------------------------- #
# Calibration panel
# --------------------------------------------------------------------------- #


class OptoGridCalibration(CalibrationBase):
    name = "optogrid_calibration"

    def __init__(self) -> None:
        super().__init__()
        # scan state
        self._scanning = False
        self._scan_done = False
        self._scan_results: list[tuple[str, str]] = []
        self._scan_error = ""
        # connect/read state
        self._connecting = False
        self._connect_done = False
        self._connect_name = ""
        self._connect_params: Optional[dict[str, str]] = None
        self._battery_mv: Optional[int] = None
        self._connect_error = ""
        # brain-map state
        self._led_selection: int = 0

    @classmethod
    def is_active(cls) -> bool:
        return True

    # ── draw ────────────────────────────────────────────────────────────────

    def draw(self) -> None:
        # ── left column (cols 1-82) ──────────────────────────────────────────
        self.layout.create_and_add_label("OptoGrid Calibration", 1, 1, 55, 2, "black")
        self.scan_button = self.layout.create_and_add_button(
            "SCAN",
            3,
            1,
            12,
            2,
            self._start_scan,
            "Scan for nearby BLE devices (~5 s)",
            "lightblue",
        )
        self.status_label = self.layout.create_and_add_label(
            "", 3, 15, 66, 2, "gray", bold=False
        )

        # scan results (rows 5-21)
        self._results_widget = QWidget()
        self._results_widget.setStyleSheet("background-color: #F5F5F5;")
        self._results_vbox = QVBoxLayout(self._results_widget)
        self._results_vbox.setAlignment(Qt.AlignTop)
        self._results_vbox.setSpacing(4)
        self._results_vbox.setContentsMargins(8, 8, 8, 8)
        scan_scroll = QScrollArea()
        scan_scroll.setWidget(self._results_widget)
        scan_scroll.setWidgetResizable(True)
        scan_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(scan_scroll, 5, 1, 17, 82)

        # device info (rows 22-43)
        self._info_widget = QWidget()
        self._info_widget.setStyleSheet("background-color: #EEF4FF;")
        self._info_vbox = QVBoxLayout(self._info_widget)
        self._info_vbox.setAlignment(Qt.AlignTop)
        self._info_vbox.setSpacing(3)
        self._info_vbox.setContentsMargins(8, 6, 8, 6)
        placeholder = QLabel("Click a device name to read its parameters")
        placeholder.setStyleSheet("color:#888; font-style:italic;")
        self._info_vbox.addWidget(placeholder)
        info_scroll = QScrollArea()
        info_scroll.setWidget(self._info_widget)
        info_scroll.setWidgetResizable(True)
        info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(info_scroll, 22, 1, 22, 82)

        # ── right column: brain map (cols 84-170) ────────────────────────────
        self.layout.create_and_add_label(
            "LED Brain Map — click to toggle LEDs", 1, 84, 70, 2, "black"
        )
        self._brain_map = _BrainMapWidget(self._on_brain_map_changed)
        self.layout.addWidget(self._brain_map, 3, 84, 35, 87)

        self.layout.create_and_add_label("LED Selection:", 38, 84, 20, 2, "black")
        self._led_value_label = self.layout.create_and_add_label(
            "0", 38, 106, 55, 2, "steelblue"
        )
        self.layout.create_and_add_button(
            "Clear",
            38,
            162,
            9,
            2,
            self._clear_brain_map,
            "Clear all LED selections",
            "lightgray",
        )
        self.layout.create_and_add_label(
            "Copy the value above into LED Selection in your task settings.",
            41,
            84,
            87,
            2,
            "gray",
            bold=False,
        )

    # ── Scan ────────────────────────────────────────────────────────────────

    def _start_scan(self) -> None:
        if self._scanning or self._connecting:
            return
        if not _BLEAK_AVAILABLE:
            self.status_label.setText("bleak not installed — cannot scan")
            return
        self._scanning = True
        self._scan_done = False
        self._scan_results = []
        self._scan_error = ""
        self.scan_button.setEnabled(False)
        self.status_label.setText("Scanning… (~5 seconds)")
        self._clear_scan_list()
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                devices = loop.run_until_complete(BleakScanner.discover(timeout=5.0))
                self._scan_results = [(d.name or "Unknown", d.address) for d in devices]
            finally:
                loop.close()
        except Exception as e:
            self._scan_error = str(e)
        self._scan_done = True

    def _populate_scan_list(self) -> None:
        self._clear_scan_list()
        self.scan_button.setEnabled(True)
        if self._scan_error:
            self.status_label.setText(f"Scan error: {self._scan_error}")
            return
        if not self._scan_results:
            self.status_label.setText("No BLE devices found")
            return
        self.status_label.setText(
            f"Found {len(self._scan_results)} device(s) — click a name to read params"
        )
        for name, address in self._scan_results:
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(4, 2, 4, 2)
            hl.setSpacing(12)

            name_btn = QPushButton(name)
            name_btn.setFixedWidth(230)
            name_btn.setStyleSheet(
                "text-align:left; font-weight:bold; color:#1a4a8a;"
                " background:transparent; border:none; padding:2px;"
            )
            name_btn.setCursor(Qt.PointingHandCursor)
            name_btn.clicked.connect(partial(self._start_connect, name, address))

            addr_lbl = QLabel(address)
            addr_lbl.setFixedWidth(195)
            addr_lbl.setStyleSheet("color:#444; font-family:monospace; font-size:12px;")

            copy_btn = QPushButton("Copy")
            copy_btn.setFixedWidth(58)
            copy_btn.setStyleSheet(
                "background-color:#b0c4de; border-radius:3px; padding:2px 5px;"
            )
            copy_btn.clicked.connect(partial(self._copy_address, address))

            hl.addWidget(name_btn)
            hl.addWidget(addr_lbl)
            hl.addWidget(copy_btn)
            hl.addStretch()
            self._results_vbox.addWidget(row)

    def _clear_scan_list(self) -> None:
        while self._results_vbox.count():
            item = self._results_vbox.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _copy_address(self, address: str) -> None:
        try:
            cb = QApplication.clipboard()
            if cb is not None:
                cb.setText(address)
                self.status_label.setText(f"Copied: {address}")
        except Exception:
            self.status_label.setText("Could not access clipboard")

    # ── Connect & read params ──────────────────────────────────────────────

    def _start_connect(self, name: str, address: str) -> None:
        if self._connecting or self._scanning:
            return
        self._connecting = True
        self._connect_done = False
        self._connect_name = name
        self._connect_params = None
        self._connect_error = ""
        self.status_label.setText(f"Connecting to {name}…")
        self._set_info_message(f"Connecting to {name}…")
        threading.Thread(
            target=self._run_connect, args=(name, address), daemon=True
        ).start()

    def _run_connect(self, name: str, address: str) -> None:
        try:
            from village.devices.optogrid import OptoGrid

            og = OptoGrid(device_name=name)
            try:
                ok = og.connect(identifier=address, timeout=10.0)
                if not ok:
                    self._connect_error = f"Could not connect to {name}"
                    return
                self._battery_mv = og.read_battery_mv()
                self._connect_params = og.read_params() or {}
            finally:
                try:
                    og.disconnect()
                except Exception:
                    pass
                og.stop()
        except Exception as e:
            self._connect_error = str(e)
        finally:
            self._connect_done = True

    def _populate_device_info(self) -> None:
        self.status_label.setText(f"{self._connect_name} — parameters loaded")
        params = self._connect_params or {}
        self._clear_info()

        # header
        device_id = params.get("device_id", self._connect_name)
        firmware = params.get("firmware", "?")
        hdr = QLabel(f"{device_id}   fw: {firmware}")
        hdr.setStyleSheet("font-weight:bold; color:#222; font-size:13px;")
        self._info_vbox.addWidget(hdr)

        # battery
        bat_mv = self._battery_mv
        if bat_mv is not None:
            pct = max(0, min(100, int((bat_mv - 3500) / 700 * 100)))
            color = "#44aa44" if pct > 30 else "#cc4444"
            stop = f"{pct / 100:.3f}"
            bar_style = (
                f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {color},stop:{stop} {color},"
                f"stop:{min(1.0, pct/100+0.001):.3f} #ddd,stop:1 #ddd);"
                f"border:1px solid #999; border-radius:3px;"
            )
            bat_row = QWidget()
            bl = QHBoxLayout(bat_row)
            bl.setContentsMargins(0, 3, 0, 3)
            bl.addWidget(QLabel(f"Battery:  {bat_mv} mV  ({pct}%)"))
            bar = QLabel()
            bar.setFixedSize(100, 14)
            bar.setStyleSheet(bar_style)
            bl.addWidget(bar)
            bl.addStretch()
            self._info_vbox.addWidget(bat_row)

        # separator
        sep = QLabel("─" * 44)
        sep.setStyleSheet("color:#bbb;")
        self._info_vbox.addWidget(sep)

        # opto params
        for key, (label, unit) in _PARAM_LABELS.items():
            val = params.get(key, "—")
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 1, 0, 1)
            hl.setSpacing(8)
            name_lbl = QLabel(label)
            name_lbl.setFixedWidth(135)
            name_lbl.setStyleSheet("color:#333;")
            val_lbl = QLabel(str(val))
            val_lbl.setStyleSheet(
                "font-family:monospace; color:#003080; font-weight:bold;"
            )
            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet("color:#888; font-size:11px;")
            hl.addWidget(name_lbl)
            hl.addWidget(val_lbl)
            hl.addWidget(unit_lbl)
            hl.addStretch()
            self._info_vbox.addWidget(row)

    def _clear_info(self) -> None:
        while self._info_vbox.count():
            item = self._info_vbox.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _set_info_message(self, msg: str) -> None:
        self._clear_info()
        lbl = QLabel(msg)
        lbl.setStyleSheet("color:#666; font-style:italic;")
        self._info_vbox.addWidget(lbl)

    # ── Brain map ────────────────────────────────────────────────────────────

    def _on_brain_map_changed(self, selection: int) -> None:
        self._led_selection = selection
        self._led_value_label.setText(str(selection))

    def _clear_brain_map(self) -> None:
        self._led_selection = 0
        self._brain_map.set_selection(0)
        self._led_value_label.setText("0")

    # ── update_gui ───────────────────────────────────────────────────────────

    def update_gui(self) -> None:
        if self._scanning and self._scan_done:
            self._scanning = False
            self._populate_scan_list()
        if self._connecting and self._connect_done:
            self._connecting = False
            if self._connect_error:
                self.status_label.setText(f"Error: {self._connect_error}")
                self._set_info_message(f"Error: {self._connect_error}")
            else:
                self._populate_device_info()
