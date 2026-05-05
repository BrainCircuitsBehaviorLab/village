from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from village.devices.camera import Camera
    from village.classes.null_classes import NullCamera


class CameraDrawBase:
    """Base class for defining custom camera draw on frame behavior.

    This class can be overridden to implement specific actions.
    """

    def __init__(self) -> None:
        """Initializes the CameraDrawBase instance."""
        self.name = "Camera Draw"

    def draw(self, cam: Camera | NullCamera) -> None:
        """Draws on the camera frame based on the camera's state.
        Args:
            cam (Camera | NullCamera): The camera instance providing the frame and state.
        """
        pass
