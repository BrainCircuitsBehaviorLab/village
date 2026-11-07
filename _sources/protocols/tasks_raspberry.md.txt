## Tasks (Raspberry Only)

With `BEHAVIOR_CONTROLLER` set to `OTHER` in `SETTINGS` and no microcontroller, the
Raspberry Pi runs the trial itself: it reacts to what it detects (the box camera
areas, the touchscreen, the GPIO input pin, the box scale) and produces the stimuli
(sounds, the screen, the LED strip, the GPIO output pin). Its timing is less precise
than a microcontroller's (see [Timing, Clocks & Latencies](../system_operation/timing.md)):
for fast and precise timing, use Bpod or a microcontroller.

A task is a class that inherits from `TaskBase`, in any `.py` file inside your
project's `code` directory. The name of the class is the name of the task: the one
shown in the GUI and used in `next_task` by the training protocol. The file name does
not matter.

### How a task runs

1. `start()` is called once, when the session starts.
2. Then, trial after trial:
   - `create_trial()` **is** the trial: it registers the start of the trial, waits
     for what has to happen (or a timeout), registers it, and returns when the trial
     is over;
   - `self.trial_data` is filled with everything registered in the trial;
   - `after_trial()` reads it and registers the values to save, at least `water`.
3. `close()` is called once, when the session ends.

The session ends when it reaches `maximum_duration` (set in the training protocol),
when the STOP button is pressed, or when your task sets `self.force_stop = True`. The
system checks these conditions continuously, not only between trials: if one is met
during a trial, the session ends at once and that trial is cut (it is not saved in the
session file, only in the RAW file). In Manual mode the session also ends after the
number of trials chosen when launching the task; this limit is reached at the end of
a trial, so nothing is lost.

`````{admonition} Check should_stop in your waiting loops
:class: warning
The system ends the session, but it cannot stop your Python code: a `create_trial`
waiting for something would keep running. Every waiting loop must check
`self.should_stop` (and a timeout), so it can never wait forever:

```python
while not self.should_stop and time_utils.now_timestamp() < deadline:
    ...  # wait for your own condition
```
`````

**Triggers.** The detections arrive through the triggers (camera, touchscreen, GPIO,
scale), which run in their own threads and call your code while the task is running.
The usual pattern is: the trigger reacts and signals the task (with a
`threading.Event`), and the loop of `create_trial` waits for that signal, or a
timeout, to end the trial.

**One clock.** Here the Raspberry Pi is also the controller, so there is only one
clock: pass `time_utils.now_timestamp()` as every timestamp, and the same time as both
clocks in `register_start_trial`.

---

### Reference

#### The four methods you write

| Method | Called | Use it to |
| :--- | :--- | :--- |
| `start(self)` | Once, before the first trial. | Compute what the whole session needs: sounds, stimulus positions... and create the signals the triggers will use. |
| `create_trial(self)` | Every trial. | Run the trial: call `register_start_trial`, wait for the trigger's signal or a timeout, and register what happened. |
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
| `self.register_start_trial(raspberry_timestamp, controller_timestamp)` | **Required** at the start of every trial, in `create_trial`: without it the task stops with an error. Pass `time_utils.now_timestamp()` as both. |
| `self.register_end_trial(controller_timestamp)` | Ends the trial. Optional: if `create_trial` returns without calling it, the trial is ended at that moment. |
| `self.register_enter_state(state_name, controller_timestamp)` | If your trial is organized in states: closes the previous state and opens this one, as Bpod does. |
| `self.register_raspberry_event(name, timestamp)` | Records an event (a camera detection, a GPIO input...) with `time_utils.now_timestamp()` as timestamp. `register_controller_event` does exactly the same here. |
| `self.register_value(name, value)` | Saves a value in the trial's row of the session file (a column named `name`). Call it in `after_trial`. |
| `self.execute_function(i)` | Runs direct function `i` (1-98), see [Direct Functions](functions.md). |

The `register_*` methods only record what happens between `register_start_trial` and
the end of the trial: anything registered outside that window is ignored.

#### Attributes you can use

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `self.settings` | `Settings` | The subject's training settings, defined in the [training protocol](creating.md) (e.g. `self.settings.reward_volume`). Changes made during the session are kept for the next one. |
| `self.calibrations` | `Calibrations` | Calibrations, e.g. `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`. |
| `self.trial_data` | `dict` | Everything registered in the trial, available in `after_trial` (see [Trial data](#trial-data)). |
| `self.info` | `str` | Description of the task, shown when it is selected in the GUI. Set it in `__init__`. |
| `self.name` | `str` | The name of the task, which is the name of its class (e.g. `"RaspberryArea1Sound"`). |
| `self.subject` | `str` | The name of the subject (`"None"` when a task is launched manually without a subject). |
| `self.current_trial` | `int` | The number of the current trial, starting from 1. |
| `self.system_name` | `str` | The name of the system (`SYSTEM_NAME` in `SETTINGS`). |
| `self.date` | `str` | The date and time the session started (`"2026-11-07 10:30:00"`). |
| `self.run_mode` | `str` | `"Auto"` or `"Manual"`. |
| `self.chrono` | `Chrono` | `self.chrono.get_time()` is the time in seconds since the session started. |
| `self.force_stop` | `bool` | Set it to `True` to end the session (see [Ending the session from the task](#ending-the-session-from-the-task)). |
| `self.stop_button_pressed` | `bool` | `True` once the STOP button has been pressed. Read it, don't set it. |
| `self.should_stop` | `bool` | `True` once any stopping condition is met (read-only). Check it in every waiting loop of `create_trial`. |
| `self.system_state` | `State` | The state of the system, e.g. `State.RUN_OPEN` (Auto mode, the subject can leave the box). Import `State` from `village.classes.enums`. |
| `self.cam_box` | `Camera` | The box camera (see [Camera](../devices/camera.md)). |
| `self.gpio` | `Gpio` | The GPIO output pin: `set_on()` / `set_off()` (see [GPIO](../devices/gpio.md)). |
| `self.custom_areas` | `dict` | The detection areas with a custom shape, if the project defines any (see [Camera](../devices/camera.md#custom-detection-area)). |

You can also add your own attributes (`self.area1_event`, `self.side = "left"`...):
they are kept from one method to the next, and the triggers and direct functions can
read them through `self.task`.

#### Triggers and devices

The triggers are classes in your `code` directory; each one is called by the system
while a task is running, and reaches the task through `self.task`:

| Trigger | Inherits from | Called | See |
| :--- | :--- | :--- | :--- |
| Camera | `CameraTriggerBase` | On every frame, with the camera (`cam.area1_is_triggered`...). | [Camera](../devices/camera.md#reacting-to-the-animals-position) |
| Touchscreen | `TouchTriggerBase` | On every touch, with its position. | [Screen & Touchscreen](../devices/screen.md#reacting-to-touches) |
| GPIO input | `GpioTriggerBase` | `trigger_on` / `trigger_off`, when the input pin turns on or off. | [GPIO](../devices/gpio.md#reacting-to-the-input-pin) |
| Box scale | `ScaleTriggerBase` | On every reading of the scale, with the weight. | [Scale](../devices/scale.md#reacting-to-the-box-scale) |

The stimuli are produced with the devices of the Raspberry Pi:
[Sound](../devices/sound.md) (`sound_device.load` and `sound_device.play`),
[Screen](../devices/screen.md), [LED Strip](../devices/led_strip.md) and the GPIO
output pin (`self.gpio`). They can be used from the task, from a trigger or from a
direct function.

---

### Examples

#### A simple task: a sound every trial

Every trial plays a sound and then waits for the inter-trial interval. It shows the
structure of every task without a controller: `create_trial` registers the start, the
states as they are entered and the end, and every wait checks `should_stop`.

```python
import time

from sound_functions import whitenoise_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils


class SoundEveryTrial(TaskBase):
    def __init__(self):
        super().__init__()
        self.info = """
        Sound Every Trial
        -----------------
        A sound, then the inter-trial interval.
        """

    def start(self):
        sound = whitenoise_generator(duration=0.5, gain=0.05)
        sound_device.load(left=sound, right=sound)  # loaded once, played every trial

    def create_trial(self):
        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)

        self.register_enter_state("sound", t0)
        sound_device.play()
        self.wait(0.5)

        self.register_enter_state("iti", time_utils.now_timestamp())
        self.wait(self.settings.iti_time)

        self.register_end_trial(time_utils.now_timestamp())

    def wait(self, seconds):
        """Waits the given seconds, less if the task has to stop."""
        end = time_utils.now_timestamp() + seconds
        while not self.should_stop and time_utils.now_timestamp() < end:
            time.sleep(0.01)

    def after_trial(self):
        self.register_value("water", 0)

    def close(self):
        pass
```

`gain=0.05` is an arbitrary volume; to play the sound at a given level in dB, use the
sound calibration, as in the next example (see [Sound](../devices/sound.md)).

#### Reacting to the camera

[raspberry_area1_sound.py](../examples/raspberry_area1_sound.md): every trial waits for
the animal to enter area 1 of the box camera (set as a TRIGGER area, with
`CAM_BOX_TRACKING_POSITION` ON); when it does, a sound is played and an LED of the LED
strip turns on.

The task loads the sound and creates the signal in `start`, and `create_trial` waits
for it:

```python
import threading

from sound_functions import whitenoise_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils

TRIAL_TIMEOUT = 60  # seconds to wait for the animal to enter area 1


class RaspberryArea1Sound(TaskBase):
    def __init__(self):
        super().__init__()
        self.info = """
        Area 1 Sound Task
        -----------------
        Entering BOX area 1 plays a sound and lights an LED of the strip.
        """

    def start(self):
        # the sound at 70 dB, from the sound calibration; loaded once, and
        # played by camera_trigger.py every time area 1 is entered
        gain_left = self.calibrations.sound_calibration.get_sound_gain(
            speaker=0, dB=70, sound_name="whitenoise"
        )
        gain_right = self.calibrations.sound_calibration.get_sound_gain(
            speaker=1, dB=70, sound_name="whitenoise"
        )
        sound_left = whitenoise_generator(duration=1, gain=gain_left)
        sound_right = whitenoise_generator(duration=1, gain=gain_right)
        sound_device.load(left=sound_left, right=sound_right)

        # set by camera_trigger.py the moment area 1 is entered
        self.area1_event = threading.Event()

    def create_trial(self):
        self.area1_event.clear()

        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)

        deadline = t0 + TRIAL_TIMEOUT
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            if self.area1_event.wait(timeout=0.05):
                break

        self.register_end_trial(time_utils.now_timestamp())

    def after_trial(self):
        self.register_value("entered_area1", self.area1_event.is_set())
        self.register_value("water", 0)

    def close(self):
        pass
```

The part of [camera_trigger.py](../examples/camera_trigger.md) that reacts to area 1.
It runs on every frame of the box camera; when the animal is in area 1 and the task's
signal is not set yet, it registers the entry, plays the sound (direct function 4,
"Play Loaded Sound"), lights the LED and sets the signal:

```python
        area1_event = getattr(self.task, "area1_event", None)  # only in this task
        if (
            cam.area1_is_triggered
            and area1_event is not None
            and not area1_event.is_set()
        ):
            self.task.register_raspberry_event(
                "area1_entered", time_utils.now_timestamp()
            )
            self.task.execute_function(4)  # "Play Loaded Sound"

            led_strip.set_led_color(0, 255, 255, 255)
            led_strip.update_strip()

            area1_event.set()
```

The original file also prints a warning in `start` if the camera is not set up for
the task.

#### Reacting to the touchscreen

[raspberry_touchscreen.py](../examples/raspberry_touchscreen.md) follows the same
pattern with the touchscreen: `start` draws 6 rectangles and creates
`self.touch_event`, and `create_trial` waits for it as above. In
[touch_trigger.py](../examples/touch_trigger.md), `trigger(self, x, y, timestamp)` is
called on every touch; when the touch is inside one of the rectangles, it runs a
different visual stimulus for each one and sets the signal:

```python
    def trigger(self, x: int, y: int, timestamp: float) -> None:
        rects = getattr(self.task, "rects", None)  # only in this task
        if rects is not None:
            for i, rect in enumerate(rects):
                if _inside(x, y, rect):
                    self.task.execute_function(FUNCTION_IDS[i])
                    self.task.touch_event.set()
                    return
```

`_inside` checks whether a point is inside a rectangle, and `FUNCTION_IDS` are the
direct functions of the 6 stimuli. Every touch is also recorded automatically as an
event (see [Trial data](#trial-data)).

#### Complete examples

The two examples above, complete, are in
[Task Examples (Raspberry Only)](../examples/tasks_raspberry.md).

---

### Trial data

When a trial ends, everything registered in it is put in `self.trial_data`, a
dictionary that `after_trial` reads to decide the outcome of the trial. Its keys:

| Key | Value |
| :--- | :--- |
| `"date"`, `"trial"`, `"subject"`, `"task"`, `"system_name"` | Which session and trial it is. |
| `"TRIAL_START"`, `"TRIAL_END"` | When the trial started (`register_start_trial`) and ended (`register_end_trial`, or the moment `create_trial` returned). |
| `"STATE_<name>_START"`, `"STATE_<name>_END"` | For every state registered with `register_enter_state`, a list with the times it was entered and left (a list, because a state can be visited several times). A state ends when the next one is entered, or when the trial ends. A state that was **not visited** is not in the dictionary. |
| `"<event>"` (`"area1_entered"`...) | For every event registered, a list with the times of each occurrence. Events that did not happen are not in the dictionary. The ones the system registers by itself are included too: `sound` when a sound starts playing, `touch_<x>_<y>` for every touch (e.g. `touch_640_360`). |
| `"ordered_list_of_events"` | The names of all the events, in the order they happened. |

All the times are in seconds (UNIX time), so they can be compared and subtracted
directly.

For example, a trial of the camera example in which the animal enters area 1 after
8.11 seconds:

```python
{
    "date": "2026-11-07 10:30:00",
    "trial": 12,
    "subject": "mouse1",
    "task": "RaspberryArea1Sound",
    "system_name": "village01",
    "TRIAL_START": 1793961045.20,
    "TRIAL_END": 1793961053.36,
    "area1_entered": [1793961053.31],
    "sound": [1793961053.32],
    "ordered_list_of_events": ["area1_entered", "sound"],
}
```

The usual questions are answered like this (the comments give the results for the
trial above):

```python
import math

def after_trial(self):
    # Did an event happen? Its key exists: use .get with an empty list by default.
    entries = self.trial_data.get("area1_entered", [])
    entered = len(entries) > 0  # True

    # How long did something take? Subtract two times.
    start = self.trial_data["TRIAL_START"]
    latency = entries[0] - start if entered else math.nan  # 8.11 s

    # Was a state visited? If not, its key is missing: use a nan default.
    t_reward = self.trial_data.get("STATE_reward_START", [math.nan])[0]
    rewarded = not math.isnan(t_reward)  # False (this task has no states)

    # Touches: one key per position, all starting with "touch_".
    n_touches = sum(
        len(times) for key, times in self.trial_data.items() if key.startswith("touch_")
    )  # 0

    self.register_value("latency", latency)
    self.register_value("water", 0)
```

#### What is saved

At the end of each trial, `trial_data` (with the values registered in `after_trial`)
becomes one row of the session table. When the session ends, two files are saved:

- **`<session>.csv`**: one row per trial, with a column for each key above and each
  registered value. It is the file used for the analysis and by the training protocol
  (`self.df`). A trial only gets its row when it finishes, so the trial that was
  running when the session stopped is not in it.
- **`<session>_RAW.csv`**: one line per event, written as they happen, including the
  trial that was interrupted.

The session is saved if at least one trial was completed. Design the task so that
trials end after a reasonable time even if the animal does nothing (with a timeout,
as in the examples): a session that is a single trial that never ends would not be
saved.

---

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

Tasks Examples <../examples/tasks_raspberry.md>
../examples/raspberry_area1_sound.md
../examples/raspberry_touchscreen.md
```
