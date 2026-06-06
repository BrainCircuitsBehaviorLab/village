from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPen

from village.classes.enums import Color
from village.custom_classes.task import Task
from village.scripts.time_utils import time_utils
from village.settings import settings

if TYPE_CHECKING:
    from village.devices.camera import Camera


class CameraDrawBase:
    """Base class for defining custom camera draw on frame behavior.

    Two methods are called automatically on every frame:

    ``draw(cam)``
        Uses cv2 to draw on ``cam.frame``; changes go to disk and screen.

    ``draw_preview(cam, painter)``
        Uses QPainter; goes to screen only — never saved to the video file.

    The following ``cam`` attributes are updated every frame and available
    inside both methods:

    **Identity & state**

    - ``cam.name`` — ``'BOX'`` or ``'CORRIDOR'``.
    - ``cam.task_is_running`` — ``True`` if a task is active, ``False`` if not.
    - ``cam.view_detection`` — whether detection overlays are enabled in the GUI.
    - ``cam.tracking`` — whether animal position tracking is active (BOX only).
    - ``cam.color`` — ``Color.BLACK`` or ``Color.WHITE``: which pixels to detect.

    **Frame data**

    - ``cam.frame`` — current frame as a BGR numpy array (read/write).
    - ``cam.width``, ``cam.height`` — frame dimensions in pixels.
    - ``cam.frame_number`` — frames captured since recording started.
    - ``cam.timing`` — milliseconds elapsed since recording started.

    **Session info**

    - ``cam.filename`` — base name of the current video file (empty if not recording).
    - ``cam.trial`` — current trial number (0 if no task running or CORRIDOR camera).
    - ``cam.annotation`` — short text rendered on every frame at a fixed position in
      the status bar. Set it from a task with ``cam_box.write_text("reward")``;
      it persists until changed. Also saved frame-by-frame to the session CSV, so
      it is useful for marking task events for post-hoc analysis.
    - ``cam.items_to_draw`` — plain ``dict`` for passing arbitrary data from the task
      to the drawing methods without coupling the task to this class. The task
      populates it at any point (e.g. ``cam_box.items_to_draw["target"] = (x, y, r)``)
      and ``draw`` / ``draw_preview`` can read it to render complex overlays such as
      circles, custom shapes, or stimulus boundaries.

    **Detection areas**

    - ``cam.number_of_areas`` — number of configurable areas (always 4).
    - ``cam.areas`` — list of ``[x1, y1, x2, y2]`` pixel coordinates per area.
    - ``cam.areas_active`` — bool list, whether each area is enabled.
    - ``cam.areas_allowed`` — bool list, whether animals are allowed in each area.

    **Detection results**

    - ``cam.masks`` — grayscale numpy arrays with the thresholded mask per area.
    - ``cam.counts`` — detected pixel count per area.
    - ``cam.x_position``, ``cam.y_position`` — tracked animal position in pixels
      (``-1`` if not detected).
    """

    def __init__(self) -> None:
        self.name = "Camera Draw"
        self.task = Task()
        self.color_areas = [
            tuple(settings.get("COLOR_AREA1")),
            tuple(settings.get("COLOR_AREA2")),
            tuple(settings.get("COLOR_AREA3")),
            tuple(settings.get("COLOR_AREA4")),
        ]

        self.thickness_line = settings.get("RECTANGLES_LINEWIDTH")
        self.detection_color = tuple(settings.get("COLOR_DETECTION"))
        self.detection_size = settings.get("DETECTION_CIRCLE_SIZE")

    # ------------------------------------------------------------------
    # Top-level methods — override these in subclasses
    # ------------------------------------------------------------------

    def draw(self, cam: Camera) -> None:
        """Default cv2 drawing — goes to disk and screen.

        Args:
            cam: The camera instance.
        """

        # Status texts and pixel counts always run for both cameras.
        # Detection (thresholded mask + areas) is CORRIDOR-only here so it goes to
        # disk. For BOX, detection goes to draw_preview (screen only).

        self.write_status_texts(cam)
        self.write_pixel_detection_texts(cam)
        if cam.name == "CORRIDOR" and cam.view_detection:
            self.draw_detection_mask_corridor(cam)
            self.draw_detection_areas_corridor(cam)

    def draw_preview(self, cam: Camera, painter: QPainter) -> None:
        """Default QPainter drawing — goes to screen only.

        Args:
            cam: The camera instance.
            painter: Active QPainter on the preview widget.
        """
        if cam.name == "BOX" and cam.view_detection:
            device = painter.device()
            if device is None:
                return

            scale_x = device.width() / cam.width
            scale_y = device.height() / cam.height

            self.draw_detection_mask_box(cam, painter, scale_x, scale_y)
            self.draw_detection_areas_box(cam, painter, scale_x, scale_y)
            self.draw_detection_position_box(cam, painter, scale_x, scale_y)

    # ------------------------------------------------------------------
    # cv2 helper methods — called from draw(), also available in subclasses
    # ------------------------------------------------------------------

    def write_status_texts(self, cam: Camera) -> None:
        """Draws the text status bar background and writes filename/timing text."""
        end_rect = (cam.width, int(cam.height / 12))
        cv2.rectangle(cam.frame, (0, 0), end_rect, (255, 255, 255), -1)

        scale = cam.width * 0.000625
        thickness_text = 1 if cam.width <= 640 else 2
        origin_text1 = (3, int(cam.height / 32))
        origin_text2 = (3, int(cam.height / 15))

        if cam.name == "BOX" and not cam.task_is_running:
            cam.frame_number = 0
            cam.timing = 0

        text_trial = "trial: " + str(cam.trial) if cam.trial != 0 else ""
        text_filename = cam.filename if cam.filename != "" else "No task running"
        text1 = text_filename + "  " + text_trial + "  " + cam.annotation
        text2 = (
            time_utils.format_duration(cam.timing) + "  frame: " + str(cam.frame_number)
        )

        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 0, 0)
        cv2.putText(cam.frame, text1, origin_text1, font, scale, color, thickness_text)
        cv2.putText(cam.frame, text2, origin_text2, font, scale, color, thickness_text)

    def write_pixel_detection_texts(self, cam: Camera) -> None:
        """Writes pixel count for each active area onto the frame."""
        color_areas = self.color_areas
        scale = cam.width * 0.000625
        thickness_text = 1 if cam.width <= 640 else 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        origin_areas = [
            (int(cam.width * 0.375), int(cam.height / 15)),
            (int(cam.width * 0.53125), int(cam.height / 15)),
            (int(cam.width * 0.6875), int(cam.height / 15)),
            (int(cam.width * 0.84375), int(cam.height / 15)),
        ]
        for i in range(cam.number_of_areas):
            if cam.areas_active[i]:
                cv2.putText(
                    cam.frame,
                    "area" + str(i + 1) + ": " + str(cam.counts[i]),
                    origin_areas[i],
                    font,
                    scale,
                    color_areas[i],
                    thickness_text,
                )

    def draw_detection_mask_corridor(self, cam: Camera) -> None:
        """Blends the thresholded detection mask into the frame via cv2.

        For black detection: darkens detected pixels using bitwise_and.
        For white detection: brightens detected pixels using bitwise_or.
        """
        for i, f in enumerate(cam.areas):
            if cam.areas_active[i]:
                try:
                    if cam.color == Color.BLACK:
                        mask = cv2.bitwise_not(
                            cv2.cvtColor(cam.masks[i], cv2.COLOR_GRAY2BGRA)
                        )
                        cam.frame[f[1] : f[3], f[0] : f[2]] = cv2.bitwise_and(
                            cam.frame[f[1] : f[3], f[0] : f[2]], mask
                        )
                    else:
                        mask = cv2.cvtColor(cam.masks[i], cv2.COLOR_GRAY2BGRA)
                        cam.frame[f[1] : f[3], f[0] : f[2]] = cv2.bitwise_or(
                            cam.frame[f[1] : f[3], f[0] : f[2]], mask
                        )
                except Exception:
                    pass

    def draw_detection_areas_corridor(self, cam: Camera) -> None:
        """Draws detection area rectangles onto the frame."""
        if not cam.view_detection:
            return
        color_areas = self.color_areas
        for i in range(cam.number_of_areas):
            if cam.areas_active[i]:
                cv2.rectangle(
                    cam.frame,
                    (cam.areas[i][0], cam.areas[i][1]),
                    (cam.areas[i][2], cam.areas[i][3]),
                    color_areas[i],
                    self.thickness_line,
                )
                if not cam.areas_allowed[i]:
                    cv2.line(
                        cam.frame,
                        (cam.areas[i][0], cam.areas[i][1]),
                        (cam.areas[i][2], cam.areas[i][3]),
                        color_areas[i],
                        self.thickness_line,
                    )
                    cv2.line(
                        cam.frame,
                        (cam.areas[i][2], cam.areas[i][1]),
                        (cam.areas[i][0], cam.areas[i][3]),
                        color_areas[i],
                        self.thickness_line,
                    )

    def draw_detection_mask_box(
        self,
        cam: Camera,
        painter: QPainter,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draws thresholded detection masks via QPainter (screen only).

        Converts each area's grayscale mask to a semi-transparent RGBA QImage
        and draws it at the scaled position on the preview widget.
        Black detection → dark overlay where the animal is.
        White detection → bright overlay where the animal is.
        """
        for i, f in enumerate(cam.areas):
            if not cam.areas_active[i]:
                continue
            mask = cam.masks[i]
            if not isinstance(mask, np.ndarray):
                continue
            try:
                h_mask, w_mask = mask.shape[:2]
                rgba = np.zeros((h_mask, w_mask, 4), dtype=np.uint8)
                if cam.color == Color.BLACK:
                    # detected pixels are white in mask → draw as dark overlay
                    rgba[:, :, 3] = mask
                else:
                    # detected pixels are white in mask → draw as bright overlay
                    rgba[:, :, 0] = 255
                    rgba[:, :, 1] = 255
                    rgba[:, :, 2] = 255
                    rgba[:, :, 3] = mask
                rgba = np.ascontiguousarray(rgba)
                qimage = QImage(
                    rgba.data,
                    w_mask,
                    h_mask,
                    rgba.strides[0],
                    QImage.Format_RGBA8888,
                )
                x1 = int(f[0] * scale_x)
                y1 = int(f[1] * scale_y)
                x2 = int(f[2] * scale_x)
                y2 = int(f[3] * scale_y)
                painter.drawImage(QRect(x1, y1, x2 - x1, y2 - y1), qimage)
            except Exception:
                pass

    def draw_detection_areas_box(
        self,
        cam: Camera,
        painter: QPainter,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draws area rectangles (and X for NOT_ALLOWED areas) via QPainter."""
        painter.setBrush(QBrush())  # transparent fill
        for i in range(cam.number_of_areas):
            if cam.areas_active[i]:
                b, g, r = self.color_areas[i]
                painter.setPen(QPen(QColor(r, g, b), self.thickness_line))
                x1 = int(cam.areas[i][0] * scale_x)
                y1 = int(cam.areas[i][1] * scale_y)
                x2 = int(cam.areas[i][2] * scale_x)
                y2 = int(cam.areas[i][3] * scale_y)
                painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                if not cam.areas_allowed[i]:
                    painter.drawLine(x1, y1, x2, y2)
                    painter.drawLine(x2, y1, x1, y2)

    def draw_detection_position_box(
        self,
        cam: Camera,
        painter: QPainter,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draws a filled circle at the tracked animal position via QPainter."""
        if not cam.tracking or cam.x_position == -1:
            return
        b, g, r = self.detection_color
        color = QColor(r, g, b)
        painter.setPen(QPen(color))
        painter.setBrush(QBrush(color))
        px = int(cam.x_position * scale_x)
        py = int(cam.y_position * scale_y)
        s = max(1, int(self.detection_size * min(scale_x, scale_y)))
        painter.drawEllipse(QPoint(px, py), s, s)
