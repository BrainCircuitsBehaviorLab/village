from __future__ import annotations

from typing import TYPE_CHECKING

from village.custom_classes.task import Task

if TYPE_CHECKING:
    from village.devices.camera import Camera


class CameraDrawBase:
    """Base class for defining custom camera draw on frame behavior.

    This class can be overridden to implement specific actions.
    """

    def __init__(self) -> None:
        """Initializes the CameraDrawBase instance."""
        self.name = "Camera Draw"
        self.task = Task()

    def draw(self, cam: Camera) -> None:
        """Draws on the camera frame based on the camera's state.
        Args:
            cam (Camera): The camera instance providing the
            frame and state.
        """
        pass
