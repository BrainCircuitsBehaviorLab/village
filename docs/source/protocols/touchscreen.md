## Custom Touchscreen Interaction

```{admonition} Note
:class: note
The touchscreen must be enabled and configured before using it in tasks. See
[Screen Integration](../system_operation/screen.md) for hardware setup and settings.
```

Every time a touch event passes the debounce filter, the `trigger` method of
`TouchTriggerBase` is called. By default it writes the touch coordinates to the
box camera feed. You can override this behavior to implement task-specific touch
responses.


---

### Creating a custom TouchTrigger

Create a file inside your project's `code` directory (e.g. `touch_trigger.py`) and define
a class (e.g. `TouchTrigger`) that inherits from `TouchTriggerBase`. The file and class names are
up to you: the system detects the class by what it inherits from, and uses it
instead of the default base class. Only one such class is used per project.

```python
from village.custom_classes.touch_trigger_base import TouchTriggerBase


class TouchTrigger(TouchTriggerBase):

    def __init__(self) -> None:
        super().__init__()

    def trigger(self, x: int, y: int, timestamp: float) -> None:
        """Called on every touch event that passes the debounce interval.

        Args:
            x (int): Touch x position in screen pixels.
            y (int): Touch y position in screen pixels.
            timestamp (float): Raspberry Pi time of the touch (the same clock as
                time_utils.now_timestamp()).

        Available via self.task:
        - self.task.cam_box      — box camera (write_text, areas, position, …)
        - self.task.bpod         — Bpod controller (send_softcode_to_bpod, …)
        - any attribute defined in the task class
        """
        self.task.cam_box.write_text(f"Touch: {x}, {y}")
```

You don't need to register the touches yourself: every touch that arrives while a trial
is running is already saved in the trial data as a Raspberry Pi event named
`touch_<x>_<y>` (e.g. `touch_640_360`), with its time.

---

### Example — checking a target area and sending a softcode to Bpod

A common pattern in touchscreen tasks is to define a circular target on the
stimulus screen and determine whether the animal's touch landed inside or outside
it. The result is then sent to Bpod as a softcode so that the state machine can
branch accordingly.

**In the task**, define the target position and tolerance as instance attributes
so the `TouchTrigger` can read them via `self.task`:

```python
from village.custom_classes.task_base import BpodEvent, TaskBase


class MyTask(TaskBase):

    def create_trial(self):
        # Position and radius of the target on the stimulus screen (pixels)
        self.target_x: int = 640
        self.target_y: int = 360
        self.tolerance_px: int = 80
        self.touch_correct: bool = False

        # ... build the state machine (see below) ...
```

**In `touch_trigger.py`**, check the distance to the target and send the
appropriate softcode:

```python
from village.custom_classes.touch_trigger_base import TouchTriggerBase


class TouchTrigger(TouchTriggerBase):

    def __init__(self) -> None:
        super().__init__()

    def trigger(self, x: int, y: int, timestamp: float) -> None:
        task = self.task

        # Compute distance from touch to the current target
        dx = x - task.target_x
        dy = y - task.target_y
        distance = (dx**2 + dy**2) ** 0.5
        tolerance = getattr(task, "tolerance_px", 80)

        if distance <= tolerance:
            task.touch_correct = True
            task.cam_box.write_text(f"Correct touch: {x}, {y}")
            task.bpod.send_softcode_to_bpod(1)   # softcode 1 → correct
        else:
            task.touch_correct = False
            task.cam_box.write_text(f"Wrong touch: {x}, {y}")
            task.bpod.send_softcode_to_bpod(2)   # softcode 2 → incorrect
```

The Bpod state machine (built in the task's `create_trial`) receives the softcode
and can use it to branch:

```python
self.bpod.add_state(
    state_name="wait_for_touch",
    state_timer=5,
    state_change_conditions={
        BpodEvent.Tup: "timeout",
        BpodEvent.SoftCode1: "reward",
        BpodEvent.SoftCode2: "punish",
    },
    output_actions=[],
)
```

```{admonition} Note
:class: note
`trigger` runs in the touch reader thread, not in the task thread. Keep the
method fast and avoid blocking calls. Writing to `cam_box` and sending a
softcode are both non-blocking and safe to call from here.
```

```{toctree}
:hidden:

Touchscreen Trigger Example <../examples/touch_trigger.md>
```
