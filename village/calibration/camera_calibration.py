"""Camera calibration: the CAMERA_CALIBRATION panel of the CALIBRATION screen.

Prints a sheet with a grid of dots (make_circle_grid). The grid (one sheet, or
several joined for a bigger surface) lies on the floor of the box, and the panel
detects it in frames of the box camera and calibrates the lens from them with
OpenCV (calibrateCamera): the camera matrix and the distortion coefficients, the
alignment of the camera with the floor, the px/cm scale and the conversion from
pixels to millimetres on the floor, saved to camera_calibration.json.

- CameraCalibration: the calibration itself (frames, detection, results).
- CameraCalibrationPanel: the widgets of the panel.
"""

from __future__ import annotations

import json
import math
import time
import traceback
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog, QLabel

from village import __version__
from village.custom_classes.calibration_base import CalibrationBase
from village.gui.layout import Layout
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.scripts.utils import create_pixmap
from village.settings import settings

if TYPE_CHECKING:
    from village.gui.gui_window import GuiWindow

# How long a captured frame stays on the preview before it goes back to live.
CAPTURED_FRAME_SECONDS = 2.0

# Frames needed to calibrate. The grid lies on the floor, so one frame already
# has the whole floor surface it covers; more frames only average the noise.
MIN_FRAMES = 1

# Initial focal length of the calibration, as a fraction of the image width. With
# the grid flat on the floor, the focal length can hardly be told apart from the
# height of the camera, so it starts from a typical value for the box camera
# instead of from OpenCV's own guess, which can then end up far away.
FOCAL_GUESS = 0.6

# Settings whose field can be left blank, saved as 0.
OPTIONAL_SETTINGS = (
    "CAMERA_CALIBRATION_SPACING_PX",
    "CAMERA_CALIBRATION_MEASURED_SPACING",
)

# Saved in camera_calibration.json, so that it can be understood on its own.
JSON_DESCRIPTION = {
    "camera_matrix": "[[fx, 0, cx], [0, fy, cy], [0, 0, 1]], in pixels: focal "
    "lengths and optical centre (OpenCV calibrateCamera)",
    "dist_coeffs": "[k1, k2, p1, p2, k3]: radial (k) and tangential (p) lens "
    "distortion (OpenCV). k1 < 0 barrel, k1 > 0 pincushion",
    "reprojection_error_px": "mean distance in pixels between the detected dots "
    "and where the calibrated model places them (< 1 is good)",
    "image_size_wh": "size of the calibrated frames in pixels: the calibration is "
    "only valid at this resolution",
    "spacing_mm": "dot spacing of the grid when the calibration ran",
    "measured_spacing_mm": "spacing measured with a ruler; only used for the px/cm "
    "heatmap (null = spacing_mm)",
    "spacing_px": "expected dot spacing in pixels given to the detector "
    "(null = dots of any usual size)",
    "tangential": "size of the tangential distortion, sqrt(p1^2 + p2^2)",
    "principal_point_offset_px": "[cx - width/2, cy - height/2]: distance from the "
    "optical centre to the centre of the image",
    "alignment": "position of the camera with respect to the floor, from the last "
    "frame: tilt left/right (x), front/back (y) and total, and roll, in degrees",
    "px_per_cm": "pixels per cm on the floor across the grid in the last frame "
    "(mean, min, max), from measured_spacing_mm or spacing_mm",
    "floor_homography": "3x3 matrix from undistorted pixels (cv2.undistortPoints "
    "with P=camera_matrix) to mm on the floor, from the last frame",
    "floor_origin": "the floor coordinates of floor_homography",
    "calibrated_region_px": "polygon (pixels) covered by the grid in the frames: "
    "the correction is only reliable inside it",
    "frames": "the frames used, in order: their source (and the box camera "
    "settings that change the calibration), grid size, spacing and dots found",
}

FLOOR_ORIGIN = (
    "mm from the centre of the dot of the grid nearest the top-left corner of the "
    "image (last frame); x along the rows of dots (GRID COLS dots), y along the "
    "columns: with the rows horizontal in the image, x goes right and y down"
)


class CameraCalibration(CalibrationBase):
    name = "camera_calibration"

    def __init__(
        self, spacing_mm: float = 50, grid_size: tuple[int, int] | None = None
    ) -> None:
        super().__init__()
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
        self._frames_info: list[dict] = []
        self.panel: CameraCalibrationPanel | None = None

    @classmethod
    def is_active(cls) -> bool:
        return True

    def draw(self) -> None:
        if not self.running:
            self.clear()
        self.panel = CameraCalibrationPanel(self)

    def update_gui(self) -> None:
        if self.panel is not None:
            self.panel.update_gui()

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

    def matches_image_size(self, frame: np.ndarray) -> bool:
        """False if frame has a different size than the frames already captured:
        they cannot be calibrated together."""
        return self._image_size in (None, (frame.shape[1], frame.shape[0]))

    def process_frame(
        self, frame: np.ndarray, source: dict | None = None
    ) -> tuple[np.ndarray, bool]:
        """Detects the grid in frame and, if found, keeps it for the calibration.
        source: where the frame comes from, saved with it in the json."""
        annotated = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        obj_pts, img_pts = _detect_grid(
            gray, self._detector, self.spacing_mm, self.grid_size
        )
        found = obj_pts is not None
        if found:
            self._image_size = (gray.shape[1], gray.shape[0])
            self._obj_points.append(obj_pts)
            self._img_points.append(img_pts)
            cols, rows = self.grid_size if self.grid_size is not None else (None, None)
            self._frames_info.append(
                {
                    **(source or {}),
                    "grid_cols": cols,
                    "grid_rows": rows,
                    "spacing_mm": self.spacing_mm,
                    "n_points": len(self._img_points[-1]),
                }
            )
            _draw_grid(annotated, img_pts, self.grid_size)
            self.last_spacing_px = _compute_spacing_px(img_pts, self.grid_size)

        return annotated, found

    def clear(self) -> None:
        self._obj_points.clear()
        self._img_points.clear()
        self._frames_info.clear()
        self._image_size = None
        self.result = None
        self.diagnostic_data = None
        self.live_metrics = None

    def calibrate_in_thread(self) -> None:
        if self.running or self.n_detected < MIN_FRAMES:
            return
        self.running = True
        self.error = False
        self.result = None
        Thread(target=self._run, daemon=True).start()

    def save(self, out_path: Path) -> None:
        if self.result is None:
            return
        keys = (
            "date",
            "system_name",
            "village_version",
            "camera_matrix",
            "dist_coeffs",
            "reprojection_error_px",
            "image_size_wh",
            "n_images_used",
            "spacing_mm",
            "measured_spacing_mm",
            "spacing_px",
            "tangential",
            "principal_point_offset_px",
            "alignment",
            "px_per_cm",
            "floor_homography",
            "floor_origin",
            "calibrated_region_px",
            "frames",
        )
        data = {k: self.result[k] for k in keys if k in self.result}
        data["description"] = JSON_DESCRIPTION
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
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
            spacing = self.measured_spacing_mm or self.spacing_mm
            last_obj, last_img = self._obj_points[-1], self._img_points[-1]
            live = _compute_live_metrics(last_obj, last_img, K, dist, self.grid_size)
            diag = _compute_diagnostic_data(
                self._obj_points,
                self._img_points,
                K,
                dist,
                rvecs,
                tvecs,
                self._image_size,
                spacing_mm=spacing,
                grid_size=self.grid_size,
            )
            scale = diag["scale_data"]
            px_per_cm = (
                {
                    "mean": round(float(np.mean(scale["vals"])), 3),
                    "min": round(float(np.min(scale["vals"])), 3),
                    "max": round(float(np.max(scale["vals"])), 3),
                }
                if scale is not None and len(scale["vals"])
                else None
            )
            region = cv2.convexHull(
                np.concatenate([p.reshape(-1, 2) for p in self._img_points])
            )
            self.result = {
                "date": time_utils.now_string(),
                "system_name": settings.get("SYSTEM_NAME"),
                "village_version": __version__,
                "camera_matrix": K.tolist(),
                "dist_coeffs": d.tolist(),
                "reprojection_error_px": float(err),
                "image_size_wh": list(self._image_size),
                "n_images_used": self.n_detected,
                "spacing_mm": self.spacing_mm,
                "measured_spacing_mm": self.measured_spacing_mm,
                "spacing_px": self._spacing_px,
                "frames": [dict(f) for f in self._frames_info],
                "k1": float(d[0]),
                "tangential": _tang,
                "cx_offset_px": float(K[0, 2] - w / 2),
                "cy_offset_px": float(K[1, 2] - h / 2),
                "principal_point_offset_px": [
                    round(float(K[0, 2] - w / 2), 2),
                    round(float(K[1, 2] - h / 2), 2),
                ],
                "alignment": {
                    "tilt_x_deg": round(live["tilt_x_deg"], 2),
                    "tilt_y_deg": round(live["tilt_y_deg"], 2),
                    "tilt_total_deg": round(live["tilt_deg"], 2),
                    "roll_deg": round(live["roll_deg"], 2),
                },
                "px_per_cm": px_per_cm,
                "floor_homography": _floor_homography(
                    last_obj * (spacing / self.spacing_mm), last_img, K, dist
                ).tolist(),
                "floor_origin": FLOOR_ORIGIN,
                "calibrated_region_px": region.reshape(-1, 2).round(1).tolist(),
            }
            diag["region"] = region.reshape(-1, 2)
            self.diagnostic_data = diag
            self.live_metrics = live
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
        return obj_pts, _orient_grid(corners, cols, rows)

    return _cluster_grid(gray, detector, spacing_mm)


def _orient_grid(corners: np.ndarray, cols: int, rows: int) -> np.ndarray:
    """Reorders the dots found by findCirclesGrid, which can start from any
    corner, so that the first one is the dot nearest the top-left corner of the
    image (the origin of the floor coordinates, see FLOOR_ORIGIN)."""
    pg = corners.reshape(rows, cols, 2)
    if cols == rows:
        # a square grid can also come transposed: keep its rows horizontal
        d = pg[0, -1] - pg[0, 0]
        if abs(d[1]) > abs(d[0]):
            pg = pg.transpose(1, 0, 2)
    options = [pg, pg[:, ::-1], pg[::-1], pg[::-1, ::-1]]
    pg = min(options, key=lambda g: float(g[0, 0].sum()))
    return np.ascontiguousarray(pg, dtype=np.float32).reshape(-1, 1, 2)


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
    w, h = image_size
    f = FOCAL_GUESS * w
    K0 = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], dtype=np.float64)
    _, K, dist, rvecs, tvecs = cv2.calibrateCamera(
        obj_points,
        img_points,
        image_size,
        K0,
        None,
        flags=cv2.CALIB_USE_INTRINSIC_GUESS,
    )
    total = sum(
        cv2.norm(ip, cv2.projectPoints(op, rv, tv, K, dist)[0], cv2.NORM_L2) / len(ip)
        for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs, strict=False)
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
    for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs, strict=False):
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

    roll_rad, roll_top_row = _grid_roll(last_ip, grid_size)
    roll_deg = float(np.degrees(roll_rad))

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


def _grid_roll(
    img_pts: np.ndarray, grid_size: tuple[int, int] | None
) -> tuple[float, np.ndarray | None]:
    """The roll (rad) of the grid in the image, from its first row of dots, and
    that row. Wrapped to +-45 degrees: a grid lying across the image has the
    same roll as one lying along it."""
    pts = img_pts.reshape(-1, 2)
    if grid_size is not None:
        cols, rows = grid_size
        row = pts.reshape(rows, cols, 2)[0]
    else:
        # no grid size: the dots near the top of the image
        y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
        row = pts[pts[:, 1] < y_min + (y_max - y_min) * 0.2]
        row = row[np.argsort(row[:, 0])]
    if len(row) < 2:
        return 0.0, None
    dx, dy = row[-1] - row[0]
    angle = float(np.arctan2(dy, dx))
    return (angle + np.pi / 4) % (np.pi / 2) - np.pi / 4, row


def _compute_live_metrics(
    obj_pts: np.ndarray,
    img_pts: np.ndarray,
    K: np.ndarray,
    dist: np.ndarray,
    grid_size: tuple[int, int] | None = None,
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

    roll_deg = float(np.degrees(_grid_roll(img_pts, grid_size)[0]))

    return {
        "reproj_err": reproj_err,
        "tilt_deg": tilt_deg,
        "tilt_x_deg": tilt_x_deg,
        "tilt_y_deg": tilt_y_deg,
        "roll_deg": roll_deg,
    }


def _floor_homography(
    obj_pts: np.ndarray, img_pts: np.ndarray, K: np.ndarray, dist: np.ndarray
) -> np.ndarray:
    """The 3x3 matrix from undistorted pixels to mm on the floor (the plane of
    the grid), fitted on the dots of one frame."""
    und = cv2.undistortPoints(img_pts.reshape(-1, 1, 2), K, dist, P=K)
    H, _ = cv2.findHomography(und.reshape(-1, 2), obj_pts[:, :2].astype(np.float32))
    return H


def pixels_to_floor_mm(points: np.ndarray, calibration: dict) -> np.ndarray:
    """Converts image points (Nx2, pixels of the box camera) to mm on the floor
    with a saved calibration (the content of camera_calibration.json)."""
    K = np.array(calibration["camera_matrix"])
    dist = np.array(calibration["dist_coeffs"])
    H = np.array(calibration["floor_homography"])
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    und = cv2.undistortPoints(pts, K, dist, P=K)
    return cv2.perspectiveTransform(und, H).reshape(-1, 2)


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
    return Path(settings.get("SYSTEM_DIRECTORY")) / "camera_calibration.json"


class CameraCalibrationPanel:
    """The widgets of the CAMERA_CALIBRATION panel, in calib.layout (44 x 172)."""

    def __init__(self, calib: CameraCalibration) -> None:
        # imported here: the box camera is created after this file is imported
        from village.devices.camera import Camera, cam_box

        self._calib = calib
        self.layout = calib.layout
        self._cam_box = cam_box if isinstance(cam_box, Camera) else None
        self._camera_frame()  # starts the copies without the status bar
        self.draw()

    def _camera_frame(self) -> np.ndarray | None:
        """The last frame of the box camera without the status bar (the dots
        under it are needed), or with it until the first copy arrives. Each
        call asks the camera to keep making the copies a little longer: they
        stop by themselves once the panel is no longer shown."""
        if self._cam_box is None:
            return None
        # update_gui calls this once every UPDATE_TIME_TABLE seconds
        seconds = 3 * float(settings.get("UPDATE_TIME_TABLE")) + 1
        self._cam_box.request_clean_frame(seconds)
        frame = self._cam_box.clean_frame
        return frame if frame is not None else getattr(self._cam_box, "frame", None)

    def draw(self) -> None:
        self._result_path: Path = default_result_path()
        self._result: dict | None = None
        self._last_annotated: np.ndarray | None = None
        self._annotated_until = 0.0

        self.layout.create_and_add_label(
            "GRID GENERATION",
            0,
            1,
            40,
            2,
            "black",
            description="Generate a printable symmetric circle grid.\n"
            "Print it at 100% scale and verify the spacing with a ruler.",
        )
        self.layout.create_and_add_label(
            "PAGE W (mm)",
            2,
            1,
            15,
            2,
            "black",
            bold=False,
            description="Page width in mm (e.g. 210 for A4)",
        )
        self.page_w_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_PAGE_W"),
            4,
            1,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_PAGE_W", text, float),
        )

        self.layout.create_and_add_label(
            "PAGE H (mm)",
            2,
            16,
            15,
            2,
            "black",
            bold=False,
            description="Page height in mm (e.g. 297 for A4)",
        )
        self.page_h_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_PAGE_H"),
            4,
            16,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_PAGE_H", text, float),
        )

        self.layout.create_and_add_label(
            "SPACING (mm)",
            2,
            31,
            15,
            2,
            "black",
            bold=False,
            description="Centre-to-centre distance between circles in mm",
        )
        self.spacing_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_SPACING"),
            4,
            31,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_SPACING", text, float),
        )

        self.layout.create_and_add_label(
            "DOT RADIUS (mm)",
            2,
            46,
            19,
            2,
            "black",
            bold=False,
            description="Radius of each printed circle in mm",
        )
        self.dot_radius_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_DOT_RADIUS"),
            4,
            46,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_DOT_RADIUS", text, float),
        )

        self.layout.create_and_add_label(
            "MARGIN (mm)",
            2,
            65,
            15,
            2,
            "black",
            bold=False,
            description="Empty border around the grid in mm.\n"
            "At least the dot radius, for complete dots. Use 0 only to overlap\n"
            "several sheets into a bigger grid: the dots on the edges are cut.",
        )
        self.margin_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_MARGIN"),
            4,
            65,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_MARGIN", text, float),
        )

        self.generate_button = self.layout.create_and_add_button(
            "GENERATE GRID PDF",
            7,
            1,
            30,
            2,
            self._generate_grid_clicked,
            "Generate a printable circle grid PDF and set GRID COLS and GRID ROWS",
            "powderblue",
        )
        self.grid_status_label = self.layout.create_and_add_label(
            "", 9, 1, 80, 2, "gray", bold=False
        )

        self.layout.create_and_add_label(
            "CALIBRATION DETECTION",
            12,
            1,
            50,
            2,
            "black",
            description="Parameters of the grid lying on the floor of the box.\n"
            "Rows/cols may differ from the printed sheet if stitched several.",
        )
        self.layout.create_and_add_label(
            "GRID COLS",
            14,
            1,
            11,
            2,
            "black",
            bold=False,
            description="Columns of dots in the grid. All of them must be visible.",
        )
        self.grid_cols_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_GRID_COLS"),
            16,
            1,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_GRID_COLS", text, int),
        )

        self.layout.create_and_add_label(
            "GRID ROWS",
            14,
            13,
            13,
            2,
            "black",
            bold=False,
            description="Rows of dots in the grid. All of them must be visible.",
        )
        self.grid_rows_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_GRID_ROWS"),
            16,
            13,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_GRID_ROWS", text, int),
        )

        self.layout.create_and_add_label(
            "SPACING (px)",
            14,
            26,
            14,
            2,
            "black",
            bold=False,
            description="Expected centre-to-centre dot spacing in pixels.\n"
            "Used to tune the blob detector area bounds.\n"
            "Leave blank to accept dots of any usual size.",
        )
        self.spacing_px_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_SPACING_PX"),
            16,
            26,
            8,
            2,
            lambda text: _store_setting("CAMERA_CALIBRATION_SPACING_PX", text, float),
        )

        self.layout.create_and_add_label(
            "MEASURED SPACING (mm)",
            14,
            41,
            32,
            2,
            "black",
            bold=False,
            description="Actual printed dot spacing measured with a ruler.\n"
            "Leave blank to use SPACING (mm) above.\n"
            "Only affects the px/cm scale and the mm on the floor.",
        )
        self.measured_spacing_edit = self.layout.create_and_add_line_edit(
            _setting_text("CAMERA_CALIBRATION_MEASURED_SPACING"),
            16,
            41,
            8,
            2,
            lambda text: _store_setting(
                "CAMERA_CALIBRATION_MEASURED_SPACING", text, float
            ),
        )

        self.capture_button = self.layout.create_and_add_button(
            "CAPTURE FRAME",
            19,
            1,
            26,
            2,
            self._capture_clicked,
            "Grab the current frame, detect the grid and run the calibration\n"
            "with all the frames captured so far.",
            "powderblue",
        )
        self.load_image_button = self.layout.create_and_add_button(
            "LOAD IMAGE",
            19,
            29,
            20,
            2,
            self._load_image_clicked,
            "Load a PNG/JPG image file and use it as a calibration frame",
            "powderblue",
        )
        self.clear_button = self.layout.create_and_add_button(
            "CLEAR FRAMES",
            19,
            51,
            20,
            2,
            self._clear_clicked,
            "Discard all captured frames and start over",
            "lightyellow",
        )
        self.frames_label = self.layout.create_and_add_label(
            f"Frames: {self._calib.n_detected}", 21, 1, 30, 2, "black", bold=False
        )

        self.calib_status_label = self.layout.create_and_add_label(
            "", 23, 1, 80, 2, "gray", bold=False
        )

        self.result_label = self.layout.create_and_add_label(
            "", 25, 1, 80, 7, "black", bold=False
        )

        self.metrics_label = self.layout.create_and_add_label(
            "", 32, 1, 80, 9, "black", bold=False
        )

        self.save_button = self.layout.create_and_add_button(
            "SAVE JSON",
            41,
            1,
            20,
            2,
            self._save_clicked,
            "Save calibration result to camera_calibration.json",
            "powderblue",
        )
        self.save_button.setDisabled(True)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "QLabel {border: 1px solid gray; background-color: black;}"
        )
        self.preview_label.setFixedSize(
            88 * self.layout.column_width, 19 * self.layout.row_height
        )
        self.layout.addWidget(self.preview_label, 0, 83, 19, 88)

        self.plot_layout = DiagnosticPlotsLayout(self._calib.window, 24, 88)
        self.layout.addLayout(self.plot_layout, 20, 83, 24, 88)

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
            cols, rows = grid_dimensions(page_w, page_h, spacing, margin)
            self.grid_cols_edit.setText(str(cols))
            self.grid_rows_edit.setText(str(rows))
            self.grid_status_label.setText(f"Saved ({cols} x {rows} dots): {out}")
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
        frame = self._camera_frame()
        if frame is None:
            self.calib_status_label.setText("No frame available")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )
            return
        # the camera keeps writing to its frame: keep this one still
        source = {
            "source": "box camera",
            "CAM_BOX_RESOLUTION": settings.get("CAM_BOX_RESOLUTION"),
            "LENS_POSITION_BOX": settings.get("LENS_POSITION_BOX"),
        }
        self._process_frame(frame.copy(), source)

    def _process_frame(self, frame: np.ndarray, source: dict) -> None:
        if not self._calib.matches_image_size(frame):
            self.calib_status_label.setText(
                "Different image size than the captured frames: CLEAR FRAMES first"
            )
            self.calib_status_label.setStyleSheet(
                "QLabel {color: orange; font-weight: normal}"
            )
            return

        self._calib.spacing_mm = self._spacing_value()
        self._calib.spacing_px = self._spacing_px_value()
        self._calib.measured_spacing_mm = self._measured_spacing_value()
        self._calib.grid_size = self._grid_size_value()
        annotated, found = self._calib.process_frame(frame, source)

        self._last_annotated = annotated
        self._annotated_until = time.monotonic() + CAPTURED_FRAME_SECONDS
        self._show_frame(annotated)

        if not found:
            grid = self._calib.grid_size
            expected = f"{grid[0]} x {grid[1]} " if grid is not None else ""
            self.calib_status_label.setText(
                f"No {expected}grid detected: check that all dots are visible, "
                "GRID COLS/ROWS, SPACING (px)"
            )
            self.calib_status_label.setStyleSheet(
                "QLabel {color: orange; font-weight: normal}"
            )
            return

        n = self._calib.n_detected
        self.frames_label.setText(f"Frames: {n}")
        if n < MIN_FRAMES:
            self.calib_status_label.setText(
                f"Grid detected, need {MIN_FRAMES - n} more frame(s) to calibrate"
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
        self.save_button.setDisabled(True)

    def _show_frame(self, frame: np.ndarray) -> None:
        try:
            px = _frame_to_pixmap(frame)
            if not px.isNull():
                self.preview_label.setPixmap(
                    px.scaled(
                        self.preview_label.width(),
                        self.preview_label.height(),
                        Qt.KeepAspectRatio,
                    )
                )
        except Exception:
            pass

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
        self._process_frame(frame, {"source": "image file", "file": Path(path).name})

    def _clear_clicked(self) -> None:
        if self._calib.running:
            return
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
            self.calib_status_label.setStyleSheet(
                "QLabel {color: green; font-weight: normal}"
            )
        except Exception:
            self.calib_status_label.setText("Error saving result")
            self.calib_status_label.setStyleSheet(
                "QLabel {color: red; font-weight: normal}"
            )

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
            f"Calib reproj error (all frames): {err:.4f} px  ({quality})\n"
            f"Distortion: {level} {dtype}  (k1={k1:+.4f})\n"
            f"k1={d[0]:+.4f}  k2={d[1]:+.4f}  "
            f"p1={d[2]:+.4f}  p2={d[3]:+.4f}\n"
            f"Principal pt offset: "
            f"({result['cx_offset_px']:+.1f} px, "
            f"{result['cy_offset_px']:+.1f} px)  "
            f"tangential: {result['tangential']:.5f}"
        )
        scale = result.get("px_per_cm")
        if scale is not None:
            text += (
                f"\nFloor scale: {scale['mean']:.2f} px/cm "
                f"({scale['min']:.2f} - {scale['max']:.2f})"
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
            "Camera alignment with the floor",
            f"  Tilt total:       {m['tilt_deg']:5.2f}°  "
            f"[{tag(m['tilt_deg'], 2.0, 5.0)}]  (good<2°, ok<5°)",
            f"    Tilt X (L/R):   {tx:+6.2f}°  "
            f"[{tag(abs(tx), 2.0, 5.0)}]  {hint_x(tx)}",
            f"    Tilt Y (F/B):   {ty:+6.2f}°  "
            f"[{tag(abs(ty), 2.0, 5.0)}]  {hint_y(ty)}",
            f"  Roll:             {roll:+6.2f}°  "
            f"[{tag(abs(roll), 1.0, 3.0)}]  {hint_roll(roll)}",
            "Pose quality (latest frame vs calibrated model)",
            f"  Reproj error:     {m['reproj_err']:5.3f} px  "
            f"[{tag(m['reproj_err'], 0.5, 1.5)}]  (good<0.5, ok<1.5)",
        ]
        self.metrics_label.setText("\n".join(lines))

    def update_gui(self) -> None:
        if self._last_annotated is not None and (
            time.monotonic() >= self._annotated_until
        ):
            self._last_annotated = None
        frame = self._camera_frame()  # also while a capture is shown: keeps copies
        if self._last_annotated is None and frame is not None:
            self._show_frame(frame)

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


def _setting_text(key: str) -> str:
    """The value of a setting as the text of its field (blank for an unset 0)."""
    value = settings.get(key)
    return "" if value == 0 and key in OPTIONAL_SETTINGS else f"{value:g}"


def _store_setting(key: str, text: str, kind: type) -> None:
    """Saves a field in its setting as soon as it holds a valid value, so the
    panel opens with the last values used."""
    text = text.strip()
    if text == "" and key in OPTIONAL_SETTINGS:
        settings.set(key, 0)
        return
    try:
        value = kind(text)
    except ValueError:
        return
    if value > 0 or (value == 0 and key == "CAMERA_CALIBRATION_MARGIN"):
        settings.set(key, value)


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
    cb_args = {"fraction": 0.03, "pad": 0.03}

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
    region = diag.get("region")
    if region is not None:
        # the correction is only reliable where the grid was
        ax.plot(*np.vstack([region, region[:1]]).T, "k--", lw=1)
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
            log.error(
                "Camera calibration plots error", exception=traceback.format_exc()
            )


# ----------------------------------------------------------------------------
# The printable grid
# ----------------------------------------------------------------------------


def grid_dimensions(
    page_w_mm: float, page_h_mm: float, spacing_mm: float, margin_mm: float
) -> tuple[int, int]:
    """(columns, rows) of dots on a sheet: those whose center is inside the page
    minus the margin. With a margin of at least the dot radius all of them are
    complete; with 0, the ones on the left and bottom edges are cut in half, to
    overlap several sheets into a bigger grid."""
    cols = int((page_w_mm - 2 * margin_mm) / spacing_mm) + 1
    rows = int((page_h_mm - 2 * margin_mm) / spacing_mm) + 1
    return cols, rows


def make_circle_grid(
    page_w_mm: float = 210.0,
    page_h_mm: float = 297.0,
    spacing_mm: float = 50.0,
    circle_radius_mm: float = 10.0,
    margin_mm: float = 15.0,
    out_path: str = "calibration_grid.pdf",
    dpi: int = 300,
    rotated_45: bool = False,
) -> Path:
    mm_per_inch = 25.4

    # The axes fill the whole figure, so 1 mm in the data is 1 mm on the page.
    fig = plt.figure(figsize=(page_w_mm / mm_per_inch, page_h_mm / mm_per_inch))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, page_w_mm)
    ax.set_ylim(0, page_h_mm)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    draw_w = page_w_mm - 2 * margin_mm
    draw_h = page_h_mm - 2 * margin_mm

    if rotated_45:
        diag = spacing_mm / math.sqrt(2)
        cx_center = page_w_mm / 2
        cy_center = page_h_mm / 2
        temp = max(draw_w, draw_h) * math.sqrt(2)
        half_extent = math.ceil(temp / diag) + 2
        for row in range(-half_extent, half_extent + 1):
            for col in range(-half_extent, half_extent + 1):
                cx = cx_center + (col * diag - row * diag)
                cy = cy_center + (col * diag + row * diag)
                cond1 = (
                    margin_mm - circle_radius_mm
                    <= cx
                    <= page_w_mm - margin_mm + circle_radius_mm
                )
                cond2 = (
                    margin_mm - circle_radius_mm
                    <= cy
                    <= page_h_mm - margin_mm + circle_radius_mm
                )
                if cond1 and cond2:
                    ax.add_patch(plt.Circle((cx, cy), circle_radius_mm, color="black"))
    else:
        cols, rows = grid_dimensions(page_w_mm, page_h_mm, spacing_mm, margin_mm)
        for row in range(rows):
            ax.plot(
                [margin_mm - spacing_mm, margin_mm + cols * spacing_mm],
                [margin_mm + row * spacing_mm] * 2,
                color="lightgray",
                linewidth=1,
                zorder=1,
            )
            for col in range(cols):
                cx = margin_mm + col * spacing_mm
                cy = margin_mm + row * spacing_mm
                ax.add_patch(plt.Circle((cx, cy), circle_radius_mm, color="black"))
                ax.plot(
                    [margin_mm + col * spacing_mm] * 2,
                    [margin_mm - spacing_mm, margin_mm + rows * spacing_mm],
                    color="lightgray",
                    linewidth=1,
                    zorder=1,
                )

                ax.plot(
                    [cx - circle_radius_mm, cx + circle_radius_mm],
                    [cy, cy],
                    color="w",
                    linewidth=1,
                    zorder=2,
                )
                ax.plot(
                    [cx, cx],
                    [cy - circle_radius_mm, cy + circle_radius_mm],
                    color="w",
                    linewidth=1,
                    zorder=2,
                )

    out = Path(out_path)
    fig.savefig(out, dpi=dpi)
    plt.close(fig)
    return out
