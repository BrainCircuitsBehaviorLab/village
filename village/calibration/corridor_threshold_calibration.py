from __future__ import annotations

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog, QLabel

from village.calibration.corridor_threshold_detection import area_count, scan_video
from village.classes.enums import Active, Color
from village.custom_classes.calibration_base import CalibrationBase
from village.settings import settings

_AREAS = range(4)


def _frame_to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QPixmap.fromImage(QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888))


class CorridorThresholdCalibration(CalibrationBase):
    name = "corridor_threshold_calibration"

    _PV_W = 40
    _PV_H = 9

    def __init__(self) -> None:
        super().__init__()
        self._paths: dict[str, str] = {}
        self._frames: dict[str, dict[int, np.ndarray | None]] = {"day": {}, "night": {}}
        self._preview_labels: dict[tuple[str, int], QLabel] = {}
        self._status: QLabel | None = None
        self._lbs: list = []
        self._last_sig: tuple | None = None

    @property
    def display_name(self) -> str:
        return "CORRIDOR THRESHOLDS"

    @classmethod
    def is_active(cls) -> bool:
        return settings.get("USE_CORRIDOR") == Active.ON

    @staticmethod
    def _padded(name: str) -> list[int]:
        v = list(settings.get(name))
        if len(v) == 5:
            v.append(v[4])
        return v

    def _ensure_six(self, name: str) -> None:
        v = list(settings.get(name))
        if len(v) == 5:
            v.append(v[4])
            settings.set(name, v)

    def draw(self) -> None:
        for i in _AREAS:
            self._ensure_six(f"AREA{i + 1}_CORRIDOR")
        self._lbs = []
        self._last_sig = None

        self.layout.create_and_add_label(
            "CORRIDOR DETECTION THRESHOLDS (DAY / NIGHT)", 0, 0, 60, 2, "black"
        )
        self.layout.create_and_add_button(
            "Load day video", 2, 0, 16, 2, lambda: self._load("day"), ""
        )
        self.layout.create_and_add_button(
            "Load night video", 2, 18, 18, 2, lambda: self._load("night"), ""
        )
        self.layout.create_and_add_button(
            "Re-find frames", 2, 38, 16, 2, lambda: self._refind(), ""
        )
        self._status = self.layout.create_and_add_label(
            "Load a day and a night corridor video.", 2, 56, 80, 2, "black"
        )

        self._draw_previews("day", "DAY (visible light)", 5, 0)
        self._draw_previews("night", "NIGHT (infrared)", 5, 88)

        self.layout.create_and_add_label(
            "Areas: left/right/top/bottom, day & night threshold", 26, 0, 70, 2, "black"
        )
        for i in _AREAS:
            self._draw_area_controls(f"AREA{i + 1}_CORRIDOR", 28, i * 34 + 2)

        self._render_all()

    def _draw_previews(self, kind: str, header: str, row: int, col: int) -> None:

        self.layout.create_and_add_label(header, row, col, 40, 2, "black")
        positions = {
            0: (row + 2, col),
            1: (row + 2, col + self._PV_W + 2),
            2: (row + 2 + self._PV_H + 1, col),
            3: (row + 2 + self._PV_H + 1, col + self._PV_W + 2),
        }
        for i in _AREAS:
            r, c = positions[i]
            label = QLabel("area " + str(i + 1))
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid #888; color: black;")
            label.setFixedSize(
                self._PV_W * self.layout.column_width,
                self._PV_H * self.layout.row_height,
            )
            self.layout.addWidget(label, r, c, self._PV_H, self._PV_W)
            self._preview_labels[(kind, i)] = label

    def _draw_area_controls(self, name: str, row: int, col: int) -> None:
        from village.gui.monitor_layout import LabelButtons

        self.layout.create_and_add_label(name, row, col, 16, 2, "black")
        r = row + 2
        for direction in (
            "left",
            "right",
            "top",
            "bottom",
            "thr_day",
            "thr_night",
        ):
            lb = LabelButtons(name, direction, r, col, 8, "black", self.layout)
            self._lbs.append(lb)
            r += 2

    def _load(self, kind: str) -> None:
        fn = "Select " + kind + " corridor video"
        lbl = "Corridor videos (CORRIDOR_*.mp4);;All files (*)"
        path, _ = QFileDialog.getOpenFileName(
            self.window, fn, settings.get("VIDEOS_DIRECTORY"), lbl
        )
        if not path:
            return
        self._paths[kind] = path
        self._scan(kind)

    def _refind(self) -> None:
        for kind in ("day", "night"):
            if kind in self._paths:
                self._scan(kind)

    def _scan(self, kind: str) -> None:
        if self._status is not None:
            self._status.setText("Scanning " + kind + " video...")
        areas = [self._padded(f"AREA{i + 1}_CORRIDOR") for i in _AREAS]
        thr_index = 4 if kind == "day" else 5
        thresholds = [a[thr_index] for a in areas]
        rects = [a[0:4] for a in areas]
        empty = settings.get("DETECTION_OF_MOUSE_CORRIDOR")[0]
        black = settings.get("DETECTION_COLOR") == Color.BLACK
        self._frames[kind] = scan_video(
            self._paths[kind], rects, thresholds, empty, black
        )
        found = sum(f is not None for f in self._frames[kind].values())
        if self._status is not None:
            status_text = f"{kind.capitalize()}: {found}/4 area frames found."
            self._status.setText(status_text)
        self._last_sig = None
        self._render_all()

    def update_gui(self) -> None:
        sig = tuple(tuple(self._padded(f"AREA{i + 1}_CORRIDOR")) for i in _AREAS)
        if sig != self._last_sig:
            self._last_sig = sig
            self._render_all()

    def _render_all(self) -> None:
        for kind in ("day", "night"):
            for i in _AREAS:
                self._render_preview(kind, i)

    def _render_preview(self, kind: str, area: int) -> None:
        label = self._preview_labels.get((kind, area))
        if label is None:
            return
        frame = self._frames.get(kind, {}).get(area)
        if frame is None:
            label.setText("area " + str(area + 1) + "\n(no frame)")
            return
        annotated = self._annotate(frame, kind)
        pixmap = _frame_to_pixmap(annotated).scaled(
            label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(pixmap)

    def _annotate(self, frame: np.ndarray, kind: str) -> np.ndarray:
        annotated = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thr_index = 4 if kind == "day" else 5
        black = settings.get("DETECTION_COLOR") == Color.BLACK
        for i in _AREAS:
            area = self._padded(f"AREA{i + 1}_CORRIDOR")
            x1, y1, x2, y2 = area[0:4]
            _, mask = area_count(gray, area[0:4], area[thr_index], black)
            sub = annotated[y1:y2, x1:x2]
            sub[mask > 0] = (0, 0, 255)
            color = tuple(int(c) for c in settings.get(f"COLOR_AREA{i + 1}"))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        return annotated
