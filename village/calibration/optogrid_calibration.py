from __future__ import annotations

import asyncio
import math
import threading
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint, QRect, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap, QPolygon
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from village.custom_classes.calibration_base import CalibrationBase
from village.scripts.time_utils import time_utils
from village.settings import settings

try:
    from bleak import BleakScanner

    _BLEAK_AVAILABLE = True
except Exception:
    _BLEAK_AVAILABLE = False

if TYPE_CHECKING:
    # OptoGrid is imported lazily at runtime (see _run_connect etc.) to
    # avoid pulling in bleak/ahrs at module import time when not needed --
    # this is a type-checking-only import, no runtime cost/dependency.
    from village.devices.optogrid import OptoGrid

_BRAIN_MAP_PATH = Path(__file__).resolve().parent / "brainmap.png"

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

    def __init__(
        self, on_changed: Callable[[int], None], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.selection: int = 0
        # uLED check mask from read_uled_check(): bit=1 means that LED
        # measured a normal drive current, bit=0 means it's broken/not
        # responding. All-ones ("all intact") until a scan says otherwise.
        self.check_mask: int = (1 << 64) - 1
        self._on_changed = on_changed
        self._bg: QPixmap | None = None
        if _BRAIN_MAP_PATH.exists():
            px = QPixmap(str(_BRAIN_MAP_PATH))
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

            broken = not (self.check_mask & (1 << bit))
            if broken:
                p.setPen(QColor(220, 0, 0))
                p.drawLine(x, y, x + lw, y + lh)
                p.drawLine(x, y + lh, x + lw, y)

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

    def set_check_mask(self, value: int) -> None:
        self.check_mask = value
        self.update()


# --------------------------------------------------------------------------- #
# Live IMU view: a wireframe "3D" box (manual rotation + orthographic
# projection, no OpenGL) and a raw-data plot, both plain QPainter. Cheap by
# construction (no Three.js-equivalent, no matplotlib) and kept cheap in use
# by decoupling redraw rate from the ~100 Hz BLE sample rate -- see
# _LiveIMUDialog's timer.
# --------------------------------------------------------------------------- #

_BOX_VERTICES = [
    (-1, -1.5, -0.3),
    (1, -1.5, -0.3),
    (1, 1.5, -0.3),
    (-1, 1.5, -0.3),
    (-1, -1.5, 0.3),
    (1, -1.5, 0.3),
    (1, 1.5, 0.3),
    (-1, 1.5, 0.3),
]
_BOX_EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]  # fmt: skip


class _Orientation3DWidget(QWidget):
    """Wireframe box rotated by roll/pitch/yaw. Rotation is three plain 3x3
    matrix multiplications done by hand (8 vertices -- negligible cost),
    projected orthographically with a cheap linear depth scale standing in
    for perspective. No OpenGL context needed, so no GPU/driver dependency
    on whatever's running the Pi.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.setMinimumSize(160, 160)

    def set_orientation(self, roll: float, pitch: float, yaw: float) -> None:
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.update()

    def _rotated_vertices(self) -> list[tuple[float, float, float]]:
        r, p, y = (
            math.radians(self.roll),
            math.radians(self.pitch),
            math.radians(self.yaw),
        )
        cr, sr = math.cos(r), math.sin(r)
        cp, sp = math.cos(p), math.sin(p)
        cy, sy = math.cos(y), math.sin(y)
        out = []
        for x0, y0, z0 in _BOX_VERTICES:
            # roll about X, then pitch about Y, then yaw about Z
            x1, y1, z1 = x0, y0 * cr - z0 * sr, y0 * sr + z0 * cr
            x2, y2, z2 = x1 * cp + z1 * sp, y1, -x1 * sp + z1 * cp
            x3, y3, z3 = x2 * cy - y2 * sy, x2 * sy + y2 * cy, z2
            out.append((x3, y3, z3))
        return out

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(250, 250, 252))

        cx, cy = self.width() / 2, self.height() / 2
        scale = min(self.width(), self.height()) / 5.0

        pts = []
        for x, y, z in self._rotated_vertices():
            depth = 1.0 + z * 0.15  # cheap pseudo-perspective, not a real projection
            pts.append((cx + x * scale * depth, cy - y * scale * depth, z))

        front_z = sum(pts[i][2] for i in range(4)) / 4
        if front_z < 0:
            poly = QPolygon([QPoint(int(pts[i][0]), int(pts[i][1])) for i in range(4)])
            p.setBrush(QColor(120, 170, 230, 110))
            p.setPen(Qt.NoPen)
            p.drawPolygon(poly)

        p.setPen(QColor(40, 90, 160))
        for a, b in _BOX_EDGES:
            p.drawLine(int(pts[a][0]), int(pts[a][1]), int(pts[b][0]), int(pts[b][1]))

        p.setPen(QColor(120, 120, 120))
        p.drawText(
            4,
            self.height() - 6,
            f"r={self.roll:.0f} p={self.pitch:.0f} y={self.yaw:.0f}",
        )
        p.end()


class _IMUPlotWidget(QWidget):
    """Rolling raw-data plot -- draws whatever's in the given history (a
    list of dicts with acc_x/y/z, gyro_x/y/z) as polylines. Plain QPainter,
    no matplotlib/pyqtgraph: for ~500 points this draws faster and far
    lighter than matplotlib's per-frame figure re-layout, and adds no new
    dependency. Only actually redrawn when the panel's poll timer calls
    set_data(), not per incoming BLE sample -- that decoupling is what
    keeps this cheap regardless of drawing technique.
    """

    _SERIES = [
        ("acc_x", QColor(200, 60, 60)),
        ("acc_y", QColor(60, 160, 60)),
        ("acc_z", QColor(60, 60, 200)),
        ("gyro_x", QColor(220, 140, 60)),
        ("gyro_y", QColor(160, 60, 160)),
        ("gyro_z", QColor(60, 160, 160)),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history: list[dict] = []
        self.setMinimumSize(280, 160)

    def set_data(self, history: list[dict]) -> None:
        self._history = history
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        p.setPen(QColor(210, 210, 210))
        p.drawRect(0, 0, self.width() - 1, self.height() - 1)

        n = len(self._history)
        if n < 2:
            p.setPen(QColor(150, 150, 150))
            p.drawText(self.rect(), Qt.AlignCenter, "No IMU data — turn IMU ON")
            p.end()
            return

        w, h = self.width(), self.height()
        margin = 4
        for key, color in self._SERIES:
            values = [row.get(key) for row in self._history]
            present = [v for v in values if v is not None]
            if not present:
                continue
            vmin, vmax = min(present), max(present)
            span = max(vmax - vmin, 1)
            path = QPainterPath()
            started = False
            for i, v in enumerate(values):
                if v is None:
                    continue
                x = margin + (w - 2 * margin) * i / (n - 1)
                y = h - margin - (h - 2 * margin) * (v - vmin) / span
                if not started:
                    path.moveTo(x, y)
                    started = True
                else:
                    path.lineTo(x, y)
            p.setPen(color)
            p.drawPath(path)

        ly = 12
        for key, color in self._SERIES:
            p.setPen(color)
            p.drawText(6, ly, key)
            ly += 12
        p.end()


class _LiveIMUDialog(QDialog):
    """Non-modal window with the orientation box + raw plot, polled from
    og.imu_raw_history on a throttled timer. Redrawing at ~10 Hz instead of
    the IMU's ~100 Hz sample rate is the main thing keeping this cheap --
    it applies regardless of which of the two widgets' drawing technique is
    used, so it's done here once rather than in each widget.
    """

    def __init__(self, og: OptoGrid, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Live IMU")
        self._og = og
        layout = QHBoxLayout(self)
        self._orientation_widget = _Orientation3DWidget()
        self._plot_widget = _IMUPlotWidget()
        layout.addWidget(self._orientation_widget)
        layout.addWidget(self._plot_widget, 1)
        self.resize(560, 260)

        self._timer = QTimer(self)
        self._timer.setInterval(100)  # 10 Hz redraw, decoupled from the ~100 Hz feed
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    def _poll(self) -> None:
        history = list(self._og.imu_raw_history)
        if history:
            last = history[-1]
            roll, pitch, yaw = last.get("roll"), last.get("pitch"), last.get("yaw")
            if roll is not None and pitch is not None and yaw is not None:
                self._orientation_widget.set_orientation(roll, pitch, yaw)
        self._plot_widget.set_data(history)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().closeEvent(event)


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
        # connect/read state -- once connected, self._og stays open (and the
        # background thread it owns stays alive) until _start_disconnect()
        # or change_layout() closes it, so Program/Trigger/SHAM/STATUS/IMU
        # below can reuse the same live connection instead of reconnecting
        # for every single action.
        self._og: OptoGrid | None = None
        self._connected = False
        self._connecting = False
        self._connect_done = False
        self._connect_name = ""
        self._connect_address = ""
        self._connect_params: dict[str, str] | None = None
        self._battery_mv: int | None = None
        self._connect_error = ""
        self._sham_on = False
        self._status_on = False
        # brain-map state
        self._led_selection: int = 0
        # program (write) state -- self._param_edits maps OptoSetting field
        # name -> its QLineEdit in the device info panel, populated by
        # _populate_device_info(). Empty until a device has been read once.
        self._param_edits: dict[str, QLineEdit] = {}
        self._programming = False
        self._program_done = False
        self._program_error = ""
        # shared state for the quick one-shot actions (trigger/sham/status/imu/
        # uled scan/last stim). on_success runs on the Qt thread from
        # update_gui(), after fn() (background thread, no widget touches) --
        # for actions that need to update a widget (e.g. the brain map) with
        # their result, not just report success/failure.
        self._busy = False
        self._action_done = False
        self._action_error = ""
        self._action_message = ""
        self._action_on_success: Callable[[], None] | None = None
        self._uled_mask: int | None = None
        self._last_stim_ms: int | None = None
        # disconnect state
        self._disconnecting = False
        self._disconnect_done = False

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
        self._connect_address = address
        self._connect_params = None
        self._connect_error = ""
        self.status_label.setText(f"Connecting to {name}…")
        self._set_info_message(f"Connecting to {name}…")
        threading.Thread(
            target=self._run_connect, args=(name, address), daemon=True
        ).start()

    def _run_connect(self, name: str, address: str) -> None:
        og = None
        try:
            from village.devices.optogrid import OptoGrid

            # A real session/filename (not the "" defaults) so that, if IMU
            # logging gets toggled on from this panel, its CSV lands
            # somewhere sane instead of next to whatever the cwd happens to
            # be at the time.
            og = OptoGrid(
                device_name=name,
                sessions_directory=settings.get("SYSTEM_DIRECTORY"),
                filename=f"optogrid_calibration_{time_utils.now_string_for_filename()}",
            )
            ok = og.connect(identifier=address, timeout=10.0)
            if not ok:
                self._connect_error = f"Could not connect to {name}"
                og.stop()
                return
            self._battery_mv = og.read_battery_mv()
            self._connect_params = og.read_params() or {}
            # Stays connected -- Program/Trigger/SHAM/STATUS/IMU below reuse
            # this same OptoGrid instead of reconnecting for every action.
            self._og = og
            self._sham_on = False
            self._status_on = False
        except Exception as e:
            self._connect_error = str(e)
            if og is not None:
                try:
                    og.stop()
                except Exception:
                    pass
        finally:
            self._connect_done = True

    def _populate_device_info(self) -> None:
        self.status_label.setText(f"{self._connect_name} — parameters loaded")
        params = self._connect_params or {}
        self._clear_info()

        # header
        device_id = params.get("device_id", self._connect_name)
        firmware = params.get("firmware", "?")
        hdr_row = QWidget()
        hdr_hl = QHBoxLayout(hdr_row)
        hdr_hl.setContentsMargins(0, 0, 0, 0)
        hdr = QLabel(f"{device_id}   fw: {firmware}")
        hdr.setStyleSheet("font-weight:bold; color:#222; font-size:13px;")
        hdr_hl.addWidget(hdr)
        hdr_hl.addStretch()
        self.disconnect_button = QPushButton("DISCONNECT")
        self.disconnect_button.setStyleSheet(
            "background-color:#e0a0a0; font-weight:bold; padding:2px 8px;"
        )
        self.disconnect_button.setCursor(Qt.PointingHandCursor)
        self.disconnect_button.clicked.connect(self._start_disconnect)
        hdr_hl.addWidget(self.disconnect_button)
        self._info_vbox.addWidget(hdr_row)

        # quick actions: trigger + the three toggle LEDs
        actions_row = QWidget()
        al = QHBoxLayout(actions_row)
        al.setContentsMargins(0, 4, 0, 4)
        al.setSpacing(6)
        self.trigger_button = QPushButton("TRIGGER")
        self.trigger_button.setCursor(Qt.PointingHandCursor)
        self.trigger_button.clicked.connect(self._start_trigger)
        al.addWidget(self.trigger_button)
        self.sham_button = QPushButton("SHAM")
        self.sham_button.setCursor(Qt.PointingHandCursor)
        self.sham_button.clicked.connect(self._start_toggle_sham)
        al.addWidget(self.sham_button)
        self.status_button = QPushButton("STATUS")
        self.status_button.setCursor(Qt.PointingHandCursor)
        self.status_button.clicked.connect(self._start_toggle_status)
        al.addWidget(self.status_button)
        self.imu_button = QPushButton("IMU")
        self.imu_button.setCursor(Qt.PointingHandCursor)
        self.imu_button.clicked.connect(self._start_toggle_imu)
        al.addWidget(self.imu_button)
        self.uled_scan_button = QPushButton("uLED SCAN")
        self.uled_scan_button.setCursor(Qt.PointingHandCursor)
        self.uled_scan_button.clicked.connect(self._start_uled_scan)
        al.addWidget(self.uled_scan_button)
        self.last_stim_button = QPushButton("LAST STIM")
        self.last_stim_button.setCursor(Qt.PointingHandCursor)
        self.last_stim_button.clicked.connect(self._start_read_last_stim)
        al.addWidget(self.last_stim_button)
        self.live_imu_button = QPushButton("LIVE IMU VIEW")
        self.live_imu_button.setCursor(Qt.PointingHandCursor)
        self.live_imu_button.clicked.connect(self._open_live_imu)
        al.addWidget(self.live_imu_button)
        al.addStretch()
        self._info_vbox.addWidget(actions_row)
        self._update_toggle_button_styles()

        self.action_status_label = QLabel("")
        self.action_status_label.setStyleSheet("color:#666; font-style:italic;")
        self._info_vbox.addWidget(self.action_status_label)

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

        # opto params -- editable, so they double as the "program" form
        self._param_edits = {}
        for key, (label, unit) in _PARAM_LABELS.items():
            val = params.get(key, "—")
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 1, 0, 1)
            hl.setSpacing(8)
            name_lbl = QLabel(label)
            name_lbl.setFixedWidth(135)
            name_lbl.setStyleSheet("color:#333;")
            val_edit = QLineEdit(str(val))
            val_edit.setFixedWidth(160)
            val_edit.setStyleSheet(
                "font-family:monospace; color:#003080; font-weight:bold;"
            )
            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet("color:#888; font-size:11px;")
            hl.addWidget(name_lbl)
            hl.addWidget(val_edit)
            hl.addWidget(unit_lbl)
            hl.addStretch()
            self._info_vbox.addWidget(row)
            self._param_edits[key] = val_edit
        # brain map may already have a selection from before this device was
        # read -- keep the led_selection field in sync with it.
        if self._led_selection:
            self._param_edits["led_selection"].setText(str(self._led_selection))

        program_row = QWidget()
        pl = QHBoxLayout(program_row)
        pl.setContentsMargins(0, 6, 0, 0)
        self.program_button = QPushButton("PROGRAM")
        self.program_button.setStyleSheet(
            "background-color:#ffd27f; font-weight:bold; padding:4px 10px;"
        )
        self.program_button.setCursor(Qt.PointingHandCursor)
        self.program_button.clicked.connect(self._start_program)
        self.program_status_label = QLabel("")
        self.program_status_label.setStyleSheet("color:#666; font-style:italic;")
        pl.addWidget(self.program_button)
        pl.addWidget(self.program_status_label)
        pl.addStretch()
        self._info_vbox.addWidget(program_row)

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
        led_edit = self._param_edits.get("led_selection")
        if led_edit is not None:
            led_edit.setText(str(selection))

    def _clear_brain_map(self) -> None:
        self._led_selection = 0
        self._brain_map.set_selection(0)
        self._led_value_label.setText("0")

    # ── Program (write) ────────────────────────────────────────────────────

    def _start_program(self) -> None:
        if self._busy or not self._connected or self._og is None:
            return
        try:
            from village.devices.optogrid import OptoSetting

            opto_settings = OptoSetting(
                **{key: int(edit.text()) for key, edit in self._param_edits.items()}
            )
        except ValueError as e:
            self.program_status_label.setText(f"Invalid value: {e}")
            return
        self._busy = True
        self._programming = True
        self._program_done = False
        self._program_error = ""
        self._set_action_buttons_enabled(False)
        self.program_status_label.setText("Programming…")
        threading.Thread(
            target=self._run_program, args=(opto_settings,), daemon=True
        ).start()

    def _run_program(self, opto_settings) -> None:
        try:
            og = self._og
            if og is None:
                self._program_error = "Not connected"
                return
            if not og.program(opto_settings):
                self._program_error = "Programming failed"
                return
            # re-read so the panel shows what's actually on the device now
            self._battery_mv = og.read_battery_mv()
            self._connect_params = og.read_params() or {}
        except Exception as e:
            self._program_error = str(e)
        finally:
            self._program_done = True

    # ── Quick actions: trigger + toggle LEDs ────────────────────────────────

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        # live_imu_button deliberately excluded: opening it only reads the
        # local imu_raw_history deque, no BLE round-trip, so it's safe to
        # click even while another action is in flight.
        for name in (
            "trigger_button",
            "sham_button",
            "status_button",
            "imu_button",
            "uled_scan_button",
            "last_stim_button",
            "program_button",
            "disconnect_button",
        ):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.setEnabled(enabled)

    def _update_toggle_button_styles(self) -> None:
        on_style = "background-color:#7fd27f; font-weight:bold;"
        off_style = "background-color:#ddd;"
        if hasattr(self, "sham_button"):
            self.sham_button.setStyleSheet(on_style if self._sham_on else off_style)
        if hasattr(self, "status_button"):
            self.status_button.setStyleSheet(on_style if self._status_on else off_style)
        if hasattr(self, "imu_button"):
            imu_on = self._og.imu_logging if self._og is not None else False
            self.imu_button.setStyleSheet(on_style if imu_on else off_style)

    def _start_quick_action(
        self,
        fn: Callable[[], None],
        ok_message: str,
        on_success: Callable[[], None] | None = None,
    ) -> None:
        """Runs fn() on a background thread against the already-open
        self._og. fn must only touch self._-prefixed state, never widgets
        directly. on_success (optional) runs afterwards on the Qt thread,
        from update_gui() -- for actions whose result needs to update a
        widget (e.g. the brain map's broken-LED overlay), not just report
        success/failure via ok_message."""
        if self._busy or not self._connected or self._og is None:
            return
        self._busy = True
        self._action_done = False
        self._action_error = ""
        self._action_message = ok_message
        self._action_on_success = on_success
        self._set_action_buttons_enabled(False)
        self.action_status_label.setText(f"{ok_message}…")
        threading.Thread(target=self._run_quick_action, args=(fn,), daemon=True).start()

    def _run_quick_action(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except Exception as e:
            self._action_error = str(e)
        finally:
            self._action_done = True

    def _start_trigger(self) -> None:
        og = self._og
        if og is None:
            return

        def do() -> None:
            if not og.trigger():
                raise RuntimeError("Trigger failed")

        self._start_quick_action(do, "Triggered")

    def _start_toggle_sham(self) -> None:
        og = self._og
        if og is None:
            return
        new_state = not self._sham_on

        def do() -> None:
            if not og.toggle_sham_led(new_state):
                raise RuntimeError("SHAM toggle failed")
            self._sham_on = new_state

        self._start_quick_action(do, f"SHAM {'ON' if new_state else 'OFF'}")

    def _start_toggle_status(self) -> None:
        og = self._og
        if og is None:
            return
        new_state = not self._status_on

        def do() -> None:
            if not og.toggle_status_led(new_state):
                raise RuntimeError("STATUS toggle failed")
            self._status_on = new_state

        self._start_quick_action(do, f"STATUS {'ON' if new_state else 'OFF'}")

    def _start_toggle_imu(self) -> None:
        og = self._og
        if og is None:
            return
        turning_on = not og.imu_logging

        def do() -> None:
            if turning_on:
                if not og.start_imu_logging():
                    raise RuntimeError("Could not start IMU logging")
            else:
                og.stop_imu_logging()

        self._start_quick_action(do, f"IMU {'ON' if turning_on else 'OFF'}")

    def _start_uled_scan(self) -> None:
        og = self._og
        if og is None:
            return

        def do() -> None:
            mask = og.read_uled_check()
            if mask is None:
                raise RuntimeError("uLED scan failed")
            self._uled_mask = mask

        def on_success() -> None:
            mask = self._uled_mask
            assert mask is not None  # do() raised above if it were
            self._brain_map.set_check_mask(mask)
            broken = bin((~mask) & ((1 << 64) - 1)).count("1")
            self._action_message = (
                f"uLED scan: {broken} broken" if broken else "uLED scan: all OK"
            )

        self._start_quick_action(do, "Scanning uLEDs", on_success)

    def _start_read_last_stim(self) -> None:
        og = self._og
        if og is None:
            return

        def do() -> None:
            ms = og.read_last_stim_ms()
            if ms is None:
                raise RuntimeError("Last-stim read failed")
            self._last_stim_ms = ms

        def on_success() -> None:
            self._action_message = f"Last stim: {self._last_stim_ms} ms (since boot)"

        self._start_quick_action(do, "Reading last stim", on_success)

    def _open_live_imu(self) -> None:
        if not self._connected or self._og is None:
            self.action_status_label.setText("Connect to a device first")
            return
        dialog = _LiveIMUDialog(self._og, parent=self.window)
        dialog.show()

    # ── Disconnect ───────────────────────────────────────────────────────────

    def _start_disconnect(self) -> None:
        if self._busy or not self._connected or self._og is None:
            return
        self._busy = True
        self._disconnecting = True
        self._disconnect_done = False
        self._set_action_buttons_enabled(False)
        self.status_label.setText(f"Disconnecting from {self._connect_name}…")
        threading.Thread(
            target=self._run_disconnect, args=(self._og,), daemon=True
        ).start()

    def _run_disconnect(self, og) -> None:
        try:
            og.disconnect()
        except Exception:
            pass
        try:
            og.stop()
        except Exception:
            pass
        self._disconnect_done = True

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
                self._connected = True
                # unknown until scanned again on this (possibly different)
                # device -- don't carry over a stale broken-LED overlay
                self._uled_mask = None
                self._brain_map.set_check_mask((1 << 64) - 1)
                self._populate_device_info()
        if self._programming and self._program_done:
            self._programming = False
            self._busy = False
            if self._program_error:
                self.status_label.setText(f"Error: {self._program_error}")
                self._set_action_buttons_enabled(True)
            else:
                # rebuilds the info panel (and program_status_label with it),
                # so the "Programmed" confirmation is set after, on status_label
                self._populate_device_info()
                self.status_label.setText(
                    f"{self._connect_name} — programmed successfully"
                )
        if self._busy and self._action_done and not self._programming:
            self._busy = False
            self._set_action_buttons_enabled(True)
            if self._action_error:
                self.action_status_label.setText(f"Error: {self._action_error}")
            else:
                if self._action_on_success is not None:
                    self._action_on_success()
                self.action_status_label.setText(self._action_message)
            self._action_on_success = None
            self._update_toggle_button_styles()
        if self._disconnecting and self._disconnect_done:
            self._disconnecting = False
            self._busy = False
            self._og = None
            self._connected = False
            self._connect_address = ""
            self.status_label.setText(f"Disconnected from {self._connect_name}")
            self._set_info_message("Click a device name to read its parameters")

    # ── Cleanup ──────────────────────────────────────────────────────────────

    def change_layout(self) -> bool:
        """Called before switching away from this calibration -- disconnect
        so we don't leak a live BLE connection and its background thread."""
        if self._connected and self._og is not None:
            og = self._og
            try:
                og.disconnect()
            except Exception:
                pass
            try:
                og.stop()
            except Exception:
                pass
            self._og = None
            self._connected = False
        return True
