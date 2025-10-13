from village.classes.abstract_classes import CameraBase


class CameraTriggerBase:
    def __init__(self) -> None:
        self.name = "Camera Trigger"

    def trigger(self, cam: CameraBase) -> None:

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
