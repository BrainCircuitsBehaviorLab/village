## Task Methods & Attributes

Full reference for `TaskBase` — every method you can override or call, and every
attribute you can read, from inside your own task. For a walkthrough of building a
task from scratch, see the [Task Development Guide](task.md).

---

### Methods you must override

| Method | Called | Use it to |
|--------|--------|-----------|
| `start(self)` | Once, before the trial loop begins. | Configure hardware, pre-compute stimuli, open files, etc. |
| `create_trial(self)` | Once at the start of every trial. | Build and run the trial. |
| `after_trial(self)` | Immediately after each trial finishes. | Score performance, update adaptive parameters, call `register_value`. |
| `close(self)` | Once after the trial loop ends (session finished, forced stop, or error). | Close files, stop hardware, release resources. |

```{admonition} create_trial with Bpod
:class: note
Each call starts with an empty state machine. Add states with `self.bpod.add_state`
— when the method returns, the state machine is sent and run automatically, and
`after_trial` is called once it finishes. Without Bpod, you're responsible for
creating and running the trial logic yourself.
```

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

#### Registering controller events

If you're using Bpod, all four of these are called automatically — you never need
to call them yourself, and you can skip this section. With `BEHAVIOR_CONTROLLER`
set to `OTHER`, call them with the right timestamps to populate `trial_data` (see
below).

| Method | Args | When to call it (`OTHER`) |
|--------|------|------|
| `register_start_trial` | `raspberry_timestamp: float, controller_timestamp: float` | At the beginning of each trial. **Required.** |
| `register_end_trial` | `controller_timestamp: float` | At the end of each trial. Optional (see below). |
| `register_enter_state` | `state_name: str, controller_timestamp: float` | Whenever you enter a state (closes the previous one). |
| `register_controller_event` | `name: str, controller_timestamp: float` | To register any other controller event. |

- `raspberry_timestamp`: the Raspberry Pi's own clock — get it with `time_utils.now_timestamp()`.
- `controller_timestamp`: read from the microcontroller's own clock (e.g. an Arduino's `millis()`, converted to seconds), if you're talking to one and it reports its own timing.
- If you're not syncing against an external clock (no microcontroller, or one that doesn't report its own timing), `controller_timestamp` is exactly the same as `raspberry_timestamp`.

`register_start_trial` uses the two timestamps together to compute a clock offset
(`raspberry_timestamp - controller_timestamp`), used to convert every later
`controller_timestamp` back to Raspberry Pi absolute time.

`````{admonition} Without Bpod, register_start_trial is required
:class: warning
Call `register_start_trial` at the beginning of **every** trial, in
`create_trial`. Without it **the task stops with an error**.

`register_end_trial` is optional: if `create_trial` returns without calling it,
the trial is ended at that moment (Raspberry time, converted to the controller
clock with the offset above). Call it yourself if you want the controller's own
end time instead.

With a controller that has its own clock (e.g. an Arduino), register the trial
start in both clocks, and everything the controller reports in its own clock
(`read_controller_time()` stands for your own way of getting it — the `arduino_*`
example tasks use the milliseconds since the Arduino received the start command):

```python
def create_trial(self):
    t0 = time_utils.now_timestamp()
    c0 = self.read_controller_time()
    self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=c0)
    ...  # the trial: register_enter_state / register_controller_event with
         # the controller's times
    c1 = self.read_controller_time()
    self.register_end_trial(controller_timestamp=c1)  # optional
```

Without an external clock (the Raspberry Pi is the controller), pass the same
time as both, and leave the end to the automatic one:

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

For events generated by the Raspberry Pi itself, asynchronously from the controller
— e.g. executing a direct function, or a camera/touchscreen detection. Pass
`time_utils.now_timestamp()` as `raspberry_timestamp`.

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
| `self.bpod` | `BpodController` | Bpod interface — state machine construction, sending, etc. Mainly used inside `create_trial`. |
| `self.arduino` | `ArduinoController` | Arduino interface, for tasks using an Arduino instead of Bpod. |
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

`````{admonition} Needed for a task with its own waiting loop
:class: tip
Trial/time limits and `force_stop` are only checked *between* trials, by the
task's own run loop — they can't interrupt a `create_trial` that's blocked inside
its own waiting loop. If your task doesn't use Bpod and waits on its own
condition inside `create_trial`, poll `self.should_stop` so the loop actually
exits when asked to:

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

You don't have to do anything for these, with or without Bpod — with one
exception: without Bpod, `TRIAL_START` comes from your call to
`register_start_trial`, which is required (see above). `TRIAL_END` comes from
`register_end_trial`, or is set automatically when `create_trial` returns if you
didn't call it.

**Keys added per state visited** (Bpod or manual):

- `"STATE_<name>_START"` / `"STATE_<name>_END"` (list[float]): timestamps of every
  entry/exit for that state — a list because the same state can be visited more
  than once per trial.

With Bpod they are added automatically, and a state that was **not visited** still
appears, with `[nan]`. Without Bpod, if your trial is organized in states, call
`register_enter_state(name, timestamp)` every time you enter one: it closes the
previous state (its end time is the new state's start) and opens the new one,
exactly as Bpod does. The trial's end (`register_end_trial`, or the automatic
one) closes the last one. Here a state that was not visited simply does not
appear.

To check whether a state was visited in both cases, look at its first start time
with a `nan` default (see the example below).

**Keys added per event type:**

- `"<EventName>"` (list[float]): timestamps of every occurrence of that event
  (e.g. `"Port1In"`, `"Port1Out"`, `"Tup"`).

With Bpod they are added automatically. Without Bpod, register them yourself,
between `register_start_trial` and the end of `create_trial` (anything registered
outside that window is ignored). Which method to use depends on **which clock
timed the event** — there are two:

- **The Raspberry Pi's clock** (`time_utils.now_timestamp()`): for events the Pi
  itself detects or produces — a camera or touchscreen detection, a direct
  function, a sound. Use `register_raspberry_event`.
- **The controller's own clock** (e.g. an Arduino's `millis()`, in seconds): for
  events the controller detects and timestamps itself — a poke on a port wired to
  the Arduino. Use `register_controller_event`; it is converted to Raspberry Pi
  time with the offset computed in `register_start_trial`.

If there is no external controller (the Raspberry Pi is the controller), both
clocks are the same and both methods do the same.

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
    "Tup": [1791454504.95, 1791454506.35],
    "ordered_list_of_events": [
        "Port3In", "Port3Out", "Port2In", "Port2Out", "Port1In", "Tup", "Tup"
    ],
}
```

Getting information out of it in `after_trial`:

```python
import math

def after_trial(self):
    # 1. Did the animal reach the REWARD state? With Bpod a state that was not
    # visited is [nan]; without Bpod it is missing. This works in both cases.
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
