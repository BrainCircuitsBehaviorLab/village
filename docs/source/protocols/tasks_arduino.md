## Tasks (Arduino or other microcontroller)

With `BEHAVIOR_CONTROLLER` set to `OTHER` in `SETTINGS`, a microcontroller (an
Arduino, or any other board that talks over a serial port) can run the
time-critical part of every trial: reading the pokes, turning the LEDs on, opening
the valves. The task, on the Raspberry Pi, tells it what to do at the start of every
trial and registers everything it reports. So there are two pieces of code:

- **The task** (`.py`), in your project's `code` directory, like any other task.
- **The firmware** (`.ino` for an Arduino), uploaded to the board with its own
  tools (e.g. the Arduino IDE). Village doesn't upload it.

They talk through the serial port set in `CONTROLLER_PORT` (`SETTINGS`). What they
say to each other is up to you: the examples use small binary messages, described
at the top of each file.

To create a task, create a Python file inside your project's `code` directory, and
within it, a class named after the task, inheriting from the generic `TaskBase`
class. Naming conventions follow Python standards: CamelCase for class names,
lower_case for filenames and function/variable names. Let's look at an example.

<!-- The code on this page is included from docs/source/examples/files/arduino_1_habituation.py (and its firmware),
selected by method name (pyobject) and by some lines of text (start-at / end-before).
If those lines change there, update them here too, and check the page: a block whose
text is not found can come out empty. -->

### A minimal task

[arduino_1_habituation.py](../examples/arduino_1_habituation.md) is the Arduino
version of [bpod_1_habituation.py](../examples/bpod_1_habituation.md), the simplest
task of the examples: the mouse is just left alone in the box, pokes are logged,
no reward is given. Its top part describes the messages and defines their codes:

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:end-before: "class Arduino1Habituation"
```

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:pyobject: Arduino1Habituation
:end-before: "    def start"
```

The task is initialized with `__init__`, where it acquires all the properties of the
generic `TaskBase` class with `super().__init__()`. `self.info` is shown to the user
when the task is selected in the GUI to run manually.

Four methods must be implemented in your class: `start`, `create_trial`,
`after_trial`, and `close`.

### The `start()` method

Called once, when the task starts. Here it opens the serial connection to the
Arduino. `BAUDRATE` must be the same as in the firmware, and `READ_TIMEOUT` is how
long each read waits for data — so also how often `create_trial` gets back to check
whether it has to stop.

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:pyobject: Arduino1Habituation.start
:dedent: 4
```

The most commonly used attributes available by default inside any task method
(see [Attributes you can read](#attributes-you-can-read) below) are:

- `self.settings` — the session's parameters, as defined in `training_protocol.py`
  (e.g. `self.settings.reward_volume`).
- `self.calibrations` — convert hardware values to real-world units, e.g.
  `self.calibrations.water_calibration.get_valve_time(port, volume)`, to tell the
  Arduino how long to open a valve.
- `self.cam_box`, `self.gpio`, `self.custom_areas` — the box camera, GPIO output
  control, and any custom-shaped detection areas the project defines.
- `self.name`, `self.subject`, `self.current_trial`, `self.system_name`, `self.date`.
- `self.trial_data` — populated automatically after each trial, available inside
  `after_trial` (see below).

### The `create_trial()` method

Called once per trial. Without Bpod, `create_trial` *is* the trial: it returns when
the trial is over.

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:pyobject: Arduino1Habituation.create_trial
:dedent: 4
```

Step by step:

1. **It tells the Arduino to start the trial**, with what it needs to know (here,
   only how long the trial lasts).
2. **It registers the start of the trial**, with `register_start_trial`, in both
   clocks: the Raspberry Pi's (`time_utils.now_timestamp()`) and the Arduino's. The
   Arduino's clock is the milliseconds since it received the command, so at that
   moment it is 0. This call is **required** without Bpod: every time the Arduino
   reports later is converted to Raspberry Pi time with the difference between the
   two, so the clocks never need to be synchronized.
3. **It listens to the Arduino** until the trial is over. The loop also checks
   `self.should_stop` (the task has to stop) and a deadline (a message lost on the
   way), so it can never wait forever.
4. **It registers what the Arduino reports**, with the Arduino's time:
   - every state it enters, with `register_enter_state` — the same state names as
     the Bpod version, so the trial data are the same;
   - every poke, with `register_controller_event` (`"Port1In"`...).
5. **It registers the end of the trial** with `register_end_trial`. This one is
   optional: if `create_trial` returns without calling it (e.g. the task was
   stopped), the trial is ended at that moment.

### The firmware

The Arduino side waits for the command, runs the trial with its own clock
(`millis()`), and sends every state and the result with the milliseconds elapsed
since the command:

```{literalinclude} ../examples/files/arduino_firmware/arduino_1_habituation.ino
:language: cpp
```

### The `after_trial()` method

Called once after each trial ends, to register whatever values you want saved to
the session's data file. `self.trial_data` has, by then, everything registered in
`create_trial` — `self.trial_data.get("Port1In", [])` is the list of times at which
port 1 was poked during the trial (empty if it never was). It's the same as in the
Bpod version:

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:pyobject: Arduino1Habituation.after_trial
:dedent: 4
```

### The `close()` method

Called once when the task finishes (session ends, or manually stopped). Here it
closes the serial connection:

```{literalinclude} ../examples/files/arduino_1_habituation.py
:language: python
:pyobject: Arduino1Habituation.close
:dedent: 4
```

### A more complete example

[arduino_4_center_initiated.py](../examples/arduino_4_center_initiated.md) is the
Arduino version of a 2-choice task: the Pi picks the correct side and sends it to
the Arduino with the timings and the valve time; the Arduino runs the center poke,
the side LED, the response and the valve, and reports every state and poke. The
inter-trial interval is timed by the Pi after the Arduino has finished
(`register_enter_state("iti", ...)` and a wait). The other `arduino_*` examples
follow the same pattern, each with its firmware.

### Water calibration

The built-in water calibration opens the valves through Bpod. With an Arduino,
write a subclass of `WaterCalibrationTaskBase` that opens them through your board:
see [Water Calibration](../calibrations/water.md).

---

### Methods you must override

| Method | Called | Use it to |
|--------|--------|-----------|
| `start(self)` | Once, before the trial loop begins. | Configure hardware, pre-compute stimuli, open files, etc. |
| `create_trial(self)` | Once at the start of every trial. | Run the trial: tell the controller what to do, and register the start of the trial and everything it reports. |
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

#### Registering the trial and controller events

| Method | Args | When to call it |
|--------|------|------|
| `register_start_trial` | `raspberry_timestamp: float, controller_timestamp: float` | At the beginning of each trial. **Required.** |
| `register_end_trial` | `controller_timestamp: float` | At the end of each trial. Optional (see below). |
| `register_enter_state` | `state_name: str, controller_timestamp: float` | Whenever you enter a state (closes the previous one). |
| `register_controller_event` | `name: str, controller_timestamp: float` | To register any other controller event. |

- `raspberry_timestamp`: the Raspberry Pi's own clock — get it with `time_utils.now_timestamp()`.
- `controller_timestamp`: the microcontroller's own clock (e.g. an Arduino's `millis()`, converted to seconds).

`register_start_trial` uses the two timestamps together to compute a clock offset
(`raspberry_timestamp - controller_timestamp`), used to convert every later
`controller_timestamp` back to Raspberry Pi absolute time.

`````{admonition} register_start_trial is required
:class: warning
Call `register_start_trial` at the beginning of **every** trial, in
`create_trial`. Without it **the task stops with an error**.

`register_end_trial` is optional: if `create_trial` returns without calling it,
the trial is ended at that moment (Raspberry time, converted to the controller
clock with the offset above). Call it yourself if you want the controller's own
end time instead.

```python
def create_trial(self):
    t0 = time_utils.now_timestamp()
    c0 = self.read_controller_time()  # your own way of getting it
    self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=c0)
    ...  # the trial: register_enter_state / register_controller_event with
         # the controller's times
    c1 = self.read_controller_time()
    self.register_end_trial(controller_timestamp=c1)  # optional
```

The `arduino_*` examples don't need to read the Arduino's clock at the start:
their Arduino counts from 0 when it receives the command, so `c0` is `0.0`.
`````

#### Registering a Raspberry-side event

```python
def register_raspberry_event(self, name: str, raspberry_timestamp: float) -> None
```

For events generated by the Raspberry Pi itself, asynchronously from the trial
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
`create_trial` (anything registered outside that window is ignored). Which method to use depends on **which clock
timed the event** — there are two:

- **The controller's own clock** (e.g. an Arduino's `millis()`, in seconds): for
  events the controller detects and timestamps itself — a poke on a port wired to
  the Arduino. Use `register_controller_event`; it is converted to Raspberry Pi
  time with the offset computed in `register_start_trial`.
- **The Raspberry Pi's clock** (`time_utils.now_timestamp()`): for events the Pi
  itself detects or produces — a camera or touchscreen detection, a direct
  function, a sound. Use `register_raspberry_event`.

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

Tasks Examples <../examples/tasks_arduino.md>
../examples/arduino_1_habituation.md
../examples/arduino_2_passive.md
../examples/arduino_3_active.md
../examples/arduino_4_center_initiated.md
../examples/arduino_5_introduce_penalty.md
../examples/arduino_6_delay.md
```
