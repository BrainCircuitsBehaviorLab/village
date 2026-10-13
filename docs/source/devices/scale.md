## Scale

The Training Village can have two scales: one in the corridor, used by the system, and
an optional one in the box, for your tasks.

---

### Setup

- **The corridor scale**, always present. The system uses it to weigh every animal when
  it goes back home and to detect that it has left the box (see
  [The Animal Doesn't Leave](../troubleshooting/troubleshooting.md#the-animal-doesnt-leave-scale-and-exit-detection)).
  The weights are saved with each session. Calibrate it from `MONITOR` → `CORRIDOR`
  (see [Monitor & Hardware Setup](../system_operation/corridor.md)), and set the valid
  range of weights with `MIN_WEIGHT_THRESHOLD` and `MAX_WEIGHT_THRESHOLD`
  (`SETTINGS` → `CORRIDOR SETTINGS`).
- **The box scale**, optional, connected to the Box Board, for your tasks (a platform,
  a lever...). It is available when `USE_BOX_BOARD` and `SCALE_BOX` are ON (in
  `SETTINGS` → `BOX SETTINGS`). Tare and calibrate it from `MONITOR` → `BOX` before
  using it.

---

### Using It in Tasks

While a task is running, the box scale is read continuously (see below), and the last
weight read is always available, without making a new reading:

```python
from village.devices.scale import scale_box

weight = scale_box.last_weight  # grams
```

---

### Reacting to the Box Scale

While a task is running, the box scale is read in its own thread every
`period` seconds (0.1 s by default) and the `on_weight` method of
`ScaleTriggerBase` is called with every reading. By default it does nothing.
You can override it to react to the weight (the animal stepping on a platform,
a lever pressed with a given force, ...).

---

#### Creating a custom ScaleTrigger

Create a file inside your project's `code` directory (e.g. `scale_trigger.py`) and define
a class (e.g. `ScaleTrigger`) that inherits from `ScaleTriggerBase`. The file and class names are
up to you: the system detects the class by what it inherits from, and uses it
instead of the default base class. Only one such class is used per project.

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

#### Choosing the period

A reading takes a few milliseconds and the thread sleeps between readings, so
it barely loads the Raspberry Pi. The limit is the scale itself: it only gives
about 10 new values per second, so a `period` below 0.1 s just repeats the
same value. The minimum accepted is 0.02 s.

```{toctree}
:hidden:

Scale Trigger Example <../examples/scale_trigger.md>
```
