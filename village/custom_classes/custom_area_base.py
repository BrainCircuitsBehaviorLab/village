from __future__ import annotations

import cv2
import numpy as np


class CustomAreaBase:
    """Base class for an arbitrary-shaped detection area (e.g. a T shape).
    The 4 built-in cam.areas are rectangles. Subclass this to add
    one extra area of any shape to the BOX camera.
    I use it so the animal is detected and the centroid follow it anywhere
    inside the shape, not only inside the rectangles. Maybe not super useful.
    Subclass in the project code directory so it is picked up by import_all.
    """

    name = "CUSTOM"
    active = True
    threshold = 65
    # Shape as one or more polygons of [x, y] vertices; concave is fine, and
    # several polygons make a disjoint area (e.g. a T as bar + stem).
    polygons: list[list[list[int]]] = []

    def __init__(self) -> None:
        self._cached_shape: tuple[int, int] | None = None
        self._cached_mask: np.ndarray | None = None

    def build_mask(self, height: int, width: int) -> np.ndarray:
        """Rasterize self.polygons to a uint8 (h, w) mask, 255 inside else 0.

        cv2.fillPoly handles concave shapes. Override only for a shape that
        isn't polygonal (e.g. build it with numpy slicing or cv2.circle)."""
        mask = np.zeros((height, width), np.uint8)
        for poly in self.polygons:
            cv2.fillPoly(mask, [np.asarray(poly, np.int32)], 255)
        return mask

    def mask(self, height: int, width: int) -> np.ndarray:
        """Cache mask for the given frame size."""
        if self._cached_shape != (height, width):
            m = self.build_mask(height, width)
            self._cached_mask = np.asarray(m, dtype=np.uint8)
            self._cached_shape = (height, width)
        assert self._cached_mask is not None
        return self._cached_mask

    def contains(self, x: int, y: int, height: int, width: int) -> bool:
        """True if pixel (x, y) is inside the area."""
        if not (0 <= x < width and 0 <= y < height):
            return False
        return bool(self.mask(height, width)[y, x])
