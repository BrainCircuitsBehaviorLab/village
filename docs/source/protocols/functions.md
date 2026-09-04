## Direct, Audio & Video Functions

Your project's `code` directory can hold three files that work together:

- **`direct_functions.py`** — numbered, self-contained actions (play a sound, draw a
  stimulus, toggle a camera annotation, ...) that can be triggered from several
  different places: a GUI button, a camera/GPIO/touchscreen trigger, a Bpod
  softcode, or a direct call from your task's own code.
- **`sound_functions.py`** and **`video_functions.py`** — small libraries of
  generator functions that direct functions (or tasks) call to actually produce a
  sound or a visual stimulus, built on top of the `sound_device` and `screen` APIs
  described in [Sound Integration](../system_operation/sound.md) and
  [Screen Integration](../system_operation/screen.md).

---

### Direct Functions

Create a file named `direct_functions.py` inside your project's `code` directory
and define a class named `DirectFunctions` that inherits from `DirectFunctionsBase`.
Each method must be named `functionN` (`N` from 1 to 98) and take no arguments other
than `self`. Its first line, as a docstring, is a short label — it's what shows up
on the corresponding button in the GUI, so keep it brief.

```python
from village.custom_classes.direct_functions_base import DirectFunctionsBase
from village.devices.camera import cam_box


class DirectFunctions(DirectFunctionsBase):

    def function1(self):
        """Camera MSG ON"""
        # self.task gives access to the currently running task, so you can read
        # anything it defines (settings, calibrations, custom attributes, ...)
        cam_box.annotation = "ON"

    def function2(self):
        """Clear Camera MSG"""
        cam_box.annotation = ""
```

```{admonition} Note
:class: note
The system detects the class automatically — no registration needed. See this
project's own `direct_functions.py` for a fuller set of examples covering sound
playback and on-screen stimuli.
```

#### Ways to trigger a direct function

- **GUI** — the `FUNCTIONS` tab shows one button per registered function, labeled
  with its docstring. Clicking it calls that function right away.
- **Camera trigger** — call `self.task.execute_function(N)` inside
  `CameraTriggerBase.trigger`. See [Camera Triggers](camera.md#camera-triggers).
- **GPIO trigger** — call `self.task.execute_function(N)` inside `trigger_on` /
  `trigger_off`. See [Custom GPIO Interaction](gpio_trigger.md).
- **Touchscreen trigger** — call `self.task.execute_function(N)` inside
  `TouchTriggerBase.trigger`. See [Touchscreen](touchscreen.md).
- **Bpod softcodes** — if `BEHAVIOR_CONTROLLER` is `BPOD`, functions 1-98 can be
  triggered automatically from inside the state machine (see below).
- **`OTHER` controller (a microcontroller you talk to yourself, or none at all)**
  — there is no state-machine layer to trigger functions for you, so call
  `self.execute_function(N)` directly from your task's own code (`create_trial`,
  `after_trial`, or anywhere else), whenever you want it to run.

#### Bpod softcodes

A softcode is a short message the Bpod state machine sends back to the Raspberry
Pi **while a trial is running**, without waiting for the trial to end. You trigger
one by including `BpodOutput.SoftCodeN` in a state's `output_actions`, alongside
any other output (opening a valve, turning on an LED, ...). `N` goes from 1 to 98,
matching direct functions 1-to-1. The moment the state machine executes that
output, Village receives the message and automatically calls
`execute_function(N)` — this is how a Bpod task can trigger a direct function mid
-trial, from inside the state machine, instead of only between trials.

```python
self.bpod.add_state(
    state_name="reward",
    state_timer=0.5,
    state_change_conditions={BpodEvent.Tup: "exit"},
    # opens Valve1 AND triggers function6, at the same time
    output_actions=[("Valve1", 1), BpodOutput.SoftCode6],
)
```

```{admonition} This is not the only softcode channel
:class: tip
The example above is Bpod → Raspberry Pi. There is also a channel the other way
around — the task can send a softcode from the Raspberry Pi to Bpod
(`self.task.bpod.send_softcode_to_bpod(N)`), for the *state machine* to branch on
via `state_change_conditions={"SoftCodeN": "next_state"}`. That's a different
mechanism (a Bpod input condition, not a direct-function trigger) — see
the "Example" section of [Touchscreen](touchscreen.md).
```

---

### Audio Functions

`sound_functions.py` holds two kinds of functions:

1. **Generic generators** (e.g. `tone_generator`, `whitenoise_generator`) that take
   whatever arguments they need and return a numpy waveform array. Call them from
   anywhere — a direct function, a task, a trigger — and pass the result to
   `sound_device.load()`.
2. **Calibration-sound wrappers** — thin wrappers around a generic generator that
   fix every argument except `duration` and `gain`, since that's the signature the
   Sound Calibration panel always calls them with. They are listed in
   `sound_calibration_functions`, which fills the `SOUND` dropdown in the
   [Sound Calibration](../calibrations/sound.md) panel.

```python
def tone_generator(duration: float, gain: float, frequency: int):
    ...  # returns a numpy array

def tone_600(duration: float, gain: float):
    return tone_generator(duration=duration, gain=gain, frequency=600)

sound_calibration_functions = [tone_600, ...]
```

```{admonition} Keep names in sync
:class: warning
A wrapper's `__name__` (`"tone_600"` above) is stored as the sound's identity in
the calibration data, and is what you pass as `sound_name=` to
`get_sound_gain(...)` everywhere else in the project. Rename a wrapper here and
every call site referencing its old name has to be updated too, or the
calibration lookup silently stops matching and raises a "not calibrated" error.
```

---

### Video Functions

`video_functions.py` holds `draw_X_generator(...)` factories: each one takes the
stimulus parameters and returns a `draw()` closure, meant to be passed to
`screen.load_draw_function(draw_fn=...)` (see
[Screen Integration](../system_operation/screen.md)). Qt then calls that `draw()`
on every frame while `screen.start_drawing()` is active.

```python
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPainter

def draw_circle_generator(duration, x_pos, y_pos, diameter, color):
    def draw():
        with QPainter(screen) as painter:
            painter.fillRect(painter.viewport(), screen.background_color)
            if screen.elapsed_time < duration:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(QRect(x_pos, y_pos, diameter, diameter))
    return draw
```

Two things every `draw()` needs to do itself, since nothing does them
automatically:

- Fill the background first (`screen.background_color`) — Qt doesn't clear the
  widget between paints, so skipping this leaves the previous frame's stimulus
  on screen underneath the new one.
- Check `screen.elapsed_time < duration` before painting anything — once the
  duration is over, `draw()` just stops drawing the stimulus (falling back to
  the plain background) until a new draw function is loaded.

---

### Adding your own functions

`sound_functions.py` and `video_functions.py` are plain modules, not subclasses —
unlike `direct_functions.py` (or `camera_trigger.py`, `gpio_trigger.py`, ...),
there is only ever one of them per project, so there's nothing to discover or
swap automatically. Add a new generator alongside the existing ones and import it
directly wherever you need it, the same way `direct_functions.py` already does:

```python
from sound_functions import tone_generator, whitenoise_generator
from video_functions import draw_circle_generator, draw_rectangle_generator
```
