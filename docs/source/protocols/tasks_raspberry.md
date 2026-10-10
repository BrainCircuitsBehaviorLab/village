## Tasks (Raspberry Only)

With `BEHAVIOR_CONTROLLER` set to `OTHER` in `SETTINGS` and no microcontroller, the
Raspberry Pi runs the trial itself: it reacts to what it detects (the box camera
areas, the touchscreen, the GPIO input pin, the box scale) and produces the
stimuli (sounds, the screen, the LED strip, the GPIO output pin). Its timing is
less precise than a microcontroller's: for fast and precise timing, use Bpod or a
microcontroller.

The detections arrive through the triggers (camera, touchscreen, GPIO, scale), which
run in their own threads and call your code while the task is running. The usual
pattern is: the trigger reacts and signals the task, and the task's `create_trial`
waits for that signal (or a timeout) to end the trial.

To create a task, create a Python file inside your project's `code` directory, and
within it, a class named after the task, inheriting from the generic `TaskBase`
class. Naming conventions follow Python standards: CamelCase for class names,
lower_case for filenames and function/variable names. Let's look at an example.

<!-- The code on this page is included from docs/source/examples/files/raspberry_area1_sound.py and camera_trigger.py,
selected by method name (pyobject) and by some lines of text (start-at / end-before).
If those lines change there, update them here too, and check the page: a block whose
text is not found can come out empty. -->

### A minimal task

[raspberry_area1_sound.py](../examples/raspberry_area1_sound.md): every trial
waits for the animal to enter area 1 of the box camera; when it does, a sound is
played and an LED of the LED strip turns on. Its top part:

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:end-before: "class RaspberryArea1Sound"
```

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:pyobject: RaspberryArea1Sound
:end-before: "    def start"
```

The task is initialized with `__init__`, where it acquires all the properties of the
generic `TaskBase` class with `super().__init__()`. `self.info` is shown to the user
when the task is selected in the GUI to run manually.

Four methods must be implemented in your class: `start`, `create_trial`,
`after_trial`, and `close`.

### The `start()` method

Called once, when the task starts. Here it loads the sound (with the gain for 70 dB
from the sound calibration), warns if the camera isn't set up for the task, and
creates the signal (`threading.Event`) that the trigger will use:

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:pyobject: RaspberryArea1Sound.start
:dedent: 4
```

The most commonly used attributes available by default inside any task method
(see [Attributes you can read](#attributes-you-can-read) below) are:

- `self.settings` — the session's parameters, as defined in `training_protocol.py`
  (e.g. `self.settings.reward_volume`).
- `self.calibrations` — convert hardware values to real-world units, e.g.
  `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`.
- `self.cam_box`, `self.gpio`, `self.custom_areas` — the box camera, GPIO output
  control, and any custom-shaped detection areas the project defines.
- `self.name`, `self.subject`, `self.current_trial`, `self.system_name`, `self.date`.
- `self.trial_data` — populated automatically after each trial, available inside
  `after_trial` (see below).

### The `create_trial()` method

Called once per trial. Without Bpod, `create_trial` *is* the trial: it returns when
the trial is over.

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:pyobject: RaspberryArea1Sound.create_trial
:dedent: 4
```

1. **It registers the start of the trial** with `register_start_trial`. This call
   is **required** without Bpod. Here the Raspberry Pi is the controller, so both
   clocks are the same and the same time is passed as both.
2. **It waits** for the trigger's signal, up to `TRIAL_TIMEOUT` seconds, checking
   `self.should_stop` so the task can stop at any moment.
3. **It registers the end of the trial** with `register_end_trial`. This one is
   optional: if `create_trial` returns without calling it, the trial is ended at
   that moment.

### The trigger

The part of [camera_trigger.py](../examples/camera_trigger.md) that reacts to area 1.
It runs on every frame of the box camera; when the animal is in area 1 and the
task's signal isn't set yet, it registers the entry, plays the sound loaded in
`start`, lights the LED, and sets the signal:

```{literalinclude} ../examples/files/camera_trigger.py
:language: python
:pyobject: CameraTrigger.trigger
:start-at: "area1_event = getattr"
:end-before: "area2_event = getattr"
:dedent: 8
```

The entry is registered with `register_raspberry_event`, since it is the Raspberry
Pi that detected it.

### The `after_trial()` and `close()` methods

`after_trial` is called once after each trial ends, to register whatever values you
want saved to the session's data file. `close` is called once when the task
finishes; here there's nothing to clean up:

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:pyobject: RaspberryArea1Sound.after_trial
:dedent: 4
```

```{literalinclude} ../examples/files/raspberry_area1_sound.py
:language: python
:pyobject: RaspberryArea1Sound.close
:dedent: 4
```

### Another example

[raspberry_touchscreen.py](../examples/raspberry_touchscreen.md) follows the same
pattern with the touchscreen: it shows 6 rectangles, and
[touch_trigger.py](../examples/touch_trigger.md) runs a different visual stimulus
for each one and signals the task when one is touched.

---

### Methods you must override

| Method | Called | Use it to |
|--------|--------|-----------|
| `start(self)` | Once, before the trial loop begins. | Configure hardware, pre-compute stimuli, open files, etc. |
| `create_trial(self)` | Once at the start of every trial. | Run the trial: register its start, wait for what has to happen, and register what happened. |
| `after_trial(self)` | Immediately after each trial finishes. | Score performance, update adaptive parameters, call `register_value`. |
| `close(self)` | Once after the trial loop ends (session finished, forced stop, or error). | Close files, stop hardware, release resources. |

```{admonition} after_trial must register "water"
:class: warning
Always call `self.register_value("water", ...)` with the amount of water consumed
during the trial. The system sums it across the session to get total water
consumption — if that total falls below a configurable threshold, an alarm is
triggered (adjustable in the Settings tab of the GUI).
```

```{admonition} What is saved when a session stops
:class: note
Each session saves two files:

- The **raw** file (`<session>_RAW.csv`) has one line per event, written as it
  happens, so it keeps everything — including the trial that was still running
  when the session stopped.
- The **clean** file (`<session>.csv`) is a table with one row per trial, and a
  trial's row is only created when the trial finishes (after `after_trial`). So
  the trial that was still running when the session stopped never gets its row.

The session is saved if at least one trial was completed. If none was, nothing
is saved (neither file) and the "No trials were recorded" alarm is raised (if
`NO_TRIALS_PERFORMED` is on).

Because the trial in progress is always lost from the clean file, design your
tasks so that trials keep advancing as time passes: a trial should end after a
reasonable time even if the animal does nothing (e.g. with a timeout), instead
of waiting indefinitely. A task that runs the whole session as a single trial
would never be saved.
```

---

### Methods you can call

Do not override these — call them from inside your task's own methods.

#### Registering the trial, states and events

| Method | Args | When to call it |
|--------|------|------|
| `register_start_trial` | `raspberry_timestamp: float, controller_timestamp: float` | At the beginning of each trial. **Required.** |
| `register_end_trial` | `controller_timestamp: float` | At the end of each trial. Optional (see below). |
| `register_enter_state` | `state_name: str, controller_timestamp: float` | Whenever you enter a state (closes the previous one). |
| `register_controller_event` | `name: str, controller_timestamp: float` | To register an event. |

Here the Raspberry Pi is the controller: pass `time_utils.now_timestamp()` as every
timestamp, and the same time as both in `register_start_trial`.

`````{admonition} register_start_trial is required
:class: warning
Call `register_start_trial` at the beginning of **every** trial, in
`create_trial`. Without it **the task stops with an error**.

`register_end_trial` is optional: if `create_trial` returns without calling it,
the trial is ended at that moment.

```python
def create_trial(self):
    t0 = time_utils.now_timestamp()
    self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)
    ...  # the trial: register_enter_state / register_raspberry_event
```
`````

#### Registering a Raspberry-side event

```python
def register_raspberry_event(self, name: str, raspberry_timestamp: float) -> None
```

For events generated by the Raspberry Pi itself, asynchronously from the trial
— e.g. executing a direct function, or a camera/touchscreen detection. Pass
`time_utils.now_timestamp()` as `raspberry_timestamp`.

With no external controller both clocks are the same, so `register_raspberry_event`
and `register_controller_event` do exactly the same.

#### Registering a value

```python
def register_value(self, name: str, value: Any) -> None
```

Saves a custom value to the current trial row in the CSV — call it inside
`after_trial`.

```python
self.register_value("correct", 1)
self.register_value("response_time", 0.432)
```

#### Executing a direct function

```python
def execute_function(self, i: int) -> None
```

Runs the direct function registered at index `i` (1-99). See
[Direct, Audio & Video Functions](functions.md) for how those get registered and
the other ways they can be triggered.

```python
self.execute_function(1)  # executes the function registered at index 1
```

---

### Attributes you can read

| Attribute | Type | Description |
|-----------|------|--------------|
| `self.name` | `str` | Name of the task (the class name). |
| `self.subject` | `str` | Name of the subject running the session. |
| `self.system_name` | `str` | Name of the system, as defined in the Settings tab. |
| `self.settings` | `Settings` | Session parameters defined in the training protocol. Read and write its attributes to implement adaptive training. |
| `self.cam_box` | `Camera \| NullCamera` | Camera attached to the operant box (`NullCamera` if not configured). |
| `self.gpio` | `Gpio \| NullGpio` | Output pin control (`set_on()` / `set_off()`). See [Custom GPIO Interaction](gpio_trigger.md) for the input-pin trigger hook. |
| `self.current_trial` | `int` | The current trial number, starting from 1. |
| `self.date` | `str` | Date string of the current session, set once when it starts. |
| `self.run_mode` | `str` | `"Manual"` or `"Auto"`. |
| `self.force_stop` | `bool` | Set to `True` from your own task logic (e.g. in `after_trial`) to make the task stop. |
| `self.stop_button_pressed` | `bool` | `True` once something external (e.g. the STOP TASK button) has asked the task to stop. Read-only — react to it, don't set it. |
| `self.chrono` | `Chrono` | `self.chrono.get_seconds()` gives the time in seconds since the task started. |

#### `self.info`

Human-readable description of the task, set once (usually in `__init__`). Shown to
the user when selecting the task in the GUI.

```python
self.info = """
My Task
-------
Describe what the task does and how it progresses here.
"""
```

#### `self.calibrations`

Holds the task's calibrations — call its methods to convert between hardware
values and real-world units (see [Custom Calibrations](../advanced_customization/calibrations.md)).

```python
gain = self.calibrations.sound_calibration.get_sound_gain(
    speaker=1, dB=70.0, sound_name="white_noise"
)
```

#### `self.should_stop` (read-only property)

`True` once *any* stopping condition is met: the trial/time limit (Manual mode
only — Auto mode runs until the subject leaves the corridor, not for a fixed
number of trials), `force_stop`, or `stop_button_pressed`.

`````{admonition} Poll it in your own waiting loop
:class: warning
Trial/time limits and `force_stop` are only checked *between* trials, by the
task's own run loop — they can't interrupt a `create_trial` that's blocked inside
its own waiting loop. Poll `self.should_stop` in that loop so it actually exits
when asked to:

```python
def create_trial(self):
    while not self.should_stop:
        ...  # wait for your own condition
```
`````

#### `self.trial_data` (dict)

Populated automatically at the end of each trial — available inside `after_trial`.

**Keys always present:**

- `"date"` (str), `"trial"` (int), `"subject"` (str), `"task"` (str), `"system_name"` (str)
- `"TRIAL_START"` / `"TRIAL_END"` (float): absolute timestamps (UNIX epoch seconds)
- `"ordered_list_of_events"` (list[str]): event names in the order they occurred (e.g. `["Port1In", "Port1Out", "Port1In"]`)

`TRIAL_START` comes from your call to `register_start_trial`, and `TRIAL_END` from
`register_end_trial` (or it is set automatically when `create_trial` returns if you
didn't call it). The rest are filled automatically.

**Keys added per state visited:**

- `"STATE_<name>_START"` / `"STATE_<name>_END"` (list[float]): timestamps of every
  entry/exit for that state — a list because the same state can be visited more
  than once per trial.

If your trial is organized in states, call `register_enter_state(name, timestamp)`
every time you enter one: it closes the previous state (its end time is the new
state's start) and opens the new one, exactly as Bpod does. The trial's end
(`register_end_trial`, or the automatic one) closes the last one. A state that was
not visited simply does not appear: to check whether a state was visited, look at
its first start time with a `nan` default (see the example below).

**Keys added per event type:**

- `"<EventName>"` (list[float]): timestamps of every occurrence of that event
  (e.g. `"Port1In"`, `"Port1Out"`).

Register them yourself, between `register_start_trial` and the end of
`create_trial` (anything registered outside that window is ignored). Use `register_raspberry_event` (or
`register_controller_event`, which here is the same) with
`time_utils.now_timestamp()`. Events registered from a trigger, while the trial is
running, are added too.

**Keys added by you:** any name passed to `register_value` inside `after_trial`.

##### Example

A short trial with four states: the animal pokes the right port (3) while
waiting, starts the trial in the center port (2), and then pokes the left port
(1), which is rewarded:

```python
{
    "date": "2026-10-08 10:15:02",
    "trial": 12,
    "subject": "mouse1",
    "task": "MyTask",
    "system_name": "village01",
    "TRIAL_START": 1791454502.10,
    "TRIAL_END": 1791454506.35,
    "STATE_WAIT_POKE_START": [1791454502.10],
    "STATE_WAIT_POKE_END": [1791454503.20],
    "STATE_RESPONSE_START": [1791454503.20],
    "STATE_RESPONSE_END": [1791454504.90],
    "STATE_REWARD_START": [1791454504.90],
    "STATE_REWARD_END": [1791454504.95],
    "STATE_ITI_START": [1791454504.95],
    "STATE_ITI_END": [1791454506.35],
    "Port3In": [1791454502.60],
    "Port3Out": [1791454502.75],
    "Port2In": [1791454503.20],
    "Port2Out": [1791454503.41],
    "Port1In": [1791454504.90],
    "ordered_list_of_events": [
        "Port3In", "Port3Out", "Port2In", "Port2Out", "Port1In"
    ],
}
```

Getting information out of it in `after_trial`:

```python
import math

def after_trial(self):
    # 1. Did the animal reach the REWARD state? A state that was not visited does not appear,
    # so look it up with a nan default.
    t_reward = self.trial_data.get("STATE_REWARD_START", [math.nan])[0]
    rewarded = not math.isnan(t_reward)

    # 2. First poke from the RESPONSE state onwards. Strictly after its start:
    # the center poke that started RESPONSE has exactly that timestamp.
    first_response_poke = "none"
    t_response = self.trial_data.get("STATE_RESPONSE_START", [math.nan])[0]
    if not math.isnan(t_response):
        pokes = [
            (t, port)
            for port in ("Port1In", "Port2In", "Port3In")
            for t in self.trial_data.get(port, [])
            if t > t_response
        ]
        if pokes:
            first_response_poke = min(pokes)[1]  # the earliest one

    # 3. Register the results (and, as always, the water).
    if rewarded:
        outcome = "correct"
    elif first_response_poke == "none":
        outcome = "miss"
    else:
        outcome = "incorrect"
    self.register_value("first_response_poke", first_response_poke)
    self.register_value("outcome", outcome)
    self.register_value("water", self.settings.reward_volume if rewarded else 0)
```

With the example above: `rewarded` is `True`, `first_response_poke` is
`"Port1In"` (the `Port3In` came before RESPONSE and the `Port2In` is the one that
started it), and `outcome` is `"correct"`.

```{toctree}
:hidden:

Tasks Examples <../examples/tasks_raspberry.md>
../examples/raspberry_area1_sound.md
../examples/raspberry_touchscreen.md
```
