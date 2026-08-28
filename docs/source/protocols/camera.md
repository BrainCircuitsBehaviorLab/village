## Custom Camera Interaction

### Camera Triggers

Every time a frame is captured from the box camera, if `CAM_BOX_TRACKING` is enabled
and a task is running,
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

In the following example, a subclass is created that writes a text when the subject
is detected in Area1, executes direct function number 2 when detected in Area2,
and triggers function number 6 when detected within a circular region at the center
of the image.

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

        Available area triggers (return True if the area is marked as a TRIGGER area
        and a subject is detected within it):
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

        # Check if the animal is in some of the defined areas
        if cam.area1_is_triggered:
            cam.write_text("Area 1 triggered") # write an annotation text to the cam

        if cam.area2_is_triggered:
            self.task.execute_function(2) # execute the direct function number 2

        # Check if the animal is within a 50-pixel radius of the center
        distance = ((cam.x_position - cam.width / 2) ** 2 +
                    (cam.y_position - cam.height / 2) ** 2) ** 0.5
        if distance < 50:
            self.task.execute_function(6) # execute the direct function number 6
```

```{admonition} Note
:class: note
`cam.areaN_is_triggered` also works transparently for a BOX area whose shape
has been replaced by a `CustomAreaBase` (see
[Custom Detection Area](#custom-detection-area)) — it checks the actual
polygon/circle, not just its bounding box.
```

---

### Custom Detection Area

The 4 BOX areas are rectangles by default, positioned and resized from the
GUI. If one of them needs to track the animal through a non-rectangular
region (e.g. an L-shaped corridor between two zones, or a circular zone),
subclass `CustomAreaBase` to **replace that area's shape** with a union of
polygons and/or circles defined in code.

```{admonition} Note
:class: note
This replaces the shape of one of the 4 existing areas — it does not add a
5th area. Its status (`ALLOWED`/`NOT_ALLOWED`/`TRIGGER`/`OFF`) and its
threshold keep working exactly as before, still set from the GUI (`SETTINGS`
-> box area usage/threshold). Only its position controls are hidden from the
GUI, since the shape is no longer a plain rectangle — a "defined with code"
label is shown in their place instead, listing the area's `polygons`/
`circles` coordinates (there's no draggable position control for them).
```

Create a file inside your project's `code` directory and define a class that
inherits from `CustomAreaBase`, setting `area_index` to the area it replaces
(1-4). The system detects it automatically.

```python
from village.custom_classes.custom_area_base import CustomAreaBase


class LCorridor(CustomAreaBase):
    name = "L_CORRIDOR"
    area_index = 2  # replaces AREA2_BOX

    # One or more polygons of [x, y] pixel vertices. Concave shapes are fine,
    # and several polygons make a disjoint area (here: an L as two rectangles).
    polygons = [
        [[100, 50], [300, 50], [300, 100], [100, 100]],   # top bar
        [[100, 100], [150, 100], [150, 250], [100, 250]],  # side
    ]

    # Optional: one or more circles, each (x, y, radius). Combined with
    # polygons in the same area — a subclass can set both at once.
    circles = [(200, 300, 40)]
```

```{admonition} Note
:class: note
Only one `CustomAreaBase` per `area_index` is used — if two subclasses target
the same area, only the first one found is registered and an error is
logged. An invalid `area_index` (not 1-4) is also rejected and logged.
```

---

### Custom Camera Drawing

#### Annotating the frame from a task

The simplest way to overlay text on the camera feed is to call `write_text()` from
the task. The text is rendered on every subsequent frame at a fixed position in the
status bar and stays visible until it is changed or cleared.

```python
from village.devices.camera import cam_box

cam_box.write_text("reward delivered")   # persists across frames until changed
cam_box.write_text("")                   # clear
```

The annotation is also saved frame-by-frame in the session CSV alongside the
position data, so it is useful for marking task events for post-hoc analysis.

For anything beyond plain text — shapes, coloured overlays, position-dependent
graphics — use the `CameraDrawBase` subclass described below.

---

#### Drawing with CameraDrawBase

`CameraDrawBase` exposes two methods that are called automatically on every frame:

| Method | Renderer | Destination |
|--------|----------|-------------|
| `draw(cam)` | cv2 (modifies `cam.frame`) | **disk and screen** |
| `draw_preview(cam, painter)` | QPainter (widget overlay) | **screen only** |

The default implementation of `draw` writes the status bar texts and pixel counts
for both cameras, and for the CORRIDOR camera also draws the thresholded detection
mask and area rectangles (if VIEW_DETECTION is active).
The default `draw_preview` draws those same overlays for the BOX camera via QPainter
so they appear on screen but are not encoded into the video file.

Create a file named `camera_draw` inside your project's `code` directory and define
a class named `CameraDraw` that inherits from `CameraDrawBase`. The system detects
it automatically and uses it instead of the base class.

**Overriding `draw`** — runs on every frame, changes are saved to disk:

```python
from village.custom_classes.camera_draw_base import CameraDrawBase
import cv2

class CameraDraw(CameraDrawBase):

    def __init__(self) -> None:
        super().__init__()

    def draw(self, cam) -> None:
        super().draw(cam)   # keep default status bar and detection overlays

        # Add a red circle at the animal's position (BOX only, task running)
        if cam.name == "BOX" and cam.task_is_running and cam.x_position != -1:
            cv2.circle(
                cam.frame,
                (cam.x_position, cam.y_position),
                radius=20,
                color=(0, 0, 255),   # BGR
                thickness=2,
            )
```

**Overriding `draw_preview`** — runs at preview framerate, screen only:

```{admonition} Note
:class: note
`cam.items_to_draw` is a plain `dict` the task can populate to pass data (like
`"reward_zone"` below) to these methods — see
[Passing data from the task](#passing-data-from-the-task-via-items_to_draw).
```

```python
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QBrush, QColor, QPainter

    def draw_preview(self, cam, painter) -> None:
        super().draw_preview(cam, painter)   # keep default detection overlays

        # Highlight the reward zone on screen (never saved to video)
        zone = cam.items_to_draw.get("reward_zone")
        if zone and cam.name == "BOX":
            device = painter.device()
            sx = device.width() / cam.width
            sy = device.height() / cam.height
            x, y, w, h = zone
            painter.setPen(QColor(0, 255, 0))
            painter.setBrush(QBrush())
            painter.drawRect(QRect(int(x*sx), int(y*sy), int(w*sx), int(h*sy)))
```

Both methods receive these attributes on `cam` (updated every frame):

**Identity & state**

- `cam.name` — `'BOX'` or `'CORRIDOR'`.
- `cam.task_is_running` — `True` if a task is active, `False` if not.
- `cam.view_detection` — whether detection overlays are enabled in the GUI.
- `cam.tracking` — whether animal position tracking is active (BOX only).
- `cam.color` — `Color.BLACK` or `Color.WHITE`: which pixels to detect.

**Frame data**

- `cam.frame` — current frame as a BGR numpy array (read/write, cv2 only).
- `cam.width`, `cam.height` — frame dimensions in pixels.
- `cam.frame_number` — frames captured since recording started.
- `cam.timing` — milliseconds elapsed since recording started.

**Session info**

- `cam.filename` — base name of the current video file (empty if not recording).
- `cam.trial` — current trial number (0 if no task running or CORRIDOR camera).
- `cam.annotation` — current `write_text()` string; persists until changed.
- `cam.items_to_draw` — plain `dict` for passing arbitrary data from the task (see below).

**Detection areas**

- `cam.number_of_areas` — number of configurable areas (always 4).
- `cam.areas` — list of `[x1, y1, x2, y2]` pixel coordinates per area. For a
  BOX area overridden by a `CustomAreaBase`, this is the shape's bounding
  box, not a real detection rectangle.
- `cam.areas_active` — bool list, whether each area is enabled (not OFF).
- `cam.areas_allowed` — bool list, `True` only for ALLOWED areas.
- `cam.areas_not_allowed` — bool list, `True` only for NOT_ALLOWED areas.
- `cam.areas_trigger` — bool list, `True` only for TRIGGER areas.
- `cam.custom_areas` — `dict[int, CustomAreaBase]`, BOX area index (1-4) to
  the `CustomAreaBase` overriding that area's shape, if any (see
  [Custom Detection Area](#custom-detection-area)).

**Detection results**

- `cam.masks` — grayscale numpy arrays with the thresholded mask per area.
- `cam.counts` — detected pixel count per area.
- `cam.x_position`, `cam.y_position` — tracked animal position in pixels (`-1` if not detected).

**Task access**

- `self.task` — the current task instance.


#### Passing data from the task via `items_to_draw`

`cam.items_to_draw` is a plain dictionary. The task can populate it at any point
to pass coordinates, labels, or any other data to the drawing methods without
coupling the task directly to this class:

```python
# Inside the task, at any point:
from village.devices.camera import cam_box

cam_box.items_to_draw["reward_zone"] = (200, 150, 80, 80)   # x, y, w, h
cam_box.items_to_draw["reward_zone"] = None                  # remove
```
