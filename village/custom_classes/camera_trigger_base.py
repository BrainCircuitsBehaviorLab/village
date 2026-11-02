from __future__ import annotations

from typing import TYPE_CHECKING

from village.custom_classes.task_base import TaskBase

if TYPE_CHECKING:
    from village.devices.camera import Camera


class CameraTriggerBase:
    """Base class for defining custom camera trigger behavior.

    Override this class to implement specific actions when an animal enters
    a detection area or reaches a specific position in the camera feed.

    You have access to self.task, so any variable or function defined in the
    task can be used to specify the actions to perform.
    """

    def __init__(self) -> None:
        """Initializes the CameraTriggerBase instance."""
        self.name = "Camera Trigger"
        self.task = TaskBase()

    def trigger(self, cam: Camera) -> None:
        """Evaluates camera triggers and performs corresponding actions.

        Called on every frame of the box camera while the task is running,
        also when no animal is detected, so it can act both when an area is
        occupied and when it is empty.

        Available area triggers (True if the area is a TRIGGER area and the
        tracked position of the subject is inside it; False when no animal is
        tracked, so tracking must be ON):
        - cam.area1_is_triggered
        - cam.area2_is_triggered
        - cam.area3_is_triggered
        - cam.area4_is_triggered

        Available area occupancy (any active area, from its pixel count and
        the two limits of DETECTION_OF_MOUSE_BOX; works without tracking):
        - cam.area1_animals ... cam.area4_animals: 0 (empty), 1 (one animal),
          2 (two or more animals) or -1 (the area is OFF)

        Available position properties:
        - cam.x_position, cam.y_position (subject position in pixels, -1 if
          no animal is tracked)
        - cam.width, cam.height (camera feed dimensions in pixels)

        Other:
        - cam.write_text("text") to overlay text on the camera feed
        - self.task.system_state: the current state of the Village system
          (see TaskBase)

        Args:
            cam (Camera): The camera instance providing trigger status
                and position data.
        """

        # Check if the animal is in any of the 4 defined areas
        if cam.area1_is_triggered:
            cam.write_text("Area 1 triggered")

        if cam.area2_is_triggered:
            cam.write_text("Area 2 triggered")

        if cam.area3_is_triggered:
            cam.write_text("Area 3 triggered")

        if cam.area4_is_triggered:
            cam.write_text("Area 4 triggered")

        # Check if the animal is within a 50-pixel radius of the center
        # distance = ((cam.x_position - cam.width / 2) ** 2 +
        #             (cam.y_position - cam.height / 2) ** 2) ** 0.5
        # if distance < 50:
        #     cam.write_text("Animal in the center area")
