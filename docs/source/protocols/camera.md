## Custom Camera Interaction

```{admonition} Note
:class: note
All custom camera interaction described on this page — triggers, annotations, and
custom drawing — applies exclusively to the **box camera** (`cam_box`). The corridor
camera (`cam_corridor`) does not support these features.
```

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
```

---

### Custom Camera Drawing

#### Annotating the frame from a task

The simplest way to overlay text on the camera feed is to call `write_text()` from
the task. The text is rendered on every subsequent frame and stays visible until it
is changed or cleared.

```python
from village.devices.camera import cam_box

# Show a label — persists across frames until changed
cam_box.write_text("reward delivered")

# Clear the annotation
cam_box.write_text("")
```

The annotation is also saved frame-by-frame in the session CSV alongside the
position data, so it can be used to mark task events for post-hoc analysis.

For anything beyond plain text — shapes, coloured overlays, position-dependent
graphics — use the `CameraDrawBase` subclass described below.

#### Drawing with CameraDrawBase

Every frame, after the built-in overlays are rendered, the `draw` method of
`CameraDrawBase` is called. By default it does nothing. You can subclass it to
draw any additional elements directly on the camera frame using OpenCV.

Create a file named `camera_draw` inside your project's `code` directory and define
a class named `CameraDraw` that inherits from `CameraDrawBase`. The system will
automatically detect it and use it instead of the default base class.

```python
from village.custom_classes.camera_draw_base import CameraDrawBase

import cv2

class CameraDraw(CameraDrawBase):

    def __init__(self) -> None:
        super().__init__()

    def draw(self, cam) -> None:
        """Called on every frame. Draw directly on cam.frame (BGR numpy array).

        Available on cam:
        - cam.frame          — the current frame as a numpy array (BGR, read/write)
        - cam.x_position     — detected animal x position in pixels (-1 if not found)
        - cam.y_position     — detected animal y position in pixels (-1 if not found)
        - cam.width          — frame width in pixels
        - cam.height         — frame height in pixels
        - cam.items_to_draw  — dict populated by the task, used to pass data here

        self.task gives access to the current task's variables and methods.
        """
        # Draw a red circle at the animal's position whenever it is detected
        if cam.x_position != -1:
            cv2.circle(
                cam.frame,
                (cam.x_position, cam.y_position),
                radius=20,
                color=(0, 0, 255),   # BGR
                thickness=2,
            )

        # Draw a custom shape passed from the task via items_to_draw
        rect = cam.items_to_draw.get("reward_zone")
        if rect is not None:
            x, y, w, h = rect
            cv2.rectangle(cam.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
```

`cam.items_to_draw` is a plain dictionary that the task can populate at any point
during a session to pass coordinates, labels, or any other data to the drawing
function without coupling the task directly to the camera module:

```python
# Inside the task, at any point:
from village.devices.camera import cam_box

cam_box.items_to_draw["reward_zone"] = (200, 150, 80, 80)
```
