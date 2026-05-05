from village.classes.abstract_classes import CameraBase


class CameraDrawBase:
    """Base class for defining custom camera draw on frame behavior.

    This class can be overridden to implement specific actions.
    """

    def __init__(self) -> None:
        """Initializes the CameraDrawBase instance."""
        self.name = "Camera Draw"

    def draw(self, cam: CameraBase) -> None:
        """Draws on the camera frame based on the camera's state.
        Args:
            cam (CameraBase): The camera instance providing the frame and state.
        """
        pass
