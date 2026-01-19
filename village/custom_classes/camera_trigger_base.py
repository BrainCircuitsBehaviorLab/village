from village.devices.camera import Camera


class CameraTriggerBase:
    """Base class for defining custom camera trigger behavior.

    This class can be overridden to implement specific actions when detection areas
    are triggered or to monitor subject position.
    """

    def __init__(self) -> None:
        """Initializes the CameraTriggerBase instance."""
        self.name = "Camera Trigger"

    def trigger(self, cam: Camera) -> None:
        """Evaluates camera triggers and performs corresponding actions.

        This method is called to check if any defined areas in the camera view
        have been triggered (e.g., by the subject entering them).

        Args:
            cam (CameraBase): The camera instance providing the trigger status.
        """
        # the camera automatically returns a True value if the subject is detected
        # within any of the predefined trigger areas.
        # then we can assign a function to be executed when the area is triggered
        if cam.area1_is_triggered:
            cam.write_text("Area 1 triggered")

        if cam.area2_is_triggered:
            cam.write_text("Area 2 triggered")

        if cam.area3_is_triggered:
            cam.write_text("Area 3 triggered")

        if cam.area4_is_triggered:
            cam.write_text("Area 4 triggered")

        # or you can check the position of the animal manually
