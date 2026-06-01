from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog, QLabel

from village.calibration.camera_calibration import (
    CameraCalibration,
    default_result_path,
)
from village.calibration.camera_calibration_grid import make_circle_grid
from village.classes.enums import State
from village.devices.camera import Camera, cam_box
from village.gui.layout import Layout
from village.manager import manager
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

    # (0,0) residual reprojection error
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

    # (0,1) lens distortion field
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

    # (1,0) tilt + roll
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

    # (1,1) px/cm scale heatmap
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
        self.draw()

    def draw(self) -> None:
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


class CameraCalibrationLayout(Layout):
    def __init__(self, window: GuiWindow) -> None:
        super().__init__(window)
        manager.state = State.MANUAL_MODE
        manager.changing_settings = False
        self.draw()

    def draw(self) -> None:
        self.camera_calibration_button.setDisabled(True)

        self._result_path: Path = default_result_path()
        self._result: dict | None = None
        self._last_annotated: np.ndarray | None = None

        self.create_and_add_label(
            "GRID GENERATION",
            5,
            2,
            40,
            2,
            "black",
            description="Generate a printable symmetric circle grid.\n"
            "Print it and verify spacing with a ruler.",
        )
        self.create_and_add_label(
            "PAGE W (mm)",
            8,
            2,
            14,
            2,
            "black",
            bold=False,
            description="Page width in mm (e.g. 210 for A4)",
        )
        self.page_w_edit = self.create_and_add_line_edit(
            "210", 10, 2, 8, 2, lambda _: None
        )

        self.create_and_add_label(
            "PAGE H (mm)",
            8,
            12,
            14,
            2,
            "black",
            bold=False,
            description="Page height in mm (e.g. 297 for A4)",
        )
        self.page_h_edit = self.create_and_add_line_edit(
            "297", 10, 12, 8, 2, lambda _: None
        )

        self.create_and_add_label(
            "SPACING (mm)",
            8,
            22,
            16,
            2,
            "black",
            bold=False,
            description="Centre-to-centre distance between circles in mm",
        )
        self.spacing_edit = self.create_and_add_line_edit(
            "50", 10, 22, 8, 2, lambda _: None
        )

        self.create_and_add_label(
            "DOT RADIUS (mm)",
            8,
            32,
            18,
            2,
            "black",
            bold=False,
            description="Radius of each printed circle in mm",
        )
        self.dot_radius_edit = self.create_and_add_line_edit(
            "10", 10, 32, 8, 2, lambda _: None
        )

        self.create_and_add_label(
            "MARGIN (mm)",
            8,
            42,
            14,
            2,
            "black",
            bold=False,
            description="Empty border around the grid in mm",
        )
        self.margin_edit = self.create_and_add_line_edit(
            "0", 10, 42, 8, 2, lambda _: None
        )

        self.generate_button = self.create_and_add_button(
            "GENERATE GRID PDF",
            13,
            2,
            30,
            2,
            self._generate_grid_clicked,
            "Generate a printable circle grid PDF",
            "powderblue",
        )
        self.grid_status_label = self.create_and_add_label(
            "", 16, 2, 50, 2, "gray", bold=False
        )

        self.create_and_add_label(
            "CALIBRATION DETECTION",
            19,
            2,
            50,
            2,
            "black",
            description="Parameters of the real grid in front of the camera.\n"
            "Rows/cols may differ from the printed sheet if stitched several.",
        )
        self.create_and_add_label(
            "GRID COLS",
            21,
            2,
            14,
            2,
            "black",
            bold=False,
            description="Columns in the stitched calibration grid",
        )
        self.grid_cols_edit = self.create_and_add_line_edit(
            "30", 23, 2, 8, 2, lambda _: None
        )

        self.create_and_add_label(
            "GRID ROWS",
            21,
            12,
            14,
            2,
            "black",
            bold=False,
            description="Rows in the stitched calibration grid",
        )
        self.grid_rows_edit = self.create_and_add_line_edit(
            "18", 23, 12, 8, 2, lambda _: None
        )

        self.create_and_add_label(
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
        self.spacing_px_edit = self.create_and_add_line_edit(
            "17", 23, 22, 8, 2, lambda _: None
        )

        self.create_and_add_label(
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
        self.measured_spacing_edit = self.create_and_add_line_edit(
            "", 23, 34, 8, 2, lambda _: None
        )

        self.capture_button = self.create_and_add_button(
            "CAPTURE FRAME",
            26,
            2,
            28,
            2,
            self._capture_clicked,
            "Grab current frame, detect grid, and run calibration",
            "powderblue",
        )
        self.load_image_button = self.create_and_add_button(
            "LOAD IMAGE",
            26,
            32,
            20,
            2,
            self._load_image_clicked,
            "Load a PNG/JPG image file and use it as a calibration frame",
            "powderblue",
        )
        self.clear_button = self.create_and_add_button(
            "CLEAR FRAMES",
            26,
            54,
            20,
            2,
            self._clear_clicked,
            "Discard all captured frames and start over",
            "lightyellow",
        )
        self.frames_label = self.create_and_add_label(
            "Frames: 0", 29, 2, 30, 2, "black", bold=False
        )

        self.calib_status_label = self.create_and_add_label(
            "", 32, 2, 95, 2, "gray", bold=False
        )

        self.result_label = self.create_and_add_label(
            "", 35, 2, 95, 5, "black", bold=False
        )

        self.metrics_label = self.create_and_add_label(
            "", 41, 2, 95, 10, "black", bold=False
        )

        self.save_button = self.create_and_add_button(
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
        self.addWidget(self.preview_label, 6, 103, 20, 95)

        self.plot_layout = DiagnosticPlotsLayout(self.window, 24, 95)
        self.addLayout(self.plot_layout, 28, 103, 24, 95)

        self._calib: CameraCalibration = CameraCalibration(
            spacing_mm=self._spacing_value(), grid_size=self._grid_size_value()
        )

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
        if self._calib.running:
            return
        if not isinstance(cam_box, Camera):
            self.calib_status_label.setText("No frame available")
            return
        frame = cam_box.frame
        self._process_frame(frame)

    def _process_frame(self, frame: np.ndarray) -> None:
        self._last_annotated = None
        self._calib.spacing_mm = self._spacing_value()
        self._calib.spacing_px = self._spacing_px_value()
        self._calib.measured_spacing_mm = self._measured_spacing_value()
        self._calib.grid_size = self._grid_size_value()
        annotated, found = self._calib.process_frame(frame)

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

        n = self._calib.n_detected
        self.frames_label.setText(f"Frames: {n}")
        if n < 4:
            self.calib_status_label.setText(
                f"Grid detected, need {4 - n} more frame(s) to calibrate"
            )
            self.calib_status_label.setStyleSheet(
                "QLabel {color: gray; font-weight: normal}"
            )
            return

        self._calib.calibrate_in_thread()
        self.calib_status_label.setText(f"Calibrating… ({n} frames)")
        self.calib_status_label.setStyleSheet(
            "QLabel {color: gray; font-weight: normal}"
        )
        self.capture_button.setDisabled(True)

    def _load_image_clicked(self) -> None:
        if self._calib.running:
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
        self._calib.clear()
        self._result = None
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
        if self._result is None:
            return
        try:
            self._calib.save(self._result_path)
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
        if self._calib.diagnostic_data is not None:
            self.plot_layout.update(self._calib.diagnostic_data)

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

    def update_gui(self) -> None:
        if self._calib is None:
            return
        self.update_status_label_buttons()

        display = (
            self._last_annotated if self._last_annotated is not None
            else cam_box.frame if isinstance(cam_box, Camera) else None
        )
        if display is not None:
            try:
                px = _frame_to_pixmap(display)
                if not px.isNull():
                    self.preview_label.setPixmap(
                        px.scaled(
                            self.preview_label.width(), self.preview_label.height(), 1
                        )
                    )
            except Exception:
                pass

        if self._calib.live_metrics is not None:
            self._show_live_metrics(self._calib.live_metrics)

        if self._calib.error:
            self.calib_status_label.setText("Calibration failed, check log")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )
            self.capture_button.setEnabled(True)
            self._calib.error = False
            return

        if (
            not self._calib.running
            and self._calib.result is not self._result
            and self._calib.result is not None
        ):
            self._result = self._calib.result
            self._show_result(self._result)
            self.capture_button.setEnabled(True)
