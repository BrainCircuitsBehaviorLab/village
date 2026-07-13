from __future__ import annotations

import json
import traceback
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog, QLabel

from village.calibration.camera_calibration_grid import make_circle_grid
from village.custom_classes.calibration_base import CalibrationBase
from village.gui.layout import Layout
from village.scripts.log import log
from village.scripts.utils import create_pixmap
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow


def _frame_to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QPixmap.fromImage(QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888))


def _make_diagnostic_plots(diag: dict, width_in: float, height_in: float) -> plt.Figure:
    pts = diag["pts"]
    errs = diag["errs"]
    mags = np.linalg.norm(errs, axis=1)
    grid_pts = diag["grid_pts"]
    disp = diag["disp"]
    disp_mag = np.linalg.norm(disp, axis=1)
    w, h = diag["image_size"]

    dpi = int(settings.get("MATPLOTLIB_DPI"))
    fig, axes = plt.subplots(2, 2, figsize=(width_in, height_in), dpi=dpi)
    cb_args = dict(fraction=0.03, pad=0.03)

    tilt_x = diag.get("tilt_x_deg", 0.0)
    tilt_y = diag.get("tilt_y_deg", 0.0)
    tilt_t = diag.get("tilt_total", 0.0)
    roll = diag.get("roll_deg", 0.0)
    fig.suptitle(
        f"Tilt X {tilt_x:+.1f}°  Tilt Y {tilt_y:+.1f}°  "
        f"Tilt total {tilt_t:.1f}°  Roll {roll:+.1f}°",
        fontsize=9,
    )

    ax = axes[0, 0]
    ax.tricontourf(pts[:, 0], pts[:, 1], mags, levels=10, cmap="hot", alpha=0.25)
    q = ax.quiver(
        pts[:, 0],
        pts[:, 1],
        errs[:, 0],
        errs[:, 1],
        mags,
        cmap="hot",
        angles="xy",
        scale_units="xy",
        scale=0.05,
    )
    fig.colorbar(q, ax=ax, label="error (px)", **cb_args)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    ax = axes[0, 1]
    q2 = ax.quiver(
        grid_pts[:, 0],
        grid_pts[:, 1],
        disp[:, 0],
        disp[:, 1],
        disp_mag,
        cmap="cool",
        angles="xy",
        scale_units="xy",
        scale=0.3,
    )
    fig.colorbar(q2, ax=ax, label="displacement (px)", **cb_args)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    ax = axes[1, 0]
    last_pts = diag.get("last_pts")
    grid_size = diag.get("grid_size")
    if last_pts is not None and grid_size is not None:
        cols, rows = grid_size
        pg = last_pts.reshape(rows, cols, 2)
        tl, tr = pg[0, 0], pg[0, cols - 1]
        bl, br = pg[rows - 1, 0], pg[rows - 1, cols - 1]
        center = np.mean([tl, tr, bl, br], axis=0)
        avg_w = (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2
        avg_h = (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2
        rr = diag.get("roll_rad", 0.0)
        cr, sr = np.cos(rr), np.sin(rr)
        hw, hh = avg_w / 2, avg_h / 2
        ideal = np.array(
            [
                center + [-cr * hw + sr * hh, -sr * hw - cr * hh],
                center + [cr * hw + sr * hh, sr * hw - cr * hh],
                center + [cr * hw - sr * hh, sr * hw + cr * hh],
                center + [-cr * hw - sr * hh, -sr * hw + cr * hh],
            ]
        )
        ax.scatter(last_pts[:, 0], last_pts[:, 1], s=3, c="steelblue", zorder=3)
        ax.plot(
            *np.vstack([tl, tr, br, bl, tl]).T,
            "r-",
            lw=2,
            label=f"Actual (tilt {tilt_t:.1f}°)",
        )
        ax.plot(*np.vstack([ideal, ideal[0]]).T, "g--", lw=2, label="Ideal")
        roll_row = diag.get("roll_top_row")
        if roll_row is not None and len(roll_row) >= 2:
            ax.scatter(
                roll_row[:, 0],
                roll_row[:, 1],
                s=20,
                c="orange",
                zorder=5,
                label="Roll ref row",
            )
            ax.plot(
                [roll_row[0, 0], roll_row[-1, 0]],
                [roll_row[0, 1], roll_row[-1, 1]],
                color="orange",
                lw=1.5,
                linestyle="--",
                zorder=4,
            )
        ax.legend(fontsize=7, ncols=3)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect("equal")
    else:
        ax.text(
            0.5,
            0.5,
            "Grid size not set",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="gray",
        )
    ax.axis("off")

    ax = axes[1, 1]
    scale_data = diag.get("scale_data")
    if scale_data is not None and len(scale_data["vals"]) > 3:
        sp = scale_data["pos"]
        sv = scale_data["vals"]
        tcf2 = ax.tricontourf(sp[:, 0], sp[:, 1], sv, levels=15, cmap="viridis")
        fig.colorbar(tcf2, ax=ax, label="px / cm", **cb_args)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.set_aspect("equal")
    else:
        ax.text(
            0.5,
            0.5,
            "Scale not available\n(set grid size)",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="gray",
        )
    ax.axis("off")

    plt.tight_layout()
    return fig


class DiagnosticPlotsLayout(Layout):
    def __init__(self, window: GuiWindow, rows: int, columns: int) -> None:
        super().__init__(window, stacked=True, rows=rows, columns=columns)
        self.rows = rows
        self.columns = columns
        self._draw()

    def _draw(self) -> None:
        self.plot_label = QLabel()
        self.plot_label.setStyleSheet(
            "QLabel {border: 1px solid gray; background-color: white;}"
        )
        self.addWidget(self.plot_label, 0, 0, self.rows, self.columns)
        dpi = int(settings.get("MATPLOTLIB_DPI"))
        self.plot_width = (self.columns * self.column_width - 10) / dpi
        self.plot_height = (self.rows * self.row_height - 5) / dpi

    def update(self, diag: dict) -> None:
        try:
            fig = _make_diagnostic_plots(diag, self.plot_width, self.plot_height)
            self.plot_label.setPixmap(create_pixmap(fig))
            plt.close(fig)
        except Exception:
            pass


class CameraCalibration(CalibrationBase):
    name = "camera_calibration"

    def __init__(
        self, spacing_mm: float = 50, grid_size: tuple[int, int] | None = None
    ) -> None:
        self.spacing_mm = spacing_mm
        self.measured_spacing_mm: float | None = None
        self.grid_size = grid_size

        self.running = False
        self.error = False
        self.result: dict | None = None
        self.diagnostic_data: dict | None = None
        self.live_metrics: dict | None = None
        self.last_spacing_px: float | None = None

        self._spacing_px: float | None = None
        self._detector = _make_blob_detector()
        self._obj_points: list[np.ndarray] = []
        self._img_points: list[np.ndarray] = []
        self._image_size: tuple[int, int] | None = None

    @classmethod
    def is_active(cls) -> bool:
        return True

    def draw(self) -> None:
        from village.devices.camera import Camera, cam_box

        self._cam_box_ref = cam_box
        self._cam_class_ref = Camera

        self._result_path: Path = default_result_path()
        self._ui_result: dict | None = None
        self._last_annotated: np.ndarray | None = None
        self._obj_points = []
        self._img_points = []
        self._image_size = None
        self.running = False
        self.error = False
        self.result = None
        self.diagnostic_data = None
        self.live_metrics = None

        self.layout.create_and_add_label(
            "GRID GENERATION",
            5,
            2,
            40,
            2,
            "black",
            description="Generate a printable symmetric circle grid.\n"
            "Print it and verify spacing with a ruler.",
        )
        self.layout.create_and_add_label(
            "PAGE W (mm)",
            8,
            2,
            14,
            2,
            "black",
            bold=False,
            description="Page width in mm (e.g. 210 for A4)",
        )
        self.page_w_edit = self.layout.create_and_add_line_edit(
            "210", 10, 2, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "PAGE H (mm)",
            8,
            12,
            14,
            2,
            "black",
            bold=False,
            description="Page height in mm (e.g. 297 for A4)",
        )
        self.page_h_edit = self.layout.create_and_add_line_edit(
            "297", 10, 12, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "SPACING (mm)",
            8,
            22,
            16,
            2,
            "black",
            bold=False,
            description="Centre-to-centre distance between circles in mm",
        )
        self.spacing_edit = self.layout.create_and_add_line_edit(
            "50", 10, 22, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "DOT RADIUS (mm)",
            8,
            32,
            18,
            2,
            "black",
            bold=False,
            description="Radius of each printed circle in mm",
        )
        self.dot_radius_edit = self.layout.create_and_add_line_edit(
            "10", 10, 32, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "MARGIN (mm)",
            8,
            42,
            14,
            2,
            "black",
            bold=False,
            description="Empty border around the grid in mm",
        )
        self.margin_edit = self.layout.create_and_add_line_edit(
            "0", 10, 42, 8, 2, lambda _: None
        )
        self.generate_button = self.layout.create_and_add_button(
            "GENERATE GRID PDF",
            13,
            2,
            30,
            2,
            self._generate_grid_clicked,
            "Generate a printable circle grid PDF",
            "powderblue",
        )
        self.grid_status_label = self.layout.create_and_add_label(
            "", 16, 2, 50, 2, "gray", bold=False
        )

        self.layout.create_and_add_label(
            "CALIBRATION DETECTION",
            19,
            2,
            50,
            2,
            "black",
            description="Parameters of the real grid in front of the camera.\n"
            "Rows/cols may differ from the printed sheet if stitched several.",
        )
        self.layout.create_and_add_label(
            "GRID COLS",
            21,
            2,
            14,
            2,
            "black",
            bold=False,
            description="Columns in the stitched calibration grid",
        )
        self.grid_cols_edit = self.layout.create_and_add_line_edit(
            "30", 23, 2, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "GRID ROWS",
            21,
            12,
            14,
            2,
            "black",
            bold=False,
            description="Rows in the stitched calibration grid",
        )
        self.grid_rows_edit = self.layout.create_and_add_line_edit(
            "18", 23, 12, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "SPACING (px)",
            21,
            22,
            16,
            2,
            "black",
            bold=False,
            description="Expected centre-to-centre dot spacing in pixels.\n"
            "Used to tune the blob detector area bounds.",
        )
        self.spacing_px_edit = self.layout.create_and_add_line_edit(
            "17", 23, 22, 8, 2, lambda _: None
        )
        self.layout.create_and_add_label(
            "MEASURED SPACING (mm)",
            21,
            34,
            22,
            2,
            "black",
            bold=False,
            description="Actual printed dot spacing measured with a ruler.\n"
            "Leave blank to use SPACING (mm) above.\n"
            "Only affects the px/cm scale heatmap.",
        )
        self.measured_spacing_edit = self.layout.create_and_add_line_edit(
            "", 23, 34, 8, 2, lambda _: None
        )

        self.capture_button = self.layout.create_and_add_button(
            "CAPTURE FRAME",
            26,
            2,
            28,
            2,
            self._capture_clicked,
            "Grab current frame, detect grid, and run calibration",
            "powderblue",
        )
        self.load_image_button = self.layout.create_and_add_button(
            "LOAD IMAGE",
            26,
            32,
            20,
            2,
            self._load_image_clicked,
            "Load a PNG/JPG image file and use it as a calibration frame",
            "powderblue",
        )
        self.clear_button = self.layout.create_and_add_button(
            "CLEAR FRAMES",
            26,
            54,
            20,
            2,
            self._clear_clicked,
            "Discard all captured frames and start over",
            "lightyellow",
        )
        self.frames_label = self.layout.create_and_add_label(
            "Frames: 0", 29, 2, 30, 2, "black", bold=False
        )
        self.calib_status_label = self.layout.create_and_add_label(
            "", 32, 2, 95, 2, "gray", bold=False
        )
        self.result_label = self.layout.create_and_add_label(
            "", 35, 2, 95, 5, "black", bold=False
        )
        self.metrics_label = self.layout.create_and_add_label(
            "", 41, 2, 95, 10, "black", bold=False
        )
        self.save_button = self.layout.create_and_add_button(
            "SAVE JSON",
            52,
            2,
            20,
            2,
            self._save_clicked,
            "Save calibration result to camera_calibration.json",
            "powderblue",
        )
        self.save_button.setDisabled(True)

        self.preview_label = QLabel()
        self.preview_label.setStyleSheet(
            "QLabel {border: 1px solid gray; background-color: black;}"
        )
        self.layout.addWidget(self.preview_label, 6, 103, 20, 95)

        self.plot_layout = DiagnosticPlotsLayout(self.window, 24, 95)
        self.layout.addLayout(self.plot_layout, 28, 103, 24, 95)

        self.spacing_mm = self._spacing_value()
        self.grid_size = self._grid_size_value()

    # ── value helpers ──────────────────────────────────────────────────────────

    def _spacing_value(self) -> float:
        try:
            return float(self.spacing_edit.text())
        except (ValueError, AttributeError):
            return 50.0

    def _spacing_px_value(self) -> float | None:
        try:
            v = float(self.spacing_px_edit.text())
            return v if v > 0 else None
        except (ValueError, AttributeError):
            return None

    def _measured_spacing_value(self) -> float | None:
        try:
            v = float(self.measured_spacing_edit.text())
            return v if v > 0 else None
        except (ValueError, AttributeError):
            return None

    def _grid_size_value(self) -> tuple[int, int] | None:
        try:
            cols = int(self.grid_cols_edit.text())
            rows = int(self.grid_rows_edit.text())
            if cols > 0 and rows > 0:
                return (cols, rows)
        except (ValueError, AttributeError):
            pass
        return None

    # ── button callbacks ───────────────────────────────────────────────────────

    def _generate_grid_clicked(self) -> None:
        try:
            page_w = float(self.page_w_edit.text())
            page_h = float(self.page_h_edit.text())
            spacing = float(self.spacing_edit.text())
            dot_radius = float(self.dot_radius_edit.text())
            margin = float(self.margin_edit.text())
            out = Path(settings.get("DATA_DIRECTORY")) / "calibration_grid.pdf"
            make_circle_grid(
                page_w_mm=page_w,
                page_h_mm=page_h,
                spacing_mm=spacing,
                circle_radius_mm=dot_radius,
                margin_mm=margin,
                out_path=str(out),
            )
            self.grid_status_label.setText(f"Saved: {out}")
            self.grid_status_label.setStyleSheet(
                "QLabel {color: green; font-weight: normal}"
            )
        except Exception:
            self.grid_status_label.setText("Error generating grid")
            self.grid_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )

    def _capture_clicked(self) -> None:
        if self.running:
            return
        if not isinstance(self._cam_box_ref, self._cam_class_ref):
            self.calib_status_label.setText("No frame available")
            return
        self._process_frame(self._cam_box_ref.frame)

    def _process_frame(self, frame: np.ndarray) -> None:
        self._last_annotated = None
        self.spacing_mm = self._spacing_value()
        self.spacing_px = self._spacing_px_value()
        self.measured_spacing_mm = self._measured_spacing_value()
        self.grid_size = self._grid_size_value()
        annotated, found = self.process_frame(frame)

        if found:
            self._last_annotated = annotated

        px = _frame_to_pixmap(annotated)
        if not px.isNull():
            self.preview_label.setPixmap(
                px.scaled(self.preview_label.width(), self.preview_label.height(), 1)
            )

        if not found:
            self.calib_status_label.setText("No grid detected in this frame")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: orange; font-weight: normal}"
            )
            return

        n = self.n_detected
        self.frames_label.setText(f"Frames: {n}")
        if n < 4:
            self.calib_status_label.setText(
                f"Grid detected, need {4 - n} more frame(s) to calibrate"
            )
            self.calib_status_label.setStyleSheet(
                "QLabel {color: gray; font-weight: normal}"
            )
            return

        self.calibrate_in_thread()
        self.calib_status_label.setText(f"Calibrating… ({n} frames)")
        self.calib_status_label.setStyleSheet(
            "QLabel {color: gray; font-weight: normal}"
        )
        self.capture_button.setDisabled(True)

    def _load_image_clicked(self) -> None:
        if self.running:
            return
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Open calibration image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not path:
            return
        frame = cv2.imread(path)
        if frame is None:
            self.calib_status_label.setText(f"Could not load image: {path}")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )
            return
        self._process_frame(frame)

    def _clear_clicked(self) -> None:
        self.clear()
        self._ui_result = None
        self._last_annotated = None
        self.frames_label.setText("Frames: 0")
        self.calib_status_label.setText("Frames cleared")
        self.calib_status_label.setStyleSheet(
            "QLabel {color: gray; font-weight: normal}"
        )
        self.result_label.setText("")
        self.metrics_label.setText("")
        self.save_button.setDisabled(True)
        self.capture_button.setEnabled(True)

    def _save_clicked(self) -> None:
        if self._ui_result is None:
            return
        try:
            self.save(self._result_path)
            self.calib_status_label.setText(f"Saved: {self._result_path}")
        except Exception:
            self.calib_status_label.setText("Error saving result")

    def _show_result(self, result: dict) -> None:
        d = result["dist_coeffs"]
        k1 = d[0]
        dtype = "barrel" if k1 < 0 else "pincushion"
        level = (
            "minimal" if abs(k1) < 0.05 else "moderate" if abs(k1) < 0.15 else "strong"
        )
        err = result["reprojection_error_px"]
        quality = "good" if err < 1.0 else "high -> retake frames"
        text = (
            f"Frames used: {result['n_images_used']}\n"
            f"Calib reproj error (all frames): {err:.4f} px  ({quality})\n"
            f"Distortion: {level} {dtype}  (k1={k1:+.4f})\n"
            f"k1={d[0]:+.4f}  k2={d[1]:+.4f}  "
            f"p1={d[2]:+.4f}  p2={d[3]:+.4f}\n"
            f"Principal pt offset: "
            f"({result['cx_offset_px']:+.1f} px, "
            f"{result['cy_offset_px']:+.1f} px)  "
            f"tangential: {result['tangential']:.5f}"
        )
        self.result_label.setText(text)
        self.calib_status_label.setText("Calibration complete")
        self.calib_status_label.setStyleSheet(
            "QLabel {color: green; font-weight: normal}"
        )
        self.save_button.setEnabled(True)
        if self.diagnostic_data is not None:
            self.plot_layout.update(self.diagnostic_data)

    def _show_live_metrics(self, m: dict) -> None:
        def tag(v, good, ok):
            return "GOOD" if v <= good else "OK  " if v <= ok else "POOR"

        def hint_x(deg):
            if abs(deg) < 0.5:
                return ""
            return "→ raise right" if deg > 0 else "→ raise left"

        def hint_y(deg):
            if abs(deg) < 0.5:
                return ""
            return "→ raise back" if deg > 0 else "→ raise front"

        def hint_roll(deg):
            if abs(deg) < 0.3:
                return ""
            return "→ rotate CW" if deg > 0 else "→ rotate CCW"

        tx = m.get("tilt_x_deg", 0.0)
        ty = m.get("tilt_y_deg", 0.0)
        roll = m["roll_deg"]
        lines = [
            "Physical adjustment",
            f"  Tilt total:       {m['tilt_deg']:5.2f}°  "
            f"[{tag(m['tilt_deg'], 2.0, 5.0)}]  (good<2°, ok<5°)",
            f"    Tilt X (L/R):   {tx:+6.2f}°  "
            f"[{tag(abs(tx), 2.0, 5.0)}]  {hint_x(tx)}",
            f"    Tilt Y (F/B):   {ty:+6.2f}°  "
            f"[{tag(abs(ty), 2.0, 5.0)}]  {hint_y(ty)}",
            f"  Roll:             {roll:5.2f}°  "
            f"[{tag(roll, 1.0, 3.0)}]  {hint_roll(roll)}",
            "Pose quality (latest frame vs calibrated model)",
            f"  Reproj error:     {m['reproj_err']:5.3f} px  "
            f"[{tag(m['reproj_err'], 0.5, 1.5)}]  (good<0.5, ok<1.5)",
        ]
        self.metrics_label.setText("\n".join(lines))

    # ── periodic update ────────────────────────────────────────────────────────

    def update_gui(self) -> None:
        self.update_status_label_buttons()

        display = (
            self._last_annotated
            if self._last_annotated is not None
            else (
                self._cam_box_ref.frame
                if isinstance(self._cam_box_ref, self._cam_class_ref)
                else None
            )
        )
        if display is not None:
            try:
                px = _frame_to_pixmap(display)
                if not px.isNull():
                    self.preview_label.setPixmap(
                        px.scaled(
                            self.preview_label.width(),
                            self.preview_label.height(),
                            1,
                        )
                    )
            except Exception:
                pass

        if self.live_metrics is not None:
            self._show_live_metrics(self.live_metrics)

        if self.error:
            self.calib_status_label.setText("Calibration failed, check log")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )
            self.capture_button.setEnabled(True)
            self.error = False
            return

        if (
            not self.running
            and self.result is not self._ui_result
            and self.result is not None
        ):
            self._ui_result = self.result
            self._show_result(self._ui_result)
            self.capture_button.setEnabled(True)

    @property
    def spacing_px(self) -> float | None:
        return self._spacing_px

    @spacing_px.setter
    def spacing_px(self, value: float | None) -> None:
        if value != self._spacing_px:
            self._spacing_px = value
            self._detector = _make_blob_detector(value)

    @property
    def n_detected(self) -> int:
        return len(self._obj_points)

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, bool]:
        annotated = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self._image_size is None:
            self._image_size = (gray.shape[1], gray.shape[0])

        obj_pts, img_pts = _detect_grid(
            gray, self._detector, self.spacing_mm, self.grid_size
        )
        found = obj_pts is not None
        if found:
            self._obj_points.append(obj_pts)
            self._img_points.append(img_pts)
            _draw_grid(annotated, img_pts, self.grid_size)
            self.last_spacing_px = _compute_spacing_px(img_pts, self.grid_size)
            if self.result is not None:
                K = np.array(self.result["camera_matrix"])
                dist = np.array(self.result["dist_coeffs"])
                self.live_metrics = _compute_live_metrics(obj_pts, img_pts, K, dist)

        return annotated, found

    def clear(self) -> None:
        self._obj_points.clear()
        self._img_points.clear()
        self._frame_idx = 0
        self.result = None
        self.diagnostic_data = None
        self.live_metrics = None

    def calibrate_in_thread(self) -> None:
        if self.running or self.n_detected < 4:
            return
        self.running = True
        self.error = False
        self.result = None
        Thread(target=self._run, daemon=True).start()

    def save(self, out_path: Path) -> None:
        if self.result is None:
            return
        keys = (
            "camera_matrix",
            "dist_coeffs",
            "reprojection_error_px",
            "image_size_wh",
            "n_images_used",
            "spacing_mm",
        )
        data = {k: self.result[k] for k in keys if k in self.result}
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    def _run(self) -> None:
        try:
            if self._image_size is None:
                return
            K, dist, rvecs, tvecs, err = _run_calibration(
                self._obj_points, self._img_points, self._image_size
            )
            d = dist.ravel()
            w, h = self._image_size
            _tang = float(np.sqrt(d[2] ** 2 + d[3] ** 2)) if len(d) >= 4 else 0.0
            self.result = {
                "camera_matrix": K.tolist(),
                "dist_coeffs": d.tolist(),
                "reprojection_error_px": float(err),
                "image_size_wh": list(self._image_size),
                "n_images_used": self.n_detected,
                "spacing_mm": self.spacing_mm,
                "k1": float(d[0]),
                "tangential": _tang,
                "cx_offset_px": float(K[0, 2] - w / 2),
                "cy_offset_px": float(K[1, 2] - h / 2),
            }

            self.diagnostic_data = _compute_diagnostic_data(
                self._obj_points,
                self._img_points,
                K,
                dist,
                rvecs,
                tvecs,
                self._image_size,
                spacing_mm=self.measured_spacing_mm or self.spacing_mm,
                grid_size=self.grid_size,
            )
        except Exception:
            log.error("Camera calibration error", exception=traceback.format_exc())
            self.error = True
        finally:
            self.running = False


def _compute_spacing_px(
    img_pts: np.ndarray, grid_size: tuple[int, int] | None
) -> float:
    pts = img_pts.reshape(-1, 2)
    if grid_size is not None:
        cols, rows = grid_size
        pg = pts.reshape(rows, cols, 2)
        h = np.linalg.norm(np.diff(pg, axis=1), axis=2)
        v = np.linalg.norm(np.diff(pg, axis=0), axis=2)
        return float(np.mean(np.concatenate([h.ravel(), v.ravel()])))
    if len(pts) < 2:
        return 0.0
    dists = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    np.fill_diagonal(dists, np.inf)
    return float(np.median(np.min(dists, axis=1)))


def _make_blob_detector(spacing_px: float | None = None) -> cv2.SimpleBlobDetector:
    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 0
    params.filterByArea = True
    if spacing_px is not None:
        r = spacing_px / 4.0
        params.minArea = float(np.pi * (r / 2) ** 2)
        params.maxArea = float(np.pi * (r * 2) ** 2)
    else:
        params.minArea = 20
        params.maxArea = 5000
    params.filterByCircularity = True
    params.minCircularity = 0.85
    params.filterByConvexity = False
    params.filterByInertia = False
    return cv2.SimpleBlobDetector_create(params)


def _detect_grid(
    gray: np.ndarray,
    detector: cv2.SimpleBlobDetector,
    spacing_mm: float,
    grid_size: tuple[int, int] | None,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    if grid_size is not None:
        found, corners = cv2.findCirclesGrid(
            gray, grid_size, flags=cv2.CALIB_CB_SYMMETRIC_GRID, blobDetector=detector
        )
        if not found:
            return None, None
        cols, rows = grid_size
        obj_pts = np.zeros((cols * rows, 3), np.float32)
        obj_pts[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * spacing_mm
        return obj_pts, corners

    return _cluster_grid(gray, detector, spacing_mm)


def _cluster_grid(
    gray: np.ndarray, detector: cv2.SimpleBlobDetector, spacing_mm: float
) -> tuple[np.ndarray | None, np.ndarray | None]:
    keypoints = detector.detect(gray)
    if len(keypoints) < 4:
        return None, None

    pts = np.array([kp.pt for kp in keypoints], dtype=np.float32)
    pts = pts[np.argsort(pts[:, 1])]

    gaps = np.diff(pts[:, 1])
    if len(gaps) == 0:
        return None, None
    threshold = np.median(gaps) * 5
    rows = np.split(pts, np.where(gaps > threshold)[0] + 1)

    row_lens = [len(r) for r in rows]
    n_cols = int(np.median(row_lens))
    if n_cols < 2 or any(abs(n - n_cols) > 1 for n in row_lens):
        return None, None

    img_pts, obj_pts = [], []
    for ri, row in enumerate(rows):
        row = row[np.argsort(row[:, 0])]
        if len(row) != n_cols:
            continue
        for ci, pt in enumerate(row):
            img_pts.append(pt)
            obj_pts.append([ci * spacing_mm, ri * spacing_mm, 0.0])

    if len(img_pts) < 4:
        return None, None

    return (
        np.array(obj_pts, np.float32),
        np.array(img_pts, np.float32).reshape(-1, 1, 2),
    )


def _draw_grid(
    frame: np.ndarray, img_pts: np.ndarray, grid_size: tuple[int, int] | None
) -> None:
    if grid_size is not None:
        cv2.drawChessboardCorners(frame, grid_size, img_pts.reshape(-1, 1, 2), True)
    pts = img_pts.reshape(-1, 2)
    for pt in pts:
        x, y = int(pt[0]), int(pt[1])
        cv2.circle(frame, (x, y), 7, (0, 255, 255), -1)
        cv2.circle(frame, (x, y), 7, (0, 0, 0), 1)


def _run_calibration(
    obj_points: list[np.ndarray],
    img_points: list[np.ndarray],
    image_size: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, list, list, float]:
    _, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, image_size, None, None
    )
    total = sum(
        cv2.norm(ip, cv2.projectPoints(op, rv, tv, K, dist)[0], cv2.NORM_L2) / len(ip)
        for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs)
    )
    return K, dist, rvecs, tvecs, total / len(obj_points)


def _compute_diagnostic_data(
    obj_points: list[np.ndarray],
    img_points: list[np.ndarray],
    K: np.ndarray,
    dist: np.ndarray,
    rvecs: list,
    tvecs: list,
    image_size: tuple[int, int],
    spacing_mm: float = 17.0,
    grid_size: tuple[int, int] | None = None,
) -> dict:
    all_pts, all_errs = [], []
    for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs):
        proj, _ = cv2.projectPoints(op, rv, tv, K, dist)
        detected = ip.reshape(-1, 2)
        all_pts.append(detected)
        all_errs.append(proj.reshape(-1, 2) - detected)

    pts = np.concatenate(all_pts)
    errs = np.concatenate(all_errs)

    w, h = image_size
    step = max(w, h) // 20
    gx, gy = np.meshgrid(np.arange(step // 2, w, step), np.arange(step // 2, h, step))
    grid_pts = np.stack([gx.ravel(), gy.ravel()], axis=1).astype(np.float32)
    undist_pts = cv2.undistortPoints(
        grid_pts.reshape(-1, 1, 2),
        K,
        dist,
        P=K,
    ).reshape(-1, 2)

    # Alignment metrics from last frame
    last_ip = img_points[-1].reshape(-1, 2)
    last_op = obj_points[-1]
    _, rvec, tvec = cv2.solvePnP(last_op, last_ip.reshape(-1, 1, 2), K, dist)
    R, _ = cv2.Rodrigues(rvec)
    tilt_total = float(np.degrees(np.arccos(np.clip(abs(R[2, 2]), 0.0, 1.0))))
    tilt_x_deg = float(np.degrees(np.arcsin(np.clip(R[0, 2], -1.0, 1.0))))
    tilt_y_deg = float(np.degrees(np.arcsin(np.clip(R[1, 2], -1.0, 1.0))))

    y_min, y_max = last_ip[:, 1].min(), last_ip[:, 1].max()
    top_row = last_ip[last_ip[:, 1] < y_min + (y_max - y_min) * 0.2]
    if len(top_row) >= 2:
        top_row = top_row[np.argsort(top_row[:, 0])]
        dx, dy = top_row[-1] - top_row[0]
        roll_rad = float(np.arctan2(dy, dx))
        roll_deg = float(abs(np.degrees(roll_rad)))
    else:
        roll_rad, roll_deg = 0.0, 0.0
    roll_top_row = top_row if len(top_row) >= 2 else None

    # px/cm scale heatmap data
    scale_data = None
    if grid_size is not None:
        cols, rows = grid_size
        pts_grid = last_ip.reshape(rows, cols, 2)
        cm_per_dot = spacing_mm / 10.0
        scale_vals, scale_pos = [], []
        for i in range(rows):
            for j in range(cols):
                neighbours = []
                if j + 1 < cols:
                    neighbours.append(
                        np.linalg.norm(pts_grid[i, j + 1] - pts_grid[i, j])
                    )
                if i + 1 < rows:
                    neighbours.append(
                        np.linalg.norm(pts_grid[i + 1, j] - pts_grid[i, j])
                    )
                if neighbours:
                    scale_vals.append(np.mean(neighbours) / cm_per_dot)
                    scale_pos.append(pts_grid[i, j])
        scale_data = {"vals": np.array(scale_vals), "pos": np.array(scale_pos)}

    return {
        "pts": pts,
        "errs": errs,
        "grid_pts": grid_pts,
        "disp": undist_pts - grid_pts,
        "image_size": image_size,
        "last_pts": last_ip,
        "grid_size": grid_size,
        "tilt_total": tilt_total,
        "tilt_x_deg": tilt_x_deg,
        "tilt_y_deg": tilt_y_deg,
        "roll_deg": roll_deg,
        "roll_rad": roll_rad,
        "roll_top_row": roll_top_row,
        "scale_data": scale_data,
    }


def _compute_live_metrics(
    obj_pts: np.ndarray, img_pts: np.ndarray, K: np.ndarray, dist: np.ndarray
) -> dict:
    _, rvec, tvec = cv2.solvePnP(obj_pts, img_pts, K, dist)

    proj, _ = cv2.projectPoints(obj_pts, rvec, tvec, K, dist)
    reproj_err = float(
        np.mean(np.linalg.norm(proj.reshape(-1, 2) - img_pts.reshape(-1, 2), axis=1))
    )

    R, _ = cv2.Rodrigues(rvec)
    tilt_deg = float(np.degrees(np.arccos(np.clip(abs(R[2, 2]), 0.0, 1.0))))
    tilt_x_deg = float(np.degrees(np.arcsin(np.clip(R[0, 2], -1.0, 1.0))))
    tilt_y_deg = float(np.degrees(np.arcsin(np.clip(R[1, 2], -1.0, 1.0))))

    flat = img_pts.reshape(-1, 2)
    y_min, y_max = flat[:, 1].min(), flat[:, 1].max()
    top_row = flat[flat[:, 1] < y_min + (y_max - y_min) * 0.2]
    if len(top_row) >= 2:
        top_row = top_row[np.argsort(top_row[:, 0])]
        dx, dy = top_row[-1] - top_row[0]
        roll_deg = float(abs(np.degrees(np.arctan2(dy, dx))))
    else:
        roll_deg = 0.0

    return {
        "reproj_err": reproj_err,
        "tilt_deg": tilt_deg,
        "tilt_x_deg": tilt_x_deg,
        "tilt_y_deg": tilt_y_deg,
        "roll_deg": roll_deg,
    }


def undistort_image(img: np.ndarray, K: np.ndarray, dist: np.ndarray) -> np.ndarray:
    # Undistort an image using the given camera matrix and
    # distortion coefficients.
    h, w = img.shape[:2]
    new_K, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
    return cv2.undistort(img, K, dist, None, new_K)


def undistort_points(points: np.ndarray, K: np.ndarray, dist: np.ndarray) -> np.ndarray:
    # Undistort 2D points using the given camera matrix and
    # distortion coefficients.
    """points: Nx2 array of (x, y)."""
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    return cv2.undistortPoints(pts, K, dist, P=K).reshape(-1, 2)


def default_result_path() -> Path:
    return Path(settings.get("DATA_DIRECTORY")) / "camera_calibration.json"
