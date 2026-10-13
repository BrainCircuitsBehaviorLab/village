## Direct Functions

Your project's `code` directory can hold three files that work together:

- **`direct_functions.py`** — numbered, self-contained actions (play a sound, draw a
  stimulus, toggle a camera annotation, ...) that can be triggered from several
  different places: a GUI button, a camera/GPIO/touchscreen trigger, a Bpod
  softcode, or a direct call from your task's own code.
- **`sound_functions.py`** and **`video_functions.py`** — small libraries of
  generator functions that direct functions (or tasks) call to actually produce a
  sound or a visual stimulus, built on top of the `sound_device` and `screen` APIs
  described in [Sound](../devices/sound.md) and
  [Screen & Touchscreen](../devices/screen.md).

---

### Writing Direct Functions

Create a file inside your project's `code` directory (e.g. `direct_functions.py`) and define
a class (e.g. `DirectFunctions`) that inherits from `DirectFunctionsBase`. The file and class names are
up to you: the system detects the class by what it inherits from, and uses it
instead of the default base class. Only one such class is used per project.
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
        cam_box.write_text("ON")

    def function2(self):
        """Clear Camera MSG"""
        cam_box.write_text("")
```

```{admonition} Note
:class: note
The system detects the class automatically — no registration needed. See the demo
project's [direct_functions.py](../examples/direct_functions.md) for a fuller set of
examples covering sound playback and on-screen stimuli.
```

#### Ways to trigger a direct function

- **GUI** — the `FUNCTIONS` tab shows one button per registered function, labeled
  with its docstring. Clicking it calls that function right away.
- **Camera trigger** — call `self.task.execute_function(N)` inside
  `CameraTriggerBase.trigger`. See [Camera Triggers](../devices/camera.md#reacting-to-the-animals-position).
- **GPIO trigger** — call `self.task.execute_function(N)` inside `trigger_on` /
  `trigger_off`. See [GPIO](../devices/gpio.md).
- **Scale trigger** — call `self.task.execute_function(N)` inside
  `ScaleTriggerBase.on_weight`. See [Scale](../devices/scale.md).
- **Touchscreen trigger** — call `self.task.execute_function(N)` inside
  `TouchTriggerBase.trigger`. See [Screen & Touchscreen](../devices/screen.md).
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
:class: note
The example above is Bpod → Raspberry Pi. There is also a channel the other way
around — the task can send a softcode from the Raspberry Pi to Bpod
(`self.task.bpod.send_softcode_to_bpod(N)`), for the *state machine* to branch on
via `state_change_conditions={"SoftCodeN": "next_state"}`. That's a different
mechanism (a Bpod input condition, not a direct-function trigger) — see
the "Example" section of [Screen & Touchscreen](../devices/screen.md).
```

---

### Sound and Video Functions

The functions that generate sounds (`sound_functions.py`) and visual stimuli
(`video_functions.py`), which direct functions use, are explained with each device:
[Sound](../devices/sound.md#sound-functions) and
[Screen & Touchscreen](../devices/screen.md#video-functions).

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

```{toctree}
:hidden:

Direct Functions Example <../examples/direct_functions.md>
```
