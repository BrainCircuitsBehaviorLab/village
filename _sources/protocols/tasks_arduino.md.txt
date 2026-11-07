## Tasks (Arduino)

With `BEHAVIOR_CONTROLLER` set to `OTHER` in `SETTINGS`, a microcontroller (an
Arduino, or any other board that talks over a serial port) can run the time-critical
part of every trial: reading the pokes, turning the LEDs on, opening the valves. The
task, on the Raspberry Pi, tells it what to do at the start of every trial and
registers everything it reports. So there are two pieces of code:

- **The task** (`.py`): a class that inherits from `TaskBase`, in any `.py` file
  inside your project's `code` directory. The name of the class is the name of the
  task: the one shown in the GUI and used in `next_task` by the training protocol.
  The file name does not matter.
- **The firmware** (`.ino` for an Arduino), uploaded to the board with its own tools
  (e.g. the Arduino IDE). Village doesn't upload it.

They talk through the serial port set in `CONTROLLER_PORT` (`SETTINGS`). What they
say to each other is up to you: the examples use small binary messages, described at
the top of each file.

### How a task runs

1. `start()` is called once, when the session starts. It usually opens the serial
   connection.
2. Then, trial after trial:
   - `create_trial()` **is** the trial: it tells the Arduino to start, registers the
     start of the trial, listens to the Arduino and registers everything it reports,
     and returns when the trial is over;
   - `self.trial_data` is filled with everything registered in the trial;
   - `after_trial()` reads it and registers the values to save, at least `water`.
3. `close()` is called once, when the session ends. It usually closes the serial
   connection.

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
waiting for the Arduino would keep running. Every waiting loop must check
`self.should_stop` (and a deadline, in case a message is lost on the way), so it can
never wait forever:

```python
while not self.should_stop and time_utils.now_timestamp() < deadline:
    ...  # read from the Arduino
```
`````

**Two clocks.** The Arduino times what it detects with its own clock, and the
Raspberry Pi with its own. `register_start_trial` receives both at the same moment,
and from then on every time the Arduino reports is converted to Raspberry Pi time, so
the clocks never need to be synchronized. In the examples the Arduino counts the
milliseconds since it received the command, so at the start of the trial its clock is
`0`.

Unlike with Bpod, the Python code is not blocked while the Arduino runs the trial: it
is the loop of `create_trial`, so it can react in the middle of the trial to what the
Arduino reports (playing a sound, for example), or to what only the Raspberry Pi sees
(the camera, the touchscreen...) by sending a message to the Arduino. Both are shown in
the [examples](#examples).

---

### Reference

#### The four methods you write

| Method | Called | Use it to |
| :--- | :--- | :--- |
| `start(self)` | Once, before the first trial. | Open the serial connection, compute what the whole session needs: valve times, sounds... |
| `create_trial(self)` | Every trial. | Run the trial: send the command to the Arduino, call `register_start_trial`, and register everything it reports until the trial is over. |
| `after_trial(self)` | After every trial. | Read `self.trial_data`, decide the outcome, and save values with `register_value`. Registering `water` is mandatory. |
| `close(self)` | Once, after the last trial (session finished, stopped, or error). | Close the serial connection. |

```{admonition} Register water in every trial
:class: warning
Call `self.register_value("water", ...)` in every `after_trial`, with the microliters
delivered in the trial (`0` if none). The system adds them up to know how much each
subject drinks, and raises an alarm if it is too little.
```

#### Methods you can call

| Method | Use |
| :--- | :--- |
| `self.register_start_trial(raspberry_timestamp, controller_timestamp)` | **Required** at the start of every trial, in `create_trial`: without it the task stops with an error. Pass `time_utils.now_timestamp()` and the Arduino's time at the same moment. |
| `self.register_end_trial(controller_timestamp)` | Ends the trial, with the Arduino's time. Optional: if `create_trial` returns without calling it, the trial is ended at that moment. |
| `self.register_enter_state(state_name, controller_timestamp)` | The Arduino entered a state: closes the previous one and opens this one, as Bpod does. |
| `self.register_controller_event(name, controller_timestamp)` | An event detected and timed by the Arduino (e.g. `"Port1In"`). |
| `self.register_raspberry_event(name, timestamp)` | An event detected by the Raspberry Pi (a camera detection, a touch...) with `time_utils.now_timestamp()` as timestamp. |
| `self.register_value(name, value)` | Saves a value in the trial's row of the session file (a column named `name`). Call it in `after_trial`. |
| `self.execute_function(i)` | Runs direct function `i` (1-98), see [Direct Functions](functions.md). |

The `register_*` methods only record what happens between `register_start_trial` and
the end of the trial: anything registered outside that window is ignored.

#### Attributes you can use

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `self.settings` | `Settings` | The subject's training settings, defined in the [training protocol](creating.md) (e.g. `self.settings.reward_volume`). Changes made during the session are kept for the next one. |
| `self.calibrations` | `Calibrations` | Calibrations, e.g. `self.calibrations.water_calibration.get_valve_time(port, volume)` (the time to send to the Arduino) or `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`. |
| `self.trial_data` | `dict` | Everything registered in the trial, available in `after_trial` (see [Trial data](#trial-data)). |
| `self.info` | `str` | Description of the task, shown when it is selected in the GUI. Set it in `__init__`. |
| `self.name` | `str` | The name of the task, which is the name of its class (e.g. `"Arduino1Habituation"`). |
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

You can also add your own attributes (`self.serial_port`, `self.side = "left"`...):
they are kept from one method to the next, and the triggers and direct functions can
read them through `self.task`.

#### The firmware

All the Arduino examples share one firmware,
[village_arduino.ino](../examples/village_arduino.md), uploaded once to the board.
Ports 1 (left), 2 (center) and 3 (right) are wired; only the side ports have a valve.
The messages are:

- **Raspberry Pi → Arduino**: one command per trial. Its first byte says which task
  it is for (`CMD_HABITUATION = 11`, `CMD_PASSIVE = 12`...), and the rest are the
  values that task needs (ports, times in milliseconds...).
- **Arduino → Raspberry Pi**: messages of 6 bytes, `[event, value, elapsed_ms]`:
  `EVENT_POKE` (the port poked), `EVENT_STATE` (the state entered) and
  `EVENT_TRIAL_END` (the result of the trial). `elapsed_ms` is the Arduino's clock:
  the milliseconds since it received the command.

The firmware's `loop()` reads the command byte, waits for the rest of the message (its
size depends on the command) and runs that task's trial:

```cpp
// Reads the command byte first, waits until the whole message has arrived
// (its size depends on the command), and runs the trial it asks for.
void loop() {
  if (Serial.available() < 1) {
    return;
  }
  byte command = Serial.peek();
  byte size = messageSize(command);
  if (size == 0) {
    Serial.read();  // unknown command: drop it
    return;
  }
  if (Serial.available() < size) {
    return;  // the rest of the message has not arrived yet
  }
  Serial.read();  // the command byte

  switch (command) {
    case CMD_HABITUATION: {
      unsigned int durationS = readUInt16();
      runHabituation(durationS);
      break;
    }
    // ... one case per task
  }
}
```

A firmware of your own can follow the same pattern: add a command, a function that
runs the trial, and the same 6-byte messages.

---

### Examples

#### A simple task: habituation

[arduino_1_habituation.py](../examples/arduino_1_habituation.md), the Arduino version
of [bpod_1_habituation.py](../examples/bpod_1_habituation.md): the mouse is left alone
in the box and the pokes are recorded, with no reward. Every trial lasts up to 60
seconds and ends at the first poke.

The firmware's part: it waits for a poke in any port for `durationS` seconds, and
reports the state it enters and the result, with its own clock (`millis()`):

```cpp
// [CMD_HABITUATION, duration_s (uint16, LE)]
const byte HABITUATION_READY_TO_EXPLORE = 1;

void runHabituation(unsigned int durationS) {
  unsigned long t0 = millis();
  unsigned long durationMs = (unsigned long)durationS * 1000UL;
  sendEvent(EVENT_STATE, HABITUATION_READY_TO_EXPLORE, 0);

  byte pokedPort = 0;
  while (millis() - t0 < durationMs) {
    pokedPort = readAnyPoke();
    if (pokedPort != 0) {
      break;
    }
  }

  sendEvent(EVENT_TRIAL_END, pokedPort, millis() - t0);
}
```

The task:

```python
import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

CMD_START_TRIAL = 11  # CMD_HABITUATION in village_arduino.ino
EVENT_TRIAL_END = 2
EVENT_STATE = 3

# State ids sent by the Arduino (same names as bpod_1_habituation.py)
STATE_NAMES = {1: "ready_to_explore"}

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop gets re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes
STATE_DURATION = 60  # seconds


class Arduino1Habituation(TaskBase):
    def __init__(self):
        super().__init__()
        self.info = """
        Habituation Task
        ----------------
        The mouse is left alone in the box; pokes are recorded, no reward.
        """

    def start(self):
        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        self.serial_port.reset_input_buffer()

    def create_trial(self):
        # 1. Tell the Arduino to start the trial, and register the start in both
        # clocks: the Arduino's starts at 0 when it gets the command.
        self.serial_port.write(struct.pack("<BH", CMD_START_TRIAL, STATE_DURATION))
        t_sent = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        # 2. Listen to the Arduino until the trial is over, the task has to stop,
        # or the deadline passes (a lost message).
        deadline = t_sent + STATE_DURATION + 2.0  # margin for serial/USB latency
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                continue  # nothing arrived within READ_TIMEOUT; keep waiting
            buffer += chunk
            if len(buffer) < MESSAGE_SIZE:
                continue

            event, value, elapsed_ms = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            t = elapsed_ms / 1000.0  # controller clock, seconds

            # 3. Register what it reports, with the Arduino's time.
            if event == EVENT_STATE:
                self.register_enter_state(STATE_NAMES.get(value, f"state{value}"), t)
            elif event == EVENT_TRIAL_END:
                if value != 0:  # the port that was poked
                    self.register_controller_event(f"Port{value}In", t)
                self.register_end_trial(t)
                break
        # If the loop ended without EVENT_TRIAL_END (task stopped, or a lost
        # message), the trial is ended automatically when this returns.

    def after_trial(self):
        outcome = "miss"
        if self.trial_data.get("Port1In"):
            outcome = "left_poke"
        elif self.trial_data.get("Port2In"):
            outcome = "center_poke"
        elif self.trial_data.get("Port3In"):
            outcome = "right_poke"

        self.register_value("outcome", outcome)
        self.register_value("water", 0)

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()
```

The rest of the examples (`arduino_2` to `arduino_6`) follow the same pattern: the
command carries more values (the correct port, the timings, the valve time), and the
firmware reports more states and pokes.

#### Playing a sound

The sound card is on the Raspberry Pi, so the Arduino reports what happened and the
task plays the sound. In
[arduino_5_introduce_penalty.py](../examples/arduino_5_introduce_penalty.md), a wrong
poke is punished with a noise: the sound is loaded before the trial (direct function 2,
"Load Noise Sound") and, if the Arduino reports an incorrect outcome, the task plays it
(direct function 4, "Play Loaded Sound") and registers the penalty states itself, with
the Arduino's clock:

```python
    def create_trial(self):
        ...
        self.execute_function(2)  # load the noise now, before it is needed
        ...  # send the command and listen to the Arduino, as in the first example
        if t_end is None:
            return  # stopped or lost message: the trial is ended automatically

        if self.outcome == "incorrect":
            self.register_enter_state("wrong_choice", t_end)
            self.execute_function(4)  # play the sound loaded above
            t_end += self.wait(self.settings.noise_time)
            if not self.should_stop:
                self.register_enter_state("timeout", t_end)
                t_end += self.wait(self.settings.timeout - self.settings.noise_time)
        self.register_end_trial(t_end)
```

`self.wait` is a method of the task that waits the given seconds (less if the task has
to stop) and returns the time actually waited. The moment the sound starts is recorded
automatically as the event `sound`.

#### Reacting to the camera

The camera is on the Raspberry Pi: the camera trigger signals the task, and the task
sends a command to the Arduino. In this example the animal gets water in port 1 when it
enters box area 1 (set as a TRIGGER area, with `CAM_BOX_TRACKING_POSITION` ON). The
Arduino only opens the valve, with the firmware's `CMD_OPEN_VALVE` command (the one the
water calibration uses), so the whole trial is timed by the Raspberry Pi: the same time
is passed as both clocks.

In `camera_trigger.py`, which runs on every camera frame:

```python
from village.custom_classes.camera_trigger_base import CameraTriggerBase
from village.devices.camera import Camera
from village.scripts.time_utils import time_utils


class CameraTrigger(CameraTriggerBase):
    def trigger(self, cam: Camera) -> None:
        if cam.name != "BOX":
            return
        area1_event = getattr(self.task, "area1_event", None)  # only in this task
        if cam.area1_is_triggered and area1_event and not area1_event.is_set():
            self.task.register_raspberry_event("area1_entered", time_utils.now_timestamp())
            area1_event.set()
```

In the task:

```python
import struct
import threading
import time

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

CMD_OPEN_VALVE = 20  # [CMD_OPEN_VALVE, port, time_us (uint32)] in village_arduino.ino


class Area1Water(TaskBase):
    def start(self):
        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"), baudrate=9600, timeout=0.05
        )
        self.valve_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.area1_event = threading.Event()  # set by camera_trigger.py

    def create_trial(self):
        self.area1_event.clear()
        self.rewarded = False
        # this task does not read the Arduino's replies (EVENT_VALVE_CLOSED)
        self.serial_port.reset_input_buffer()

        # the whole trial is timed by the Raspberry Pi: the same time as both clocks
        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)
        self.register_enter_state("wait_area1", t0)

        deadline = t0 + 60
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            if self.area1_event.wait(timeout=0.05):
                self.register_enter_state("reward", time_utils.now_timestamp())
                time_us = int(self.valve_time * 1_000_000)
                self.serial_port.write(struct.pack("<BBI", CMD_OPEN_VALVE, 1, time_us))
                time.sleep(self.valve_time)  # the Arduino times the valve itself
                self.rewarded = True
                break

        self.register_end_trial(time_utils.now_timestamp())

    def after_trial(self):
        self.register_value("water", self.settings.reward_volume if self.rewarded else 0)

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()
```

The touchscreen works the same way: in `touch_trigger.py`, `trigger(self, x, y,
timestamp)` is called on every touch, and it signals the task when the touch is inside
a target. See [Screen & Touchscreen](../devices/screen.md#reacting-to-touches).

#### Complete examples

The Arduino versions of the six stages of the example project, from habituation to a
full discrimination task, are in [Task Examples (Arduino)](../examples/tasks_arduino.md),
together with the firmware.

---

### Trial data

When a trial ends, everything registered in it is put in `self.trial_data`, a
dictionary that `after_trial` reads to decide the outcome of the trial. Its keys:

| Key | Value |
| :--- | :--- |
| `"date"`, `"trial"`, `"subject"`, `"task"`, `"system_name"` | Which session and trial it is. |
| `"TRIAL_START"`, `"TRIAL_END"` | When the trial started (`register_start_trial`) and ended (`register_end_trial`, or the moment `create_trial` returned). |
| `"STATE_<name>_START"`, `"STATE_<name>_END"` | For every state registered with `register_enter_state`, a list with the times it was entered and left (a list, because a state can be visited several times). A state ends when the next one is entered, or when the trial ends. A state that was **not visited** is not in the dictionary. |
| `"<event>"` (`"Port1In"`...) | For every event registered, a list with the times of each occurrence. Events that did not happen are not in the dictionary. The ones the system registers by itself are included too: `sound` when a sound starts playing, `touch_<x>_<y>` for every touch. |
| `"ordered_list_of_events"` | The names of all the events, in the order they happened. |

All the times are in seconds, converted to the Raspberry Pi's clock (UNIX time), so
the Arduino's and the Raspberry Pi's can be compared and subtracted directly.

For example, a trial of the habituation task in which the animal pokes the center port
after 3.25 seconds:

```python
{
    "date": "2026-11-07 10:30:00",
    "trial": 12,
    "subject": "mouse1",
    "task": "Arduino1Habituation",
    "system_name": "village01",
    "TRIAL_START": 1793961045.20,
    "TRIAL_END": 1793961048.45,
    "STATE_ready_to_explore_START": [1793961045.20],
    "STATE_ready_to_explore_END": [1793961048.45],
    "Port2In": [1793961048.45],
    "ordered_list_of_events": ["Port2In"],
}
```

The usual questions are answered like this (the comments give the results for the
trial above):

```python
import math

def after_trial(self):
    # Was a state visited? If not, its key is missing: use a nan default.
    t_reward = self.trial_data.get("STATE_reward_START", [math.nan])[0]
    rewarded = not math.isnan(t_reward)  # False

    # Did an event happen? Its key exists: use .get with an empty list by default.
    center_pokes = self.trial_data.get("Port2In", [])
    poked_center = len(center_pokes) > 0  # True

    # How long did something take? Subtract two times.
    start = self.trial_data["TRIAL_START"]
    response_time = center_pokes[0] - start if poked_center else math.nan  # 3.25 s

    self.register_value("response_time", response_time)
    self.register_value("water", self.settings.reward_volume if rewarded else 0)
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
trials end after a reasonable time even if the animal does nothing (with a timeout in
the firmware and a deadline in `create_trial`, as in the examples): a session that is
a single trial that never ends would not be saved.

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

Tasks Examples <../examples/tasks_arduino.md>
../examples/village_arduino.md
../examples/arduino_1_habituation.md
../examples/arduino_2_passive.md
../examples/arduino_3_active.md
../examples/arduino_4_center_initiated.md
../examples/arduino_5_introduce_penalty.md
../examples/arduino_6_delay.md
```
