from collections import deque

import cv2
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QBrush, QColor, QPen, QPolygon

from village.custom_classes.camera_draw_base import CameraDrawBase

TRAIL_LENGTH = 60  # frames


class CameraDraw(CameraDrawBase):
    """Keeps the default drawing of both cameras and adds two things to the
    box camera while a task is running:

    - draw (cv2, saved in the video): the circles the task asks for in
      cam_box.items_to_draw["circles"], a list of (x, y, radius) in pixels.
      For example, from a task:

          self.cam_box.items_to_draw["circles"] = [(320, 240, 30)]
          self.cam_box.items_to_draw["circles"] = []  # remove them

    - draw_preview (QPainter, only on screen, not saved): the trail of the
      last TRAIL_LENGTH positions of the animal (only when tracking).
    """

    def __init__(self) -> None:
        super().__init__()
        self.trail: deque[tuple[int, int]] = deque(maxlen=TRAIL_LENGTH)

    def draw(self, cam) -> None:
        super().draw(cam)  # status bar, pixel counts, corridor detection

        if cam.name != "BOX":
            return
        if not cam.task_is_running:
            self.trail.clear()
            return

        # draw runs once per frame: a good place to collect the positions
        if cam.x_position != -1:
            self.trail.append((int(cam.x_position), int(cam.y_position)))

        for x, y, radius in cam.items_to_draw.get("circles") or []:
            cv2.circle(cam.frame, (x, y), radius, (0, 0, 255), 2)  # BGR: red

    def draw_preview(self, cam, painter) -> None:
        super().draw_preview(cam, painter)  # box detection overlays

        trail = list(self.trail)  # copy: draw keeps adding from another thread
        if cam.name != "BOX" or len(trail) < 2:
            return
        device = painter.device()
        if device is None:
            return
        scale_x = device.width() / cam.width
        scale_y = device.height() / cam.height
        points = [QPoint(int(x * scale_x), int(y * scale_y)) for x, y in trail]
        painter.setPen(QPen(QColor(255, 165, 0), 2))  # RGB: orange
        painter.setBrush(QBrush())  # no fill
        painter.drawPolyline(QPolygon(points))
