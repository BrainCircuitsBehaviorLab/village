## Custom Camera Interaction


### Camera Triggers

Every time a frame is captured from the box camera, if `CAM_BOX_TRACKING` is enabled,
the (x, y) position of the animal inside the operant box is computed and the `trigger`
method of `CameraTriggerBase` is called.

The default implementation checks each of the four configurable areas (the rectangles
defined in the GUI). For any area set to TRIGGER status, if the animal is detected
inside it, the text "Area X triggered" is overlaid on the camera feed.

```{admonition} Note
:class: note
Active areas can be set to ALLOWED, NOT_ALLOWED, or TRIGGER.
```

You can override this behavior by creating a custom class in your project. Create a
file named `camera_trigger` inside your project's `code` directory and define a class
named `CameraTrigger` that inherits from `CameraTriggerBase`.
If the system detects a class inheriting from `CameraTriggerBase` in your project, it will use your custom class instead of the default base class.

```python
from village.custom_classes.camera_trigger_base import CameraTriggerBase

class CameraTrigger(CameraTriggerBase):
    """Implement specific actions when an animal enters
    a detection area or reaches a specific position in the camera feed.

    You have access to self.task, so any variable or function defined in the
    task can be used to specify the actions to perform.
    """

    def __init__(self) -> None:
        super().__init__()

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
        distance = ((cam.x_position - cam.width / 2) ** 2 +
                    (cam.y_position - cam.height / 2) ** 2) ** 0.5
        if distance < 50:
            cam.write_text("Animal in the center area")
