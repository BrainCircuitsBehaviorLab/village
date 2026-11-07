## Tasks (Bpod)

With Bpod (`BEHAVIOR_CONTROLLER` set to `BPOD` in `SETTINGS`), every trial is a Bpod
state machine: your task describes the states of the trial, Bpod runs them with its
own precise timing, and everything that happens (states, pokes, timers...) is recorded
automatically.

A task is a class that inherits from `TaskBase`, in any `.py` file inside your
project's `code` directory. The name of the class is the name of the task: the one
shown in the GUI and used in `next_task` by the training protocol. The file name
does not matter.

### How a task runs

1. `start()` is called once, when the session starts.
2. Then, trial after trial:
   - `create_trial()` builds the state machine of the trial;
   - Bpod runs it, and the task waits until the trial ends;
   - `self.trial_data` is filled with everything that happened in the trial;
   - `after_trial()` reads it and registers the values to save, at least `water`.
3. `close()` is called once, when the session ends.

The session ends when it reaches `maximum_duration` (set in the training protocol),
when the STOP button is pressed, or when your task sets `self.force_stop = True`. The
system checks these conditions continuously, not only between trials: if one is met
during a trial, the session ends at once and that trial is cut (it is not saved in the
session file, only in the RAW file). In Manual mode the session also ends after the
number of trials chosen when launching the task; this limit is reached at the end of
a trial, so nothing is lost.

While Bpod runs a trial your Python code is waiting, so it cannot react in the
middle of a trial by itself. Two channels connect the Raspberry Pi and Bpod during
the trial: **softcodes** from Bpod make the Raspberry Pi run a direct function (to
play a sound, show an image...), and **softcodes** from the Raspberry Pi to Bpod let the
state machine react to something only the Raspberry Pi sees (the camera, the
touchscreen...). Both are shown in the [examples](#examples).

---

### Reference

#### The four methods you write

| Method | Called | Use it to |
| :--- | :--- | :--- |
| `start(self)` | Once, before the first trial. | Compute what the whole session needs: valve times, sounds, stimulus positions... |
| `create_trial(self)` | At the start of every trial. | Build the trial's state machine with `self.bpod.add_state`. It starts empty every trial; when the method returns, it is sent to Bpod and run. |
| `after_trial(self)` | After every trial. | Read `self.trial_data`, decide the outcome, and save values with `register_value`. Registering `water` is mandatory. |
| `close(self)` | Once, after the last trial (session finished, stopped, or error). | Clean up: close files or connections. Usually `pass`. |

```{admonition} Register water in every trial
:class: warning
Call `self.register_value("water", ...)` in every `after_trial`, with the microliters
delivered in the trial (`0` if none). The system adds them up to know how much each
subject drinks, and raises an alarm if it is too little.
```

#### Methods you can call

| Method | Use |
| :--- | :--- |
| `self.register_value(name, value)` | Saves a value in the trial's row of the session file (a column named `name`). Call it in `after_trial`. |
| `self.register_raspberry_event(name, timestamp)` | Records an event that happened on the Raspberry Pi (a camera detection, a touch...) with `time_utils.now_timestamp()` as timestamp. If it happens during a trial, it is added to `trial_data` like the Bpod events. |
| `self.execute_function(i)` | Runs direct function `i` (1-98), see [Direct Functions](functions.md). |
| `self.bpod.add_state(...)` | Adds a state to the trial's state machine (see [Bpod primitives](bpod-primitives)). |
| `self.bpod.send_softcode_to_bpod(i)` | Sends softcode `i` from the Raspberry Pi to Bpod, usually from a trigger (camera, touchscreen...). The state machine reacts to it with `BpodEvent.SoftCode<i>`. |
| `self.bpod.set_global_timer(...)`, `set_global_counter(...)`, `set_condition(...)` | Advanced primitives, see [Bpod primitives](bpod-primitives). |

With Bpod, the start and end of every trial, state and event are recorded
automatically: the `register_start_trial`, `register_end_trial`,
`register_enter_state` and `register_controller_event` methods are only for tasks
without Bpod.

#### Attributes you can use

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `self.settings` | `Settings` | The subject's training settings, defined in the [training protocol](creating.md) (e.g. `self.settings.reward_volume`). Changes made during the session are kept for the next one. |
| `self.calibrations` | `Calibrations` | Calibrations, e.g. `self.calibrations.water_calibration.get_valve_time(port, volume)` or `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`. |
| `self.bpod` | `BpodController` | The Bpod interface (see the methods above). |
| `self.trial_data` | `dict` | Everything that happened in the trial, available in `after_trial` (see [Trial data](#trial-data)). |
| `self.info` | `str` | Description of the task, shown when it is selected in the GUI. Set it in `__init__`. |
| `self.name` | `str` | The name of the task, which is the name of its class (e.g. `"LightAndWater"`). |
| `self.subject` | `str` | The name of the subject (`"None"` when a task is launched manually without a subject). |
| `self.current_trial` | `int` | The number of the current trial, starting from 1. |
| `self.system_name` | `str` | The name of the system (`SYSTEM_NAME` in `SETTINGS`). |
| `self.date` | `str` | The date and time the session started (`"2026-11-07 10:30:00"`). |
| `self.run_mode` | `str` | `"Auto"` or `"Manual"`. |
| `self.chrono` | `Chrono` | `self.chrono.get_time()` is the time in seconds since the session started. |
| `self.force_stop` | `bool` | Set it to `True` to end the session (see [Ending the session from the task](#ending-the-session-from-the-task)). |
| `self.stop_button_pressed` | `bool` | `True` once the STOP button has been pressed. Read it, don't set it. |
| `self.should_stop` | `bool` | `True` once any stopping condition is met (read-only). The system checks it and ends the session; with Bpod you rarely need it. |
| `self.system_state` | `State` | The state of the system, e.g. `State.RUN_OPEN` (Auto mode, the subject can leave the box). Import `State` from `village.classes.enums`. |
| `self.cam_box` | `Camera` | The box camera (see [Camera](../devices/camera.md)). |
| `self.gpio` | `Gpio` | The GPIO output pin: `set_on()` / `set_off()` (see [GPIO](../devices/gpio.md)). |
| `self.custom_areas` | `dict` | The detection areas with a custom shape, if the project defines any (see [Camera](../devices/camera.md#custom-detection-area)). |

You can also add your own attributes (`self.side = "left"`): they are kept from one
method to the next, and the triggers and direct functions can read them through
`self.task`.

(bpod-primitives)=
#### Bpod primitives

`BpodEvent` and `BpodOutput` are imported together with `TaskBase`:

```python
from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
```

A state is added with:

```python
self.bpod.add_state(
    state_name="light_on",           # any name; "exit" ends the trial
    state_timer=5,                   # seconds until the Tup event (0: no timer)
    state_change_conditions={        # event -> next state
        BpodEvent.Port2In: "reward",
        BpodEvent.Tup: "exit",
    },
    output_actions=[(BpodOutput.PWM2, 255)],  # what is on during the state
)
```

The trial starts in the first state added and ends when a transition goes to
`"exit"`. Every state turns off all the outputs of the previous one and turns on only
its own `output_actions`, so there is no need to turn anything off. A state with
`state_timer=0` and no `Tup` condition waits for its events indefinitely; with
`state_timer=0` and a `Tup` condition, it fires its outputs and moves on at once.

**Events** (`state_change_conditions`):

| Event | When it happens |
| :--- | :--- |
| `BpodEvent.Tup` | The state's timer (`state_timer`) runs out. |
| `BpodEvent.Port1In` ... `Port8In` | The animal pokes into port N (its infrared beam is broken). |
| `BpodEvent.Port1Out` ... `Port8Out` | The animal leaves port N. |
| `BpodEvent.BNC1High`, `BNC1Low`, `BNC2High`, `BNC2Low` | A TTL signal on a BNC input goes high or low. |
| `BpodEvent.SoftCode1`, `SoftCode2`... | The Raspberry Pi sent that softcode with `self.bpod.send_softcode_to_bpod(i)`. |
| `BpodEvent.GlobalTimer1End`... | A global timer ends (see below). |

**Outputs** (`output_actions`):

| Output | What it does |
| :--- | :--- |
| `(BpodOutput.PWM1, value)` ... `PWM8` | Turns on the LED of port N with an intensity from 0 to 255. |
| `BpodOutput.Valve1` ... `Valve8` | Opens the valve of port N during the state: use the valve time as `state_timer`. |
| `BpodOutput.BNC1High`, `BNC2High` | Sets a BNC output high (a TTL to another device) during the state. |
| `BpodOutput.SoftCode1` ... `SoftCode98` | Makes the Raspberry Pi run direct function N, at the moment the state starts. |
| `BpodOutput.GlobalTimer1Trig`, `GlobalTimer1Cancel`... | Starts or cancels a global timer. |

**Advanced primitives:**

- **Global timers**: a timer that keeps running across states, independently of each
  state's own timer, e.g. a deadline for the whole trial. Configure it with
  `self.bpod.set_global_timer(timer_id=1, timer_duration=10)`, start it with the
  output `BpodOutput.GlobalTimer1Trig` and react to `BpodEvent.GlobalTimer1End`. See
  [bpod_global_timer.py](../examples/bpod_global_timer.md).
- **Global counters** (`self.bpod.set_global_counter(counter_number, target_event,
  threshold)`): count an event and fire `GlobalCounterNEnd` when a threshold is
  reached.
- **Conditions** (`self.bpod.set_condition(condition_number, condition_channel,
  channel_value)`): check the current level of a channel at the moment of a
  transition, instead of reacting to a change.

For global counters, conditions and Bpod modules, see the
[Bpod documentation](https://sanworks.github.io/Bpod_Wiki/).
[bpod_outputs_and_events.py](../examples/bpod_outputs_and_events.md) shows every
event and output of the tables above in a single task.

---

### Examples

#### A simple task: light and water

The center port lights up; if the animal pokes it, it gets water; if not, the trial
ends after `led_on_time` seconds. The settings it uses (`reward_volume`,
`led_on_time`, `led_intensity`, `iti_time`) are defined in the training protocol.

```python
import math

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class LightAndWater(TaskBase):
    def __init__(self):
        super().__init__()
        self.info = """
        Light and Water
        ---------------
        The center port lights up; poking it delivers water.
        """

    def start(self):
        # the time valve 2 must stay open to deliver reward_volume microliters
        self.valve_time = self.calibrations.water_calibration.get_valve_time(
            port=2, volume=self.settings.reward_volume
        )

    def create_trial(self):
        self.bpod.add_state(
            state_name="light_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions={
                BpodEvent.Port2In: "reward",
                BpodEvent.Tup: "exit",
            },
            output_actions=[(BpodOutput.PWM2, self.settings.led_intensity)],
        )
        self.bpod.add_state(
            state_name="reward",
            state_timer=self.valve_time,
            state_change_conditions={BpodEvent.Tup: "iti"},
            output_actions=[BpodOutput.Valve2],
        )
        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        # a state that was not visited appears as [nan]
        rewarded = not math.isnan(self.trial_data["STATE_reward_START"][0])
        self.register_value("outcome", "correct" if rewarded else "miss")
        self.register_value("water", self.settings.reward_volume if rewarded else 0)

    def close(self):
        pass
```

The water calibration must exist for port 2, or `get_valve_time` raises an error.

#### Playing a sound

The sound card is controlled by the Raspberry Pi, not by Bpod. The task loads the
sound once, in `start`, and the state machine asks the Raspberry Pi to play it with
a softcode: `BpodOutput.SoftCode1` runs direct function 1 at the moment the state
starts.

In `direct_functions.py`:

```python
from village.custom_classes.direct_functions_base import DirectFunctionsBase
from village.devices.sound_device import sound_device


class DirectFunctions(DirectFunctionsBase):
    def function1(self):
        """Play Loaded Sound"""
        sound_device.play()
```

In the task, the sound plays when the animal pokes the center port, together with
the water:

```python
from sound_functions import whitenoise_generator

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
from village.devices.sound_device import sound_device


class SoundAndWater(TaskBase):
    def start(self):
        self.valve_time = self.calibrations.water_calibration.get_valve_time(
            port=2, volume=self.settings.reward_volume
        )
        sound = whitenoise_generator(duration=0.5, gain=0.05)
        sound_device.load(left=sound, right=sound)  # loaded once, played every trial

    def create_trial(self):
        self.bpod.add_state(
            state_name="wait_poke",
            state_timer=60,
            state_change_conditions={
                BpodEvent.Port2In: "sound_and_water",
                BpodEvent.Tup: "exit",
            },
            output_actions=[],
        )
        self.bpod.add_state(
            state_name="sound_and_water",
            state_timer=self.valve_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[BpodOutput.SoftCode1, BpodOutput.Valve2],
        )

    ...  # after_trial and close as in the first example
```

`gain=0.05` is an arbitrary volume; to play the sound at a given level in dB, use the
sound calibration (see [Sound](../devices/sound.md)).

#### Reacting to the camera

The camera is also on the Raspberry Pi, so the information goes the other way: the
camera trigger sends a softcode to Bpod, and the state machine waits for it. In this
example the animal gets water when it enters box area 1 (set as a TRIGGER area, with
`CAM_BOX_TRACKING_POSITION` ON).

In `camera_trigger.py`, which runs on every camera frame:

```python
from village.custom_classes.camera_trigger_base import CameraTriggerBase
from village.devices.camera import Camera
from village.scripts.time_utils import time_utils


class CameraTrigger(CameraTriggerBase):
    def __init__(self) -> None:
        super().__init__()
        self.inside = False

    def trigger(self, cam: Camera) -> None:
        if cam.name != "BOX":
            return
        # only when the animal enters, not on every frame while it is inside
        if cam.area1_is_triggered and not self.inside:
            self.task.register_raspberry_event("area1_entered", time_utils.now_timestamp())
            self.task.bpod.send_softcode_to_bpod(1)
        self.inside = cam.area1_is_triggered
```

In the task:

```python
    def create_trial(self):
        self.bpod.add_state(
            state_name="wait_area1",
            state_timer=60,
            state_change_conditions={
                BpodEvent.SoftCode1: "reward",  # sent by camera_trigger.py
                BpodEvent.Tup: "exit",
            },
            output_actions=[],
        )
        self.bpod.add_state(
            state_name="reward",
            state_timer=self.valve_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[BpodOutput.Valve2],
        )
```

The touchscreen works the same way: in `touch_trigger.py`, `trigger(self, x, y,
timestamp)` is called on every touch, and it sends a softcode when the touch is
inside a target. See [Screen & Touchscreen](../devices/screen.md#reacting-to-touches)
and [bpod_touchscreen.py](../examples/bpod_touchscreen.md).

#### Complete examples

The tasks of the example project, from habituation to a full discrimination task,
with the state machine diagram of each one, are in
[Task Examples (Bpod)](../examples/tasks_bpod.md). Among them,
[bpod_area2_sound.py](../examples/bpod_area2_sound.md) combines the last two
examples: entering an area plays a sound and delivers water.

---

### Trial data

When a trial ends, everything that happened in it is put in `self.trial_data`, a
dictionary that `after_trial` reads to decide the outcome of the trial. Its keys:

| Key | Value |
| :--- | :--- |
| `"date"`, `"trial"`, `"subject"`, `"task"`, `"system_name"` | Which session and trial it is. |
| `"TRIAL_START"`, `"TRIAL_END"` | When the trial started and ended. |
| `"STATE_<name>_START"`, `"STATE_<name>_END"` | For every state of the state machine, a list with the times it was entered and left (a list, because a state can be visited several times). A state that was **not visited** has `[nan]`. |
| `"<event>"` (`"Port1In"`, `"Tup"`, `"SoftCode1"`...) | For every event that happened, a list with the times of each occurrence. Events that did not happen are not in the dictionary. Events registered with `register_raspberry_event` during the trial are included too, and so are the ones the system registers by itself: `sound` when a sound starts playing, `touch_<x>_<y>` for every touch. |
| `"ordered_list_of_events"` | The names of all the events, in the order they happened. |

All the times are in seconds (UNIX time, the same clock for Bpod and the Raspberry
Pi), so they can be compared and subtracted directly.

For example, a trial of the first example in which the animal pokes port 3 (which
does nothing), then the lit port 2, and gets water:

```python
{
    "date": "2026-11-07 10:30:00",
    "trial": 12,
    "subject": "mouse1",
    "task": "LightAndWater",
    "system_name": "village01",
    "TRIAL_START": 1793961045.20,
    "TRIAL_END": 1793961048.43,
    "STATE_light_on_START": [1793961045.20],
    "STATE_light_on_END": [1793961047.38],
    "STATE_reward_START": [1793961047.38],
    "STATE_reward_END": [1793961047.43],
    "STATE_iti_START": [1793961047.43],
    "STATE_iti_END": [1793961048.43],
    "Port3In": [1793961046.10],
    "Port3Out": [1793961046.31],
    "Port2In": [1793961047.38],
    "Tup": [1793961047.43, 1793961048.43],
    "ordered_list_of_events": ["Port3In", "Port3Out", "Port2In", "Tup", "Tup"],
}
```

The usual questions are answered like this (the comments give the results for the
trial above):

```python
import math

def after_trial(self):
    # Was a state visited? Its first start time is not nan.
    rewarded = not math.isnan(self.trial_data["STATE_reward_START"][0])  # True

    # Did an event happen? Its key exists: use .get with an empty list by default.
    poked_port3 = len(self.trial_data.get("Port3In", [])) > 0  # True

    # How long did something take? Subtract two times.
    light_on = self.trial_data["STATE_light_on_START"][0]
    light_off = self.trial_data["STATE_light_on_END"][0]
    response_time = light_off - light_on  # 2.18 s

    # Which port was poked first after the light turned on? Compare the times.
    pokes = [
        (t, port)
        for port in ("Port1In", "Port2In", "Port3In")
        for t in self.trial_data.get(port, [])
        if t > light_on
    ]
    first_poke = min(pokes)[1] if pokes else "none"  # "Port3In"

    self.register_value("first_poke", first_poke)
    self.register_value("response_time", response_time)
    self.register_value("water", self.settings.reward_volume if rewarded else 0)
```

#### What is saved

At the end of each trial, `trial_data` (with the values registered in `after_trial`)
becomes one row of the session table. When the session ends, two files are saved:

- **`<session>.csv`**: one row per trial, with a column for each key above and each
  registered value. It is the file used for the analysis and by the training
  protocol (`self.df`). A trial only gets its row when it finishes, so the trial
  that was running when the session stopped is not in it.
- **`<session>_RAW.csv`**: one line per event, written as they happen, including
  the trial that was interrupted.

The session is saved if at least one trial was completed. Design the task so that
trials end after a reasonable time even if the animal does nothing (with a `Tup`
condition, as in the examples): a session that is a single trial that never ends
would not be saved.

---

(force-stop)=
### Ending the session from the task

Set `self.force_stop = True` to end the session. The session ends at once, so set it
in `after_trial`, when the trial is already complete: set during a trial (from a
trigger or a direct function), it cuts that trial. It works in Auto mode too: the
session is saved and the subject is let out, as when `maximum_duration` is reached,
even before `minimum_duration`. For example, to stop after a maximum number of trials
(`max_trials` defined in the training protocol):

```python
def after_trial(self):
    ...
    if self.current_trial >= self.settings.max_trials:
        self.force_stop = True
```

The same works for any criterion: an amount of water, a number of correct trials...

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
../examples/bpod_global_timer.md
../examples/bpod_outputs_and_events.md
../examples/bpod_purge_ports.md
```
