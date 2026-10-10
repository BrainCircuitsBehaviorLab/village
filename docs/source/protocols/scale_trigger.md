## Custom Scale Interaction

```{admonition} Note
:class: note
Only available when `USE_BOX_BOARD` and `SCALE_BOX` are ON (in `SETTINGS`).
Tare and calibrate the box scale from the `MONITOR` tab before using it.
```

While a task is running, the box scale is read in its own thread every
`period` seconds (0.1 s by default) and the `on_weight` method of
`ScaleTriggerBase` is called with every reading. By default it does nothing.
You can override it to react to the weight (the animal stepping on a platform,
a lever pressed with a given force, ...).

---

### Creating a custom ScaleTrigger

Create a file named `scale_trigger.py` inside your project's `code` directory
and define a class named `ScaleTrigger` that inherits from `ScaleTriggerBase`.
The system will automatically detect it and use it instead of the default
base class.

```python
from village.custom_classes.scale_trigger_base import ScaleTriggerBase


class ScaleTrigger(ScaleTriggerBase):

    def __init__(self) -> None:
        super().__init__()
        self.period = 0.1  # seconds between readings
        self.on_platform = False

    def on_weight(self, weight: float, timestamp: float) -> None:
        """Called after every reading of the box scale.

        Available via self.task:
        - self.task.cam_box      — box camera (write_text, areas, position, …)
        - self.task.bpod         — Bpod controller (send_softcode_to_bpod, …)
        - self.task.gpio         — set_on()/set_off() for the output pin
        - any attribute defined in the task class
        """
        if weight > 10 and not self.on_platform:
            self.on_platform = True
            self.task.register_raspberry_event("PlatformIn", timestamp)
            self.task.bpod.send_softcode_to_bpod(1)
        elif weight < 5 and self.on_platform:
            self.on_platform = False
            self.task.register_raspberry_event("PlatformOut", timestamp)
```

```{admonition} Note
:class: note
`on_weight` runs in the scale reader thread, not in the task thread. Keep it
fast and avoid blocking calls: the next reading waits until it returns.
```

A complete example, which records when the animal steps on and off the scale
in the trial data of any task: [scale_trigger.py](../examples/scale_trigger.md).

### Choosing the period

A reading takes a few milliseconds and the thread sleeps between readings, so
it barely loads the Raspberry Pi. The limit is the scale itself: it only gives
about 10 new values per second, so a `period` below 0.1 s just repeats the
same value. The minimum accepted is 0.02 s.

The last weight read is also available as `scale_box.last_weight`
(`from village.devices.scale import scale_box`), without making a new reading.

```{toctree}
:hidden:

Scale Trigger Example <../examples/scale_trigger.md>
```
