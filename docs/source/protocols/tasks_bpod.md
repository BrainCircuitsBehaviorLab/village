## Tasks (Bpod)

With Bpod (`BEHAVIOR_CONTROLLER` set to `BPOD` in `SETTINGS`), every trial is a
Bpod state machine: the task builds it in `create_trial`, Bpod runs it with its own
precise timing, and everything that happened (states, pokes, timers...) is recorded
automatically in the trial data.

To create a task, create a Python file inside your project's `code` directory, and
within it, a class named after the task, inheriting from the generic `TaskBase`
class. Naming conventions follow Python standards: CamelCase for class names,
lower_case for filenames and function/variable names. Let's look at an example.

### A minimal task

[bpod_1_habituation.py](../examples/bpod_1_habituation.md) is the simplest real task of the examples — the
mouse is just left alone in the box, pokes are logged, no reward is given:

```python
from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class Bpod1Habituation(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = """
        Habituation Task (Bpod)
        ----------------------------------------------------------
        This task is an automatic mouse habituation to the box.
        Nothing will happen during the task, the mouse will be left alone in the box
        for the duration of the task.
        Port pokes will be registered but no reward will be delivered.
        """
```

The task is named `Bpod1Habituation`. It's initialized with `__init__`, and we
acquire all the properties of the generic `TaskBase` class using `super().__init__()`.
`self.info` is shown to the user when the task is selected in the GUI to run
manually.

Four methods must be implemented in your class: `start`, `create_trial`,
`after_trial`, and `close`.

### The `start()` method

Called once, when the task starts. Use it to compute anything the whole session
needs — valve opening times, loaded sounds, opened serial connections, etc.

```python
    def start(self):
        """In this simple task we don't need to do anything in the start method."""

        pass
```

The most commonly used attributes available by default inside any task method
(see the `TaskBase` class docstring for the full list) are:

- `self.bpod` — the Bpod interface, used inside `create_trial` to build the state
  machine.
- `self.settings` — the session's parameters, as defined in `training_protocol.py`
  (e.g. `self.settings.reward_volume`).
- `self.calibrations` — convert hardware values to real-world units, e.g.
  `self.calibrations.water_calibration.get_valve_time(port, volume)` or
  `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`.
- `self.cam_box`, `self.gpio`, `self.custom_areas` — the box camera, GPIO output
  control, and any custom-shaped detection areas the project defines.
- `self.name`, `self.subject`, `self.current_trial`, `self.system_name`, `self.date`.
- `self.trial_data` — populated automatically after each trial, available inside
  `after_trial` (see below).

A task that delivers water almost always needs a valve opening time first —
calibrate the ports from the Water Calibration panel before using this, or it
raises an exception:

```python
    def start(self):
        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )
```

### The `create_trial()` method

Called once per trial. It builds the Bpod state machine for that trial (the
machine is only sent to Bpod and actually run once `create_trial` returns).

```python
    def create_trial(self):
        """
        This task is very simple, the state machine has only one state
        called "ready_to_explore". We give it a 60-second timer and a
        timer-up condition (once the timer elapses) that takes us to "exit".
        Also, every time there's a poke in any port, we switch to the "exit" state.
        """

        self.bpod.add_state(
            state_name="ready_to_explore",
            state_timer=60,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                BpodEvent.Port1In: "exit",
                BpodEvent.Port2In: "exit",
                BpodEvent.Port3In: "exit",
            },
            output_actions=[],
        )
```

`BpodEvent` and `BpodOutput` (imported from `village.custom_classes.task_base`
alongside `TaskBase`) enumerate every Bpod input event and output action. See
[More Bpod primitives](#more-bpod-primitives) below for a full walkthrough of
`add_state`, LEDs, valves, softcodes and TTL.

### The `after_trial()` method

Called once after each trial ends, to register whatever values you want saved
to the session's data file. `self.trial_data` is populated automatically by
then — `self.trial_data.get("Port1In", [])` is the list of timestamps at which
port 1 was poked during the trial (empty if it never was), and
`self.trial_data.get("STATE_<name>_START", [])` / `"..._END"` likewise for every
Bpod state visited.

```python
    def after_trial(self):
        """
        Here we look at the trial_data dictionary that bpod records automatically
        to find out which events we got.
        """

        outcome = "miss"

        # for each portIn, we have a list of times at which pokes were registered,
        # so we check that there's an entry for that port and that it isn't empty,
        # which indicates that a poke happened.
        if self.trial_data.get("Port1In"):
            outcome = "left_poke"
        if self.trial_data.get("Port2In"):
            outcome = "center_poke"
        if self.trial_data.get("Port3In"):
            outcome = "right_poke"

        # Register the outcome of the trial and the water consumed.
        # Registering "water" (in microliters) is mandatory on every task --
        # it's how the system tracks each subject's daily water intake.
        self.register_value("outcome", outcome)
        self.register_value("water", 0)
```

### The `close()` method

Called once when the task finishes (session ends, or manually stopped). Use it
for any cleanup — closing a serial connection, sending a Slack/email summary,
generating a plot, etc.

```python
    def close(self):
        """
        We don't need to do any extra work when the task finishes.
        """

        pass
```

### A more complete example: FollowTheLight

Now let's look at a task closer to a real 2-choice discrimination protocol —
[bpod_4_center_initiated.py](../examples/bpod_4_center_initiated.md) and
[bpod_5_introduce_penalty.py](../examples/bpod_5_introduce_penalty.md) are
the real versions of this in the examples (respectively without and with a
penalty for the wrong side); this walkthrough merges both into one task that
switches behavior based on `self.settings.stage`:

- The mouse initiates each trial by poking the center port (its LED turns on).
- After the center poke, one of the two side LEDs turns on at random.
- Poking the correct side delivers a reward.
- In stage 1, poking the wrong side does nothing (the mouse can just try again).
  In stage 2, it triggers a penalty (noise + timeout) instead.
- Progression between stages is decided in `training_protocol.py`'s
  `update_training_settings`, based on performance.

```python
import random

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class FollowTheLight(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = """
        Follow The Light Task
        -------------------
        The mouse pokes the center port to start a trial. One of the two side
        ports then lights up; poking it delivers a reward. Stage 1 has no
        penalty for the wrong side, stage 2 does (see self.settings.stage).
        """

    def start(self):
        """
        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: reward volume delivered on a correct poke
        - self.settings.led_intensity: port LED brightness (0-255)
        - self.settings.c_led_on_time: time allowed to poke the center port, seconds
        - self.settings.led_on_time: time allowed to poke the correct side, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        - self.settings.stage: 1 (no penalty) or 2 (penalty for the wrong side)
        - self.settings.noise_time, self.settings.timeout: only used in stage 2
        """

        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )

    def create_trial(self):
        self.side = random.choice(["left", "right"])

        if self.side == "left":
            valvetime = self.valve_l_time
            valve_action = BpodOutput.Valve1
            correct_led = (BpodOutput.PWM1, self.settings.led_intensity)
            correct_side = BpodEvent.Port1In
            wrong_side = BpodEvent.Port3In
        else:
            valvetime = self.valve_r_time
            valve_action = BpodOutput.Valve3
            correct_led = (BpodOutput.PWM3, self.settings.led_intensity)
            correct_side = BpodEvent.Port3In
            wrong_side = BpodEvent.Port1In

        # In stage 1, a wrong poke isn't wired to any transition, so it's just
        # ignored and the mouse can try again before "side_led_on" times out.
        side_led_on_conditions = {
            BpodEvent.Tup: "exit",
            correct_side: "water_delivery",
        }
        if self.settings.stage == 2:
            side_led_on_conditions[wrong_side] = "wrong_choice"

        # 'c_led_on': center LED on, waits for the trial-initiating center poke
        self.bpod.add_state(
            state_name="c_led_on",
            state_timer=self.settings.c_led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                BpodEvent.Port2In: "side_led_on",
            },
            output_actions=[(BpodOutput.PWM2, self.settings.led_intensity)],
        )

        # 'side_led_on': only the correct side's LED turns on
        self.bpod.add_state(
            state_name="side_led_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions=side_led_on_conditions,
            output_actions=[correct_led],
        )

        self.bpod.add_state(
            state_name="water_delivery",
            state_timer=valvetime,
            state_change_conditions={BpodEvent.Tup: "iti"},
            output_actions=[valve_action],
        )

        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

        # Stage 2 only: noise, then a silent timeout, before exiting.
        self.bpod.add_state(
            state_name="wrong_choice",
            state_timer=self.settings.noise_time,
            state_change_conditions={BpodEvent.Tup: "timeout"},
            output_actions=[BpodOutput.SoftCode4],
        )

        self.bpod.add_state(
            state_name="timeout",
            state_timer=self.settings.timeout - self.settings.noise_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        """Work out response_side and outcome for this trial.

        Whichever side the animal poked first (if any) after the side LED
        turned on determines the outcome, independently of which Bpod state
        that poke happened to transition into -- this way stage 1 (where a
        wrong poke isn't wired to any transition) and stage 2 (where it goes
        to "wrong_choice") are scored the same way.
        """

        side_led_on_start = self.trial_data.get("STATE_side_led_on_START")
        if not side_led_on_start:
            # The center poke never happened -> side LED never turned on.
            self.register_value("rewarded_side", self.side)
            self.register_value("water", 0)
            self.register_value("outcome", "omission")
            self.register_value("response_side", "none")
            return

        t_side_led_on = side_led_on_start[0]

        correct_key, wrong_key = (
            ("Port1In", "Port3In") if self.side == "left" else ("Port3In", "Port1In")
        )
        correct_pokes = [
            t for t in self.trial_data.get(correct_key, []) if t >= t_side_led_on
        ]
        wrong_pokes = [
            t for t in self.trial_data.get(wrong_key, []) if t >= t_side_led_on
        ]

        if correct_pokes and (not wrong_pokes or correct_pokes[0] <= wrong_pokes[0]):
            outcome = "correct"
            response_side = self.side
            water = self.settings.reward_volume
        elif wrong_pokes:
            outcome = "incorrect"
            response_side = "right" if self.side == "left" else "left"
            water = 0
        else:
            outcome = "miss"
            response_side = "none"
            water = 0

        self.register_value("rewarded_side", self.side)
        self.register_value("water", water)
        self.register_value("outcome", outcome)
        self.register_value("response_side", response_side)

    def close(self):
        pass
```

---

### More Bpod primitives

For a runnable walkthrough of the Bpod building blocks, see two reference
tasks of the examples (neither is a real behavioral protocol):

- [bpod_example_outputs_and_events.py](../examples/bpod_example_outputs_and_events.md) — LEDs, a valve, poke in/out,
  softcodes in both directions, and TTL pulses in both directions.
- [bpod_example_global_timer.py](../examples/bpod_example_global_timer.md) — a global timer: a deadline that ticks in
  the background across every state, independently of each state's own
  timer, until it ends or is cancelled.

Two more primitives exist beyond what those examples cover — global counters
(`self.bpod.set_global_counter(counter_number, target_event, threshold)`,
counts occurrences of an event and fires once a threshold is reached) and
conditions (`self.bpod.set_condition(condition_number, condition_channel,
channel_value)`, checks a channel's current level at the moment of a
transition rather than reacting to an edge). For both, see the official Bpod
documentation: [sanworks.github.io/Bpod_Wiki](https://sanworks.github.io/Bpod_Wiki/).

---

### Methods you must override

| Method | Called | Use it to |
|--------|--------|-----------|
| `start(self)` | Once, before the trial loop begins. | Configure hardware, pre-compute stimuli, open files, etc. |
| `create_trial(self)` | Once at the start of every trial. | Build the trial's state machine with `self.bpod.add_state`. |
| `after_trial(self)` | Immediately after each trial finishes. | Score performance, update adaptive parameters, call `register_value`. |
| `close(self)` | Once after the trial loop ends (session finished, forced stop, or error). | Close files, stop hardware, release resources. |

```{admonition} create_trial with Bpod
:class: note
Each call starts with an empty state machine. Add states with `self.bpod.add_state`
— when the method returns, the state machine is sent and run automatically, and
`after_trial` is called once it finishes.
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

#### Trial, states and controller events

With Bpod, the start and end of every trial, every state and every Bpod event are
registered automatically: you never need to call `register_start_trial`,
`register_end_trial`, `register_enter_state` or `register_controller_event`.

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
| `self.bpod` | `BpodController` | Bpod interface — state machine construction, sending, etc. Mainly used inside `create_trial`. |
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

#### `self.trial_data` (dict)

Populated automatically at the end of each trial — available inside `after_trial`.

**Keys always present:**

- `"date"` (str), `"trial"` (int), `"subject"` (str), `"task"` (str), `"system_name"` (str)
- `"TRIAL_START"` / `"TRIAL_END"` (float): absolute timestamps (UNIX epoch seconds)
- `"ordered_list_of_events"` (list[str]): event names in the order they occurred (e.g. `["Port1In", "Port1Out", "Port1In"]`)

With Bpod all of them are filled automatically.

**Keys added per state** (Bpod states):

- `"STATE_<name>_START"` / `"STATE_<name>_END"` (list[float]): timestamps of every
  entry/exit for that state — a list because the same state can be visited more
  than once per trial.

They are added automatically for every state of the state machine. A state that
was **not visited** still appears, with `[nan]`: to check whether a state was
visited, look at its first start time (see the example below).

**Keys added per event type:**

- `"<EventName>"` (list[float]): timestamps of every occurrence of that event
  (e.g. `"Port1In"`, `"Port1Out"`, `"Tup"`, `"SoftCode1"`).

Bpod events are added automatically. Events you register yourself with
`register_raspberry_event` (only those registered while the trial is running) are
added the same way, in the same absolute time as the Bpod events.

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
    # 1. Did the animal reach the REWARD state? With Bpod a state that was not visited is [nan].
    # The default makes it work as well if the key is missing.
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

Tasks Examples <../examples/tasks_bpod.md>
../examples/bpod_1_habituation.md
../examples/bpod_2_passive.md
../examples/bpod_3_active.md
../examples/bpod_4_center_initiated.md
../examples/bpod_5_introduce_penalty.md
../examples/bpod_6_delay.md
../examples/bpod_area2_sound.md
../examples/bpod_touchscreen.md
../examples/bpod_example_global_timer.md
../examples/bpod_example_outputs_and_events.md
../examples/bpod_purge_ports.md
```
