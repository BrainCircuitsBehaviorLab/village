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

Create a file named `touch_trigger` inside your project's `code` directory and
define a class named `TouchTrigger` that inherits from `TouchTriggerBase`. The
system will automatically detect it and use it instead of the default base class.

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
            timestamp (float): Monotonic timestamp of the event (seconds).

        Available via self.task:
        - self.task.cam_box      — box camera (write_text, areas, position, …)
        - self.task.bpod         — Bpod controller (send_softcode_to_bpod, …)
        - any attribute defined in the task class
        """
        self.task.cam_box.write_text(f"Touch: {x}, {y}")
```

---

### Example — checking a target area and sending a softcode to Bpod

A common pattern in touchscreen tasks is to define a circular target on the
stimulus screen and determine whether the animal's touch landed inside or outside
it. The result is then sent to Bpod as a softcode so that the state machine can
branch accordingly.

**In the task**, define the target position and tolerance as instance attributes
so the `TouchTrigger` can read them via `self.task`:

```python
class MyTask(Task):

    def start_trial(self):
        # Position and radius of the target on the stimulus screen (pixels)
        self.target_x: int = 640
        self.target_y: int = 360
        self.tolerance_px: int = 80
        self.touch_correct: bool = False

        # ... build and run the state machine ...
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
        dx = x - getattr(task, "target_x", 0)
        dy = y - getattr(task, "target_y", 0)
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

The Bpod state machine receives the softcode and can use it to branch:

```python
sma.add_state(
    state_name="WaitForTouch",
    state_timer=5,
    state_change_conditions={
        "Tup": "Timeout",
        "SoftCode1": "Reward",
        "SoftCode2": "Punish",
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
