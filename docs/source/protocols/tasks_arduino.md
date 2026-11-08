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
say to each other is up to you: the examples use small binary messages.

### How a task runs

1. `start()` is called once, when the session starts, before the first trial.
   Open the serial connection and compute what the whole session needs: valve
   times, sounds...
2. Then, trial after trial:
   - `create_trial()` **is** the trial: it tells the Arduino to start, registers the
     start of the trial, listens to the Arduino and registers everything it
     reports, and returns when the trial is over. Then `self.trial_data` is filled
     with everything registered in the trial;
   - `after_trial()` is called after every trial. It reads `self.trial_data` and saves
     values with `register_value`. Registering `water` is mandatory.
3. `close()` is called once, when the session ends (session finished, stopped, or
   error), after the last trial. Close the serial connection here.

The session ends when it reaches `maximum_duration` (set in the training protocol),
when the STOP button is pressed, or when your task sets `self.force_stop = True`. The
system checks these conditions continuously, not only between trials: if one is met
during a trial, the session ends at once and that trial is cut (it is not saved in the
session file, only in the RAW file). In Manual mode the session also ends after the
number of trials chosen when launching the task.

`````{admonition} Check should_stop in your waiting loops
:class: warning
When the session ends, the system waits up to 5 seconds for `create_trial` to return
before saving, but it cannot stop your Python code: a `create_trial` waiting for the
Arduino would keep running. Every waiting loop must check `self.should_stop` (and a
deadline, in case a message is lost on the way), so it can never wait forever:

```python
while not self.should_stop and time_utils.now_timestamp() < deadline:
    ...  # read from the Arduino
```
`````

Unlike with Bpod, the Python code is not blocked while the Arduino runs the trial: it
is the loop of `create_trial`, so it can react in the middle of the trial to what the
Arduino reports (playing a sound, as in [Playing a sound](#playing-a-sound)), or to
what only the Raspberry Pi sees (the camera, the touchscreen...) by sending a message
to the Arduino.

All the methods and attributes a task can use are in
[Task Reference](tasks_reference.md).

```{admonition} Register water in every trial
:class: warning
Call `self.register_value("water", ...)` in every `after_trial`, with the microliters
delivered in the trial (`0` if none). The system adds them up to know how much each
subject drinks, and raises an alarm if it is too little.
```

---

### A first task: habituation

This is the first task of the example project, the Arduino version of
[Tasks (Bpod)](tasks_bpod.md#a-first-task-habituation): the animal is left alone in
the box to explore it. Nothing happens and no water is given, but every poke is
recorded. Each trial waits up to 60 seconds and ends earlier if the animal pokes any
port.

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

The habituation trial: it reports the state it enters, waits for a poke in any port
for `durationS` seconds, and reports the result (the port poked, or `0`), with its own
clock (`millis()`):

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

A firmware of your own can follow the same pattern: add a command, a function that
runs the trial, and the same 6-byte messages.

#### The task

```python
import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Protocol (see runHabituation() in village_arduino/village_arduino.ino):
#
# Pi -> Arduino, 3 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, duration_s (uint16, little-endian)]
#   Tells the Arduino how long this trial lasts. From here the Arduino
#   watches the 3 poke sensors on its own; the Pi just listens.
#
# Arduino -> Pi, 6 raw bytes per message:
#   [EVENT_STATE, state, elapsed_ms (uint32, LE)]
#     -- every time the Arduino enters a new state (see STATE_NAMES), so it
#        can be registered with register_enter_state, as Bpod does.
#   [EVENT_TRIAL_END, port (0 if nobody poked), elapsed_ms (uint32, LE)]
#     -- once, when the trial is over.
#   elapsed_ms is milliseconds since the Arduino received CMD_START_TRIAL
#   for THIS trial (its own timer, reset every trial). It is the controller
#   clock: the trial start is registered as controller time 0 at the moment
#   the Pi sent CMD_START_TRIAL, and every elapsed_ms as a controller
#   timestamp (register_controller_event / register_enter_state), so the two
#   clocks never need to be synchronized.
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
        ----------------------------------------------------------
        Lets a mouse get used to being in the box on its own. Every trial,
        the Pi tells the Arduino how long to wait (STATE_DURATION), and the
        Arduino watches all 3 ports for that whole window, ending the trial
        early the moment any one of them is poked. No reward is delivered --
        pokes are only recorded, to see the animal is exploring the box.
        """

    def start(self):
        """Opens the serial connection to the Arduino."""

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        self.serial_port.reset_input_buffer()

    def create_trial(self):
        """Tells the Arduino how long this trial should last, then waits for
        its single reply: either a port number (whichever was poked first)
        or 0 if the whole duration passed with no poke at all.

        The deadline below is only a safety net for a lost/garbled message
        -- in normal operation the Arduino's own reply always arrives well
        before it.
        """

        self.serial_port.write(struct.pack("<BH", CMD_START_TRIAL, STATE_DURATION))
        t_sent = time_utils.now_timestamp()
        # The Arduino's clock (elapsed_ms) starts at 0 when it gets the command.
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

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
        """Reads back whichever port event create_trial registered, if any,
        to label the trial."""

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
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
```

Step by step:

- **The constants** at the top are the protocol: the command byte of the habituation
  trial, the event codes the Arduino sends, and `STATE_NAMES`, which translates the
  number of each state into the name it gets in the trial data.
- **The class name**, `Arduino1Habituation`, is the name of the task.
- **`__init__`** only sets `self.info`, the description shown when the task is
  selected in the GUI. Always call `super().__init__()` first.
- **`start`** opens the serial port and discards anything left in it.
- **`create_trial`** runs the whole trial:
  1. It sends the command, `[11, 60]`: run a habituation trial of 60 seconds.
  2. It registers the start of the trial with **both clocks** at the same moment:
     the Raspberry Pi's time (`t_sent`) and the Arduino's (`0`, since the Arduino
     starts counting when it receives the command). From then on, every time the
     Arduino reports is converted to Raspberry Pi time, so the two clocks never need
     to be synchronized.
  3. It reads the messages of the Arduino, 6 bytes each, and registers what they
     report with the Arduino's time: the state entered with `register_enter_state`,
     the port poked with `register_controller_event` (as `Port1In`, `Port2In` or
     `Port3In`, the same names as Bpod), and the end of the trial with
     `register_end_trial`.
  4. The loop also ends if the task has to stop or the deadline passes. Then the
     trial is ended automatically when `create_trial` returns.

  When the trial ends, the next one starts right away with a new call to
  `create_trial`, until the session ends.
- **`after_trial`** reads `self.trial_data` to find out how the trial ended: if there
  is a `Port1In`, `Port2In` or `Port3In` event, the animal poked that port; if not,
  the time ran out (`"miss"`). It saves the result with
  `self.register_value("outcome", outcome)`, and the water given, `0`, with
  `self.register_value("water", 0)`.
- **`close`** closes the serial port.

The complete code of this task and the rest of the example project, from habituation
to a full discrimination task, are in
[Task Examples (Arduino)](../examples/tasks_arduino.md), together with the firmware.

---

### Trial data

When a trial ends, everything registered in it is put in `self.trial_data`, a
dictionary that `after_trial` reads to decide the outcome of the trial. For example,
a trial of the habituation task in which the animal pokes the center port after
12.3 seconds:

```python
{
    "date": "2026-11-07 10:30:00",
    "trial": 5,
    "subject": "mouse1",
    "task": "Arduino1Habituation",
    "system_name": "village01",
    "TRIAL_START": 1793961045.20,
    "TRIAL_END": 1793961057.50,
    "STATE_ready_to_explore_START": [1793961045.20],
    "STATE_ready_to_explore_END": [1793961057.50],
    "Port2In": [1793961057.50],
    "ordered_list_of_events": ["Port2In"],
}
```

If the animal does not poke, there is no `Port2In` key: the trial just ends after
60 seconds.

The keys are:

| Key | Value |
| :--- | :--- |
| `"date"`, `"trial"`, `"subject"`, `"task"`, `"system_name"` | Which session and trial it is. |
| `"TRIAL_START"`, `"TRIAL_END"` | When the trial started (`register_start_trial`) and ended (`register_end_trial`, or the moment `create_trial` returned). |
| `"STATE_<name>_START"`, `"STATE_<name>_END"` | For every state registered with `register_enter_state`, a list with the times it was entered and left (a list, because a state can be visited several times). A state ends when the next one is entered, or when the trial ends. A state that was **not visited** is not in the dictionary. |
| `"<event>"` (`"Port1In"`...) | For every event registered, a list with the times of each occurrence. Events that did not happen are not in the dictionary. Events registered with `register_raspberry_event` during the trial are included too, and so are the ones the system registers by itself: `sound` when a sound starts playing, `touch_<x>_<y>` for every touch. |
| `"ordered_list_of_events"` | The names of all the events, in the order they happened. |

All the times are in seconds, converted to the Raspberry Pi's clock (UNIX time), so
the Arduino's and the Raspberry Pi's can be compared and subtracted directly.

This is how to get the usual information from it in `after_trial` (the comments
give the results for the trial above):

```python
def after_trial(self):
    # Did an event happen? Its key exists.
    center_poke = "Port2In" in self.trial_data  # True

    # How many times? The length of its list (an empty list if it did not happen).
    number_of_pokes = len(self.trial_data.get("Port2In", []))  # 1

    # When? The first element of its list.
    poke_time = self.trial_data["Port2In"][0]  # 1793961057.50

    # How long did something take? Subtract two times.
    trial_start = self.trial_data["TRIAL_START"]
    reaction_time = poke_time - trial_start  # 12.3 s

    # Was a state visited? Its key exists.
    explored = "STATE_ready_to_explore_START" in self.trial_data  # True
```

#### What is saved

At the end of each trial, `trial_data`, with the values registered in `after_trial`
(`outcome` and `water` in the habituation task), becomes one row of the session
table. When the session ends, two files are saved:

- **`<session>.csv`**: one row per trial, with a column for each key above and each
  registered value. It is the file used for the analysis and by the training
  protocol (`self.df`). A trial only gets its row when it finishes, so the trial
  that was running when the session stopped is not in it.
- **`<session>_RAW.csv`**: one line per event, written as they happen, including
  the trial that was interrupted.

The session is saved if at least one trial was completed. Design the task so that
trials end after a reasonable time even if the animal does nothing (with a timeout in
the firmware and a deadline in `create_trial`, as in the habituation task): a session
that is a single trial that never ends would not be saved.

---

### Delivering water

The valves are connected to the Arduino, and the firmware opens them: the valve time
must be precise, and only the Arduino can time it to the millisecond. The task gets
the valve time that gives a volume from the water calibration of that port, and sends
it to the Arduino in the command of the trial.

In [arduino_2_passive.py](../examples/arduino_2_passive.md), the second task of the
example project, every trial a side port lights up and gives water at once; then the
LED stays on until the animal pokes that port, or a timeout. The parts that deliver the
water are:

**In the task**, `start` computes the valve times once, for the whole session:

```python
    def start(self):
        ...  # open the serial port, as in the habituation task
        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )
```

and `create_trial` chooses the port and sends the command, with the valve time in
milliseconds:

```python
    def create_trial(self):
        self.side = random.choice(["left", "right"])
        if self.side == "left":
            valvetime, port = self.valve_l_time, 1
        else:
            valvetime, port = self.valve_r_time, 3

        valve_time_ms = int(valvetime * 1000)
        led_on_timeout_ms = int(self.settings.led_on_time * 1000)
        self.serial_port.write(
            struct.pack(
                "<BBHH", CMD_START_TRIAL, port, valve_time_ms, led_on_timeout_ms
            )
        )
        ...  # register the start and listen to the Arduino, as in the habituation task
```

**In the firmware**, `runPassive` turns the LED on and opens the valve for
`valveTimeMs` milliseconds, reporting the state it enters:

```cpp
void deliverWater(byte port, unsigned int valveTimeMs) {
  byte valvePin = valvePinOf(port);
  digitalWrite(valvePin, HIGH);
  delay(valveTimeMs);
  digitalWrite(valvePin, LOW);
}

void runPassive(byte port, unsigned int valveTimeMs, unsigned int ledOnTimeoutMs) {
  unsigned long t0 = millis();
  byte ledPin = ledPinOf(port);

  sendEvent(EVENT_STATE, PASSIVE_WATER_DELIVERY, 0);
  digitalWrite(ledPin, HIGH);
  deliverWater(port, valveTimeMs);

  sendEvent(EVENT_STATE, PASSIVE_LED_ON, millis() - t0);
  ...  // wait for the poke, then send EVENT_TRIAL_END
}
```

**In `after_trial`**, the water is registered. In this task it is given in every
trial:

```python
        self.register_value("water", self.settings.reward_volume)
```

In a task where the water depends on the response, register `reward_volume` only if
the reward state was visited: `"STATE_reward_START" in self.trial_data`.

- `reward_volume` is a setting defined in the training protocol. The water
  calibration must exist for the port, or `get_valve_time` raises an error. With an
  Arduino, the calibration needs a calibration task of its own: see
  [Water Calibration with Arduino](../advanced_customization/water_calibration_arduino.md).
- The firmware already has a command that only opens a valve, `CMD_OPEN_VALVE`
  (`[20, port, time_us (uint32)]`), the one the water calibration uses. A task can
  send it to give water at any moment, e.g. when the camera trigger detects the
  animal in an area. The firmware replies with `EVENT_VALVE_CLOSED`, when the valve
  closes.

---

### Playing a sound

The sound card is connected to the Raspberry Pi, not to the Arduino. So the sound is
loaded by the task, before the trial starts, and played by the task when the Arduino
reports what has to trigger it. This uses a file of your project's `code` directory,
written by you (the example project already includes it): **`sound_functions.py`**,
with functions that generate sounds as NumPy arrays, such as `tone_generator` or
`whitenoise_generator`. See [Sound Functions](../devices/sound.md#sound-functions).
The sound is loaded with `sound_device.load` and played with `sound_device.play` (see
[Using It in Tasks](../devices/sound.md#using-it-in-tasks)).

In this example, every trial a tone of a random frequency (5 or 10 kHz) is loaded,
and it is played when the animal pokes the center port. It uses the habituation trial
of the firmware, which ends at the first poke:

```python
import random
import struct
import time

import serial
from sound_functions import tone_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils
from village.settings import settings

CMD_HABITUATION = 11
EVENT_TRIAL_END = 2
MESSAGE_SIZE = 6
TRIAL_DURATION = 60  # seconds


class PokeForSound(TaskBase):
    def start(self):
        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"), baudrate=9600, timeout=0.05
        )
        self.serial_port.reset_input_buffer()

    def create_trial(self):
        # load this trial's sound before the trial starts
        self.frequency = random.choice([5000, 10000])
        sound = tone_generator(duration=0.5, gain=0.05, frequency=self.frequency)
        sound_device.load(left=sound, right=sound)

        self.serial_port.write(struct.pack("<BH", CMD_HABITUATION, TRIAL_DURATION))
        t_sent = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        deadline = t_sent + TRIAL_DURATION + 2.0
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            buffer += self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if len(buffer) < MESSAGE_SIZE:
                continue
            event, port, elapsed_ms = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            if event == EVENT_TRIAL_END:  # the state messages are not used here
                t = elapsed_ms / 1000.0
                if port != 0:
                    self.register_controller_event(f"Port{port}In", t)
                if port == 2:  # the center port: play the sound
                    sound_device.play()
                    time.sleep(0.5)  # the trial ends when the sound ends
                    t += 0.5
                self.register_end_trial(t)
                break

    def after_trial(self):
        self.register_value("frequency", self.frequency)
        self.register_value("water", 0)

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()
```

- `create_trial` loads the sound before sending the command, so it is ready when it is
  needed. Loading takes longer the longer the sound is; playing a loaded sound starts
  at once.
- The sound starts a few milliseconds after the poke: the time the message takes to
  reach the Raspberry Pi, plus the time to start the sound (see
  [Timing, Clocks & Latencies](../system_operation/timing.md)).
- `self.frequency` is an attribute of the task, so `after_trial` can register it.
- `gain=0.05` is an arbitrary volume. To play the sound at a given level in dB, use
  the sound calibration (see [Sound](../devices/sound.md)).
- When the sound starts playing, the system adds a `sound` event to `trial_data`.

The task can also play the sound with a direct function (`self.execute_function(4)`,
"Play Loaded Sound" in the example project), as
[arduino_5_introduce_penalty.py](../examples/arduino_5_introduce_penalty.md) does.
Direct functions can also be run from the GUI or from the triggers: see
[Direct Functions](functions.md).

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
