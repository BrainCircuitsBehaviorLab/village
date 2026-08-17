from __future__ import annotations

import cv2
import numpy as np

_AREAS = range(4)
_MAX_SAMPLES = 2000


def area_count(gray: np.ndarray, rect: list[int],
               threshold: int, black: bool) -> tuple[int, np.ndarray]:
    """Replicates per-area pixel count (camera.py detect_black/white)."""
    x1, y1, x2, y2 = rect
    roi = gray[y1:y2, x1:x2]
    mode = cv2.THRESH_BINARY_INV if black else cv2.THRESH_BINARY
    _, mask = cv2.threshold(roi, threshold, 255, mode)
    return cv2.countNonZero(mask), mask


def select_from_grays(grays: list[np.ndarray], rects: list[list[int]],
                      thresholds: list[int], empty: int, black: bool
                      ) -> dict[int, tuple[int | None, bool]]:
    """For each area, pick the gray-frame index where only that area is
    occupied. Returns {area: (frame_index_or_None, isolated)}. isolated is
    True when a frame with the mouse alone in that area was found;
    False: returns best-effort fallback (max occupancy difference)"""
    best_iso: dict[int, tuple[int, int | None]] = {i: (-1, None)
                                                   for i in _AREAS}
    best_fb: dict[int, tuple[int, int | None]] = {
        i: (-(1 << 30), None) for i in _AREAS}
    for fi, gray in enumerate(grays):
        counts = [area_count(gray, rects[i], thresholds[i], black)[0]
                  for i in _AREAS]
        for i in _AREAS:
            others = [counts[j] for j in _AREAS if j != i]
            if counts[i] > empty and all(c <= empty for c in others):
                if counts[i] > best_iso[i][0]:
                    best_iso[i] = (counts[i], fi)
            diff = counts[i] - sum(others)
            if diff > best_fb[i][0]:
                best_fb[i] = (diff, fi)
    out: dict[int, tuple[int | None, bool]] = {}
    for i in _AREAS:
        if best_iso[i][1] is not None:
            out[i] = (best_iso[i][1], True)
        else:
            out[i] = (best_fb[i][1], False)
    return out


def scan_video(path: str, rects: list[list[int]], thresholds: list[int],
               empty: int, black: bool) -> dict[int, np.ndarray | None]:
    """Scans a video, keeping only the best BGR frame per area.
    same as select_from_grays but retains one frame per area instead of all."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return {i: None for i in _AREAS}
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // _MAX_SAMPLES) if total > 0 else 1

    best_iso: dict[int, tuple[int, np.ndarray | None]] = {i: (-1, None)
                                                          for i in _AREAS}
    best_fb: dict[int, tuple[int, np.ndarray | None]] = {
        i: (-(1 << 30), None) for i in _AREAS
    }
    idx = 0
    while True:
        if not cap.grab():
            break
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            counts = [area_count(gray, rects[i], thresholds[i], black)[0]
                      for i in _AREAS]
            for i in _AREAS:
                others = [counts[j] for j in _AREAS if j != i]
                if counts[i] > empty and all(c <= empty for c in others):
                    if counts[i] > best_iso[i][0]:
                        best_iso[i] = (counts[i], frame.copy())
                diff = counts[i] - sum(others)
                if diff > best_fb[i][0]:
                    best_fb[i] = (diff, frame.copy())
        idx += 1
    cap.release()
    return {i: (best_iso[i][1] if best_iso[i][1] is not None
                else best_fb[i][1])
            for i in _AREAS}
