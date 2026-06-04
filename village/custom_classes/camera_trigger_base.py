from __future__ import annotations

from typing import TYPE_CHECKING

from village.custom_classes.task import Task

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
        self.task = Task()

    def trigger(self, cam: Camera) -> None:
        """Evaluates camera triggers and performs corresponding actions.

        Called on every frame to check whether the subject has entered any
        defined area or reached a specific position in the camera feed.

        Available area triggers (return True when the subject is detected):
        - cam.area1_is_triggered
        - cam.area2_is_triggered
        - cam.area3_is_triggered
        - cam.area4_is_triggered

        Available position properties:
        - cam.x_position, cam.y_position (subject position in pixels)
        - cam.width, cam.height (camera feed dimensions in pixels)

        Other:
        - cam.write_text("text") to overlay text on the camera feed

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
