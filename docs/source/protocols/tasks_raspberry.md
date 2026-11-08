## Tasks (Raspberry Only)

With `BEHAVIOR_CONTROLLER` set to `OTHER` in `SETTINGS` and no microcontroller, the
Raspberry Pi runs the trial itself: it reacts to what it detects (the box camera
areas, the touchscreen, the GPIO input pin, the box scale) and produces the stimuli
(sounds, the screen, the LED strip, the GPIO output pin). Its timing is less precise
than a microcontroller's (see [Timing, Clocks & Latencies](../system_operation/timing.md)):
for fast and precise timing, use Bpod or a microcontroller. And without a controller
there are no valves: these tasks don't give water.

A task is a class that inherits from `TaskBase`, in any `.py` file inside your
project's `code` directory. The name of the class is the name of the task: the one
shown in the GUI and used in `next_task` by the training protocol. The file name does
not matter.

### How a task runs

1. `start()` is called once, when the session starts, before the first trial.
   Compute what the whole session needs: sounds, stimulus positions...
2. Then, trial after trial:
   - `create_trial()` **is** the trial: it registers the start of the trial, waits
     for what has to happen (or a timeout), registers it, and returns when the trial
     is over. Then `self.trial_data` is filled with everything registered in the
     trial;
   - `after_trial()` is called after every trial. It reads `self.trial_data` and saves
     values with `register_value`. Registering `water` is mandatory.
3. `close()` is called once, when the session ends (session finished, stopped, or
   error), after the last trial. It can be used to close files or connections.

The session ends when it reaches `maximum_duration` (set in the training protocol),
when the STOP button is pressed, or when your task sets `self.force_stop = True`. The
system checks these conditions continuously, not only between trials: if one is met
during a trial, the session ends at once and that trial is cut (it is not saved in the
session file, only in the RAW file). In Manual mode the session also ends after the
number of trials chosen when launching the task.

`````{admonition} Check should_stop in your waiting loops
:class: warning
When the session ends, the system waits up to 5 seconds for `create_trial` to return
before saving, but it cannot stop your Python code: a `create_trial` waiting for
something would keep running. Every waiting loop must check `self.should_stop` (and a
timeout), so it can never wait forever:

```python
while not self.should_stop and time_utils.now_timestamp() < deadline:
    ...  # wait for your own condition
```
`````

The detections arrive through the **triggers** (camera, touchscreen, GPIO, scale):
classes in your `code` directory that the system calls, in their own threads, while
the task is running. The usual pattern is: the trigger reacts and signals the task
(with a `threading.Event`), and the loop of `create_trial` waits for that signal, or a
timeout, to end the trial. The first task below works this way.

All the methods and attributes a task can use are in
[Task Reference](tasks_reference.md).

```{admonition} Register water in every trial
:class: warning
Call `self.register_value("water", 0)` in every `after_trial`, even though these tasks
give no water. The system adds up the water of every trial to know how much each
subject drinks, and raises an alarm if it is too little.
```

---

### A first task: entering an area

This task of the example project waits, every trial, for the animal to enter area 1
of the box camera. When it does, a sound plays and an LED of the LED strip turns on.
If the animal does not enter in 60 seconds, the trial ends anyway.

It needs two settings: area 1 of the box camera set as a `TRIGGER` area, and
`CAM_BOX_TRACKING_POSITION` ON (see
[Detection in the Operant Box](../system_operation/detection.md#detection-in-the-operant-box)).

#### The task

```python
import threading

from sound_functions import whitenoise_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils

TRIAL_TIMEOUT = 60  # seconds to wait for the animal to enter area 1


class RaspberryArea1Sound(TaskBase):
    """No Bpod, no Arduino (BEHAVIOR_CONTROLLER = OTHER): area 1 entry is
    reacted to by a custom CameraTriggerBase (camera_trigger.py, in this
    same code directory), which plays the sound and lights an LED strip LED
    the moment the animal enters. create_trial just waits for that to
    happen (or times out), then ends the trial.

    Required setup (in SETTINGS, not in this file):
    - CAM_BOX_TRACKING_POSITION must be ON.
    - BOX area 1 must be set to TRIGGER status (and positioned/sized as
      wanted) in the box area settings.
    Without both, area1_is_triggered never becomes True and every trial
    will just time out.
    """

    def __init__(self):
        super().__init__()

        self.info = f"""
        Area 1 Sound Task
        ----------------------------------------------------------------
        No controller involved -- driven entirely by camera position
        tracking, reacted to in camera_trigger.py. Each trial:
        - If the animal enters BOX area 1, camera_trigger.py plays a sound
          and lights an LED on the strip; the trial ends right after.
        - Otherwise, the trial ends anyway after {TRIAL_TIMEOUT} seconds.

        Requires CAM_BOX_TRACKING_POSITION ON and BOX area 1 set to TRIGGER
        (see SETTINGS).
        """

    def start(self):
        """Loads the sound once -- camera_trigger.py's function4 call
        replays this same loaded sound every time area 1 is entered, no
        reload needed.
        """

        gain_left = self.calibrations.sound_calibration.get_sound_gain(
            speaker=0, dB=70, sound_name="whitenoise"
        )
        gain_right = self.calibrations.sound_calibration.get_sound_gain(
            speaker=1, dB=70, sound_name="whitenoise"
        )
        sound_left = whitenoise_generator(duration=1, gain=gain_left)
        sound_right = whitenoise_generator(duration=1, gain=gain_right)
        sound_device.load(left=sound_left, right=sound_right)

        if not self.cam_box.tracking:
            print(
                "Warning: CAM_BOX_TRACKING_POSITION is OFF -- "
                "area1 will never trigger."
            )
        if not self.cam_box.areas_trigger[0]:
            print(
                "Warning: BOX area 1 is not set to TRIGGER -- "
                "area1 will never trigger."
            )

        # Set by camera_trigger.py's CameraTrigger.trigger() the moment
        # area 1 is entered; create_trial just waits on it.
        self.area1_event = threading.Event()

    def create_trial(self):
        """Waits for camera_trigger.py to react to area 1, or for
        TRIAL_TIMEOUT seconds to pass -- then ends the trial either way."""

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

Step by step:

- **The imports.** `TaskBase` is the class every task inherits from.
  `whitenoise_generator` comes from `sound_functions.py`, a file of the example
  project (see [Playing a sound](#playing-a-sound)), `sound_device` is the sound card,
  and `time_utils` gives the time of the Raspberry Pi.
- **The class name**, `RaspberryArea1Sound`, is the name of the task.
- **`__init__`** only sets `self.info`, the description shown when the task is
  selected in the GUI. Always call `super().__init__()` first.
- **`start`** prepares the session:
  - it loads the sound, a white noise of 1 second at 70 dB from the sound
    calibration, once: it will be played every time the animal enters the area;
  - it warns if the camera is not set up for the task;
  - it creates `self.area1_event`, the signal the camera trigger sets when the
    animal enters area 1.
- **`create_trial`** runs the whole trial:
  1. It clears the signal and registers the start of the trial. Here the Raspberry
     Pi is also the controller, so there is only **one clock**: the same time is
     passed as both clocks.
  2. It waits for the signal, checking every 0.05 seconds whether the task has to
     stop, up to `TRIAL_TIMEOUT` seconds.
  3. It registers the end of the trial.

  When the trial ends, the next one starts right away with a new call to
  `create_trial`, until the session ends.
- **`after_trial`** saves whether the animal entered the area (`entered_area1`), and
  the water given, `0`.
- **`close`** has nothing to clean up.

#### The camera trigger

The animal is detected by the camera trigger, in
[camera_trigger.py](../examples/camera_trigger.md): a class that inherits from
`CameraTriggerBase`, whose `trigger` method is called on every frame of the box
camera while a task is running (see
[Reacting to the Animal's Position](../devices/camera.md#reacting-to-the-animals-position)).
This is the part that reacts to area 1:

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
            led_strip.update_strip(sleep_duration=None)

            area1_event.set()
```

- `cam.area1_is_triggered` is `True` while the animal is in area 1. It stays `True`
  on every frame while the animal is inside, so the trigger only acts if the signal
  is not set yet: once per trial.
- It registers the entry as the event `area1_entered`, plays the sound loaded in
  `start` (direct function 4, see [Playing a sound](#playing-a-sound)), lights the
  first LED of the strip, and sets the signal, which ends the wait of
  `create_trial`.
- `self.task` is the task that is running. `getattr` is used because the trigger is
  called for every task, and only this one has `area1_event`.

The complete code of this task and of
[raspberry_stimulus_menu.py](../examples/raspberry_stimulus_menu.md), which follows the
same pattern with the touchscreen, are in
[Task Examples (Raspberry Only)](../examples/tasks_raspberry.md).

---

### Trial data

When a trial ends, everything registered in it is put in `self.trial_data`, a
dictionary that `after_trial` reads to decide the outcome of the trial. For example,
a trial of the first task in which the animal enters area 1 after 8.11 seconds:

```python
{
    "date": "2026-11-07 10:30:00",
    "trial": 5,
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

If the animal does not enter, there are no `area1_entered` and `sound` keys: the
trial just ends after 60 seconds.

The keys are:

| Key | Value |
| :--- | :--- |
| `"date"`, `"trial"`, `"subject"`, `"task"`, `"system_name"` | Which session and trial it is. |
| `"TRIAL_START"`, `"TRIAL_END"` | When the trial started (`register_start_trial`) and ended (`register_end_trial`, or the moment `create_trial` returned). |
| `"STATE_<name>_START"`, `"STATE_<name>_END"` | For every state registered with `register_enter_state`, a list with the times it was entered and left (a list, because a state can be visited several times). A state ends when the next one is entered, or when the trial ends. A state that was **not visited** is not in the dictionary. The first task has no states. |
| `"<event>"` (`"area1_entered"`...) | For every event registered, a list with the times of each occurrence. Events that did not happen are not in the dictionary. The ones the system registers by itself are included too: `sound` when a sound starts playing, `touch_<x>_<y>` for every touch (e.g. `touch_640_360`), `screen_*` when a stimulus appears on the screen. |
| `"ordered_list_of_events"` | The names of all the events, in the order they happened. |

All the times are in seconds (UNIX time), so they can be compared and subtracted
directly.

This is how to get the usual information from it in `after_trial` (the comments
give the results for the trial above):

```python
def after_trial(self):
    # Did an event happen? Its key exists.
    entered = "area1_entered" in self.trial_data  # True

    # How many times? The length of its list (an empty list if it did not happen).
    number_of_sounds = len(self.trial_data.get("sound", []))  # 1

    # When? The first element of its list.
    entry_time = self.trial_data["area1_entered"][0]  # 1793961053.31

    # How long did something take? Subtract two times.
    trial_start = self.trial_data["TRIAL_START"]
    latency = entry_time - trial_start  # 8.11 s

    # Was a state visited? Its key exists.
    in_iti = "STATE_iti_START" in self.trial_data  # False (this task has no states)

    # Touches: one key per position, all starting with "touch_".
    number_of_touches = sum(
        len(times) for key, times in self.trial_data.items() if key.startswith("touch_")
    )  # 0
```

#### What is saved

At the end of each trial, `trial_data`, with the values registered in `after_trial`
(`entered_area1` and `water` in the first task), becomes one row of the session
table. When the session ends, two files are saved:

- **`<session>.csv`**: one row per trial, with a column for each key above and each
  registered value. It is the file used for the analysis and by the training
  protocol (`self.df`). A trial only gets its row when it finishes, so the trial
  that was running when the session stopped is not in it.
- **`<session>_RAW.csv`**: one line per event, written as they happen, including
  the trial that was interrupted.

The session is saved if at least one trial was completed. Design the task so that
trials end after a reasonable time even if the animal does nothing (with a timeout,
as in the first task): a session that is a single trial that never ends would not be
saved.

---

### Playing a sound

The sound card is connected to the Raspberry Pi, so the task loads the sound and plays
it directly. This uses a file of your project's `code` directory, written by you (the
example project already includes it): **`sound_functions.py`**, with functions that
generate sounds as NumPy arrays, such as `tone_generator` or `whitenoise_generator`.
See [Sound Functions](../devices/sound.md#sound-functions). The sound is loaded with
`sound_device.load` and played with `sound_device.play` (see
[Using It in Tasks](../devices/sound.md#using-it-in-tasks)).

In this example, every trial a tone of a random frequency (5 or 10 kHz) is loaded and
played, followed by the inter-trial interval:

```python
import random
import time

from sound_functions import tone_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils


class SoundEveryTrial(TaskBase):
    def create_trial(self):
        # load this trial's sound before the trial starts
        self.frequency = random.choice([5000, 10000])
        sound = tone_generator(duration=0.5, gain=0.05, frequency=self.frequency)
        sound_device.load(left=sound, right=sound)

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
        self.register_value("frequency", self.frequency)
        self.register_value("water", 0)
```

- `create_trial` loads the sound before registering the start of the trial, so it is
  ready when it is needed. Loading takes longer the longer the sound is; playing a
  loaded sound starts at once.
- `register_enter_state` organizes the trial in states, as Bpod does: the trial data
  gets `STATE_sound_START`, `STATE_iti_START`... A state ends when the next one is
  entered, or when the trial ends.
- `wait` is a method of this task, not of `TaskBase`: it waits in short steps, so the
  task can stop in the middle of a wait.
- `self.frequency` is an attribute of the task, so `after_trial` can register it.
- `gain=0.05` is an arbitrary volume. To play the sound at a given level in dB, use
  the sound calibration, as the first task does (see [Sound](../devices/sound.md)).
- When the sound starts playing, the system adds a `sound` event to `trial_data`.

A trigger can also play a sound, as the camera trigger of the first task does with a
**direct function**: `self.task.execute_function(4)` runs `function4` of
`direct_functions.py`, another file of the example project, which plays the sound
that is loaded:

```python
from village.custom_classes.direct_functions_base import DirectFunctionsBase
from village.devices.sound_device import sound_device


class DirectFunctions(DirectFunctionsBase):
    def function4(self):
        """Play Loaded Sound"""
        sound_device.play()
```

Direct functions are numbered actions, `function1` to `function98`, that you write in
a class that inherits from `DirectFunctionsBase`. They can be run from the task, the
triggers or the GUI, and they can do anything the Raspberry Pi can: draw on the
screen, write on the camera image... See
[Writing Direct Functions](functions.md#writing-direct-functions).

```{toctree}
:hidden:

Tasks Examples <../examples/tasks_raspberry.md>
../examples/raspberry_area1_sound.md
../examples/raspberry_stimulus_menu.md
```
