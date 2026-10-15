## Water Calibration with Arduino

The [Water Calibration](../calibrations/water.md) panel opens the valves through a
built-in Bpod sequence. With an Arduino (`BEHAVIOR_CONTROLLER` set to `OTHER`), the
project needs a task that inherits from `WaterCalibrationTaskBase` and runs the same
sequence on the board. This page gives one, ready to use: the task and its firmware.

---

### How It Works

When you click `CALIBRATE` or `TEST`, the panel creates the task with three arguments
(so its `__init__` must not change):

- `indices`: the ports to open, 0-based (`0` is port 1).
- `times`: the opening time of each one, in seconds, in the same order.
- `maximum_number_of_trials`: the number of iterations.

Every trial opens each valve for its time, one after the other, with 0.1 s in between,
as the Bpod sequence does. The Arduino times each opening itself, in microseconds, so
the USB latency does not change the volume delivered.

### Installing It

1. Download both files below. Copy `water_calibration_arduino.py` to your project's
   `code` directory.
2. In `water_calibration_arduino.ino`, set `valvePins` to the pins of your valves, and
   upload it to the board.
3. Check that `CONTROLLER_PORT` (`SETTINGS` → `CONTROLLER SETTINGS`) is the board's port,
   and that the baud rate is the same in both files (9600).
4. Restart the Training Village, so that it finds the new class.

```{warning}
Keep only one `WaterCalibrationTaskBase` subclass in a project. It is used even if the
controller is Bpod, instead of the built-in sequence, so do not copy it to a Bpod
project. That is also why this example is not part of the demo project.
```

```{note}
The firmware below only opens valves, so you would have to upload it to calibrate and
upload the task firmware back afterwards. If your task firmware already listens for
commands, add `CMD_OPEN_VALVE` to it instead: the same sketch then serves for the tasks
and for the calibration.
```

---

### The Task

{download}`Download water_calibration_arduino.py <../examples/extra/water_calibration_arduino.py>`

```{literalinclude} ../examples/extra/water_calibration_arduino.py
:language: python
```

### The Firmware

{download}`Download water_calibration_arduino.ino <../examples/extra/water_calibration_arduino.ino>`

```{literalinclude} ../examples/extra/water_calibration_arduino.ino
:language: cpp
```
