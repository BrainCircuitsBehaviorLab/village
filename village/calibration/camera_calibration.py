from __future__ import annotations

import json
import traceback
from pathlib import Path
from threading import Thread

import cv2
import numpy as np

from village.scripts.log import log
from village.settings import settings
from village.custom_classes.calibration_base import CalibrationBase


class CameraCalibration(CalibrationBase):
    name = "camera_calibration"

    def __init__(self, spacing_mm: float,
                 grid_size: tuple[int, int] | None = None) -> None:
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
        pass

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

        obj_pts, img_pts = _detect_grid(gray, self._detector,
                                        self.spacing_mm, self.grid_size)
        found = obj_pts is not None
        if found:
            self._obj_points.append(obj_pts)
            self._img_points.append(img_pts)
            _draw_grid(annotated, img_pts, self.grid_size)
            self.last_spacing_px = _compute_spacing_px(img_pts, self.grid_size)
            if self.result is not None:
                K = np.array(self.result["camera_matrix"])
                dist = np.array(self.result["dist_coeffs"])
                self.live_metrics = _compute_live_metrics(obj_pts, img_pts,
                                                          K, dist)

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
        keys = ("camera_matrix", "dist_coeffs", "reprojection_error_px",
                "image_size_wh", "n_images_used", "spacing_mm")
        data = {k: self.result[k] for k in keys if k in self.result}
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    def _run(self) -> None:
        try:
            K, dist, rvecs, tvecs, err = _run_calibration(
                self._obj_points, self._img_points, self._image_size)
            d = dist.ravel()
            w, h = self._image_size
            _tang = float(np.sqrt(d[2] ** 2 + d[3] ** 2)) if len(d) >= 4 else 0.0
            self.result = {"camera_matrix": K.tolist(), "dist_coeffs": d.tolist(),
                           "reprojection_error_px": float(err),
                           "image_size_wh": list(self._image_size),
                           "n_images_used": self.n_detected,
                           "spacing_mm": self.spacing_mm,
                           "k1": float(d[0]),
                           "tangential": _tang,
                           "cx_offset_px": float(K[0, 2] - w / 2),
                           "cy_offset_px": float(K[1, 2] - h / 2)}

            self.diagnostic_data = _compute_diagnostic_data(
                                    self._obj_points, self._img_points,
                                    K, dist, rvecs, tvecs, self._image_size,
                                    spacing_mm=self.measured_spacing_mm or self.spacing_mm,
                                    grid_size=self.grid_size)
        except Exception:
            log.error("Camera calibration error",
                      exception=traceback.format_exc())
            self.error = True
        finally:
            self.running = False


def _compute_spacing_px(img_pts: np.ndarray,
                        grid_size: tuple[int, int] | None) -> float:
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


def _detect_grid(gray: np.ndarray, detector: cv2.SimpleBlobDetector,
                 spacing_mm: float, grid_size: tuple[int, int] | None
                 ) -> tuple[np.ndarray | None, np.ndarray | None]:
    if grid_size is not None:
        found, corners = cv2.findCirclesGrid(gray, grid_size,
                                             flags=cv2.CALIB_CB_SYMMETRIC_GRID,
                                             blobDetector=detector)
        if not found:
            return None, None
        cols, rows = grid_size
        obj_pts = np.zeros((cols * rows, 3), np.float32)
        obj_pts[:, :2] = (np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * spacing_mm)
        return obj_pts, corners

    return _cluster_grid(gray, detector, spacing_mm)


def _cluster_grid(gray: np.ndarray, detector: cv2.SimpleBlobDetector,
                  spacing_mm: float) -> tuple[np.ndarray | None, np.ndarray | None]:
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

    return (np.array(obj_pts, np.float32),
            np.array(img_pts, np.float32).reshape(-1, 1, 2))


def _draw_grid(frame: np.ndarray, img_pts: np.ndarray,
               grid_size: tuple[int, int] | None) -> None:
    if grid_size is not None:
        cv2.drawChessboardCorners(frame, grid_size,
                                  img_pts.reshape(-1, 1, 2), True)
    pts = img_pts.reshape(-1, 2)
    for pt in pts:
        x, y = int(pt[0]), int(pt[1])
        cv2.circle(frame, (x, y), 7, (0, 255, 255), -1)
        cv2.circle(frame, (x, y), 7, (0, 0, 0), 1)


def _run_calibration(obj_points: list[np.ndarray], img_points: list[np.ndarray],
                     image_size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, list, list, float]:
    _, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points,
                                                   image_size, None, None)
    total = sum(cv2.norm(ip, cv2.projectPoints(op, rv, tv, K, dist)[0], cv2.NORM_L2) / len(ip)
                for op, ip, rv, tv in zip(obj_points, img_points, rvecs, tvecs))
    return K, dist, rvecs, tvecs, total / len(obj_points)


def _compute_diagnostic_data(obj_points: list[np.ndarray],
                             img_points: list[np.ndarray],
                             K: np.ndarray, dist: np.ndarray,
                             rvecs: list, tvecs: list,
                             image_size: tuple[int, int],
                             spacing_mm: float = 17.0,
                             grid_size: tuple[int, int] | None = None) -> dict:
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
    gx, gy = np.meshgrid(np.arange(step // 2, w, step),
                          np.arange(step // 2, h, step))
    grid_pts = np.stack([gx.ravel(), gy.ravel()], axis=1).astype(np.float32)
    undist_pts = cv2.undistortPoints(
        grid_pts.reshape(-1, 1, 2), K, dist, P=K,
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
                        np.linalg.norm(pts_grid[i, j + 1] - pts_grid[i, j]))
                if i + 1 < rows:
                    neighbours.append(
                        np.linalg.norm(pts_grid[i + 1, j] - pts_grid[i, j]))
                if neighbours:
                    scale_vals.append(np.mean(neighbours) / cm_per_dot)
                    scale_pos.append(pts_grid[i, j])
        scale_data = {"vals": np.array(scale_vals), "pos": np.array(scale_pos)}

    return {"pts": pts, "errs": errs, "grid_pts": grid_pts, 
            "disp": undist_pts - grid_pts, "image_size": image_size,
            "last_pts": last_ip, "grid_size": grid_size,
            "tilt_total": tilt_total, "tilt_x_deg": tilt_x_deg,
            "tilt_y_deg": tilt_y_deg, "roll_deg": roll_deg,
            "roll_rad": roll_rad, "roll_top_row": roll_top_row,
            "scale_data": scale_data}


def _compute_live_metrics(obj_pts: np.ndarray, img_pts: np.ndarray,
                          K: np.ndarray, dist: np.ndarray) -> dict:
    _, rvec, tvec = cv2.solvePnP(obj_pts, img_pts, K, dist)

    proj, _ = cv2.projectPoints(obj_pts, rvec, tvec, K, dist)
    reproj_err = float(np.mean(np.linalg.norm(
                        proj.reshape(-1, 2) - img_pts.reshape(-1, 2), axis=1)))

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

    return {"reproj_err": reproj_err, "tilt_deg": tilt_deg,
            "tilt_x_deg": tilt_x_deg, "tilt_y_deg": tilt_y_deg,
            "roll_deg": roll_deg}


def undistort_image(img: np.ndarray, K: np.ndarray,
                    dist: np.ndarray) -> np.ndarray:
    # Undistort an image using the given camera matrix and
    # distortion coefficients.
    h, w = img.shape[:2]
    new_K, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
    return cv2.undistort(img, K, dist, None, new_K)


def undistort_points(points: np.ndarray, K: np.ndarray,
                     dist: np.ndarray) -> np.ndarray:
    # Undistort 2D points using the given camera matrix and
    # distortion coefficients.
    """points: Nx2 array of (x, y)."""
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    return cv2.undistortPoints(pts, K, dist, P=K).reshape(-1, 2)


def default_result_path() -> Path:
    return Path(settings.get("DATA_DIRECTORY")) / "camera_calibration.json"
