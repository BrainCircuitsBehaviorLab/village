from __future__ import annotations

import cv2
import numpy as np


class CustomAreaBase:
    """Overrides the shape of one of the 4 BOX camera detection areas.

    The 4 BOX areas (AREA1_BOX..AREA4_BOX) are rectangles by default, edited
    from the GUI. Subclass this to replace the *shape* of one of them with a
    union of polygons and/or circles defined in code (e.g. an L-shaped
    region), while its status (ALLOWED/NOT_ALLOWED/TRIGGER/OFF) and its
    threshold keep working exactly as before and stay editable from the GUI
    — only the position controls for that area are hidden, since the shape
    is no longer a plain rectangle.
    Subclass in the project code directory so it is picked up by import_all.
    """

    name = "CUSTOM"
    # Which of the 4 BOX areas this replaces: 1, 2, 3, or 4.
    area_index = 1
    # Shape as one or more polygons of [x, y] vertices; concave is fine, and
    # several polygons make a disjoint area (e.g. an L as two rectangles).
    polygons: list[list[list[int]]] = []
    # Shape as one or more circles, each (x, y, radius). Combined with
    # polygons in the same mask, so a subclass can set both.
    circles: list[tuple[int, int, int]] = []

    def __init__(self) -> None:
        # Set by Camera.set_properties() to the BOX camera's frame size,
        # before mask()/bbox()/contains() are used.
        self.height = 0
        self.width = 0
        self._cached_shape: tuple[int, int] | None = None
        self._cached_mask: np.ndarray | None = None
        self._cached_bbox: tuple[int, int, int, int] | None = None

    def build_mask(self, height: int, width: int) -> np.ndarray:
        """Rasterize self.polygons and self.circles to a uint8 (h, w) mask,
        255 inside else 0.

        cv2.fillPoly/cv2.circle handle concave shapes and circles
        respectively. Override only for a shape that is neither (e.g. build
        it with numpy slicing)."""
        mask = np.zeros((height, width), np.uint8)
        for poly in self.polygons:
            cv2.fillPoly(mask, [np.asarray(poly, np.int32)], 255)
        for x, y, radius in self.circles:
            cv2.circle(mask, (x, y), radius, 255, -1)
        return mask

    def _ensure_cached(self) -> None:
        """Rebuilds the mask and its bounding box when the frame size changes."""
        shape = (self.height, self.width)
        if self._cached_shape != shape:
            m = self.build_mask(self.height, self.width)
            self._cached_mask = np.asarray(m, dtype=np.uint8)
            x, y, w, h = cv2.boundingRect(self._cached_mask)
            self._cached_bbox = (x, y, x + w, y + h)
            self._cached_shape = shape

    def mask(self) -> np.ndarray:
        """Cached mask, sized self.height x self.width."""
        self._ensure_cached()
        assert self._cached_mask is not None
        return self._cached_mask

    def bbox(self) -> tuple[int, int, int, int]:
        """Cached (x1, y1, x2, y2) bounding box of the shape."""
        self._ensure_cached()
        assert self._cached_bbox is not None
        return self._cached_bbox

    def contains(self, x: int, y: int) -> bool:
        """True if pixel (x, y) is inside the area."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return bool(self.mask()[y, x])
