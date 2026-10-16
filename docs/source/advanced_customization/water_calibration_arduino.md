## Water Calibration with Arduino

The [Water Calibration](../calibrations/water.md) panel opens the valves through a
built-in Bpod sequence. With an Arduino (`BEHAVIOR_CONTROLLER` set to `OTHER`), the
project needs a task that inherits from `WaterCalibrationTaskBase` and runs the same
sequence on the board. This page gives one, ready to use, for the firmware of the
Arduino examples, [village_arduino.ino](../examples/village_arduino.md), which already
understands the message it sends.

---

### How It Works

When you click `CALIBRATE` or `TEST`, the panel creates the task with three arguments
(so its `__init__` must not change):

- `indices`: the ports to open, 0-based (`0` is port 1).
- `times`: the opening time of each one, in seconds, in the same order.
- `maximum_number_of_trials`: the number of iterations.

Every trial opens each valve for its time, one after the other, with 0.1 s in between,
as the Bpod sequence does. To open a valve, the task sends a single message,
`CMD_OPEN_VALVE` (the port and the time in microseconds), and waits for the reply,
`EVENT_VALVE_CLOSED`. The Arduino times each opening itself, so the USB latency does not
change the volume delivered.

### Installing It

1. Download `water_calibration_arduino.py` below and copy it to your project's `code`
   directory.
2. Make sure the board runs a firmware that understands `CMD_OPEN_VALVE`: the firmware
   of the Arduino examples does (see below). If you use your own, add the same message
   to it, so that one firmware serves for the tasks and for the calibration.
3. Check that `CONTROLLER_PORT` (`SETTINGS` → `CONTROLLER SETTINGS`) is the board's port,
   and that the baud rate is the same in the task and in the firmware (9600).
4. Restart the Training Village, so that it finds the new class.

---

### The Task

{download}`Download water_calibration_arduino.py <../examples/extra/water_calibration_arduino.py>`

```{literalinclude} ../examples/extra/water_calibration_arduino.py
:language: python
```

### The Firmware

In [village_arduino.ino](../examples/village_arduino.md), the firmware of the Arduino
examples, `CMD_OPEN_VALVE` is handled by `openValve()`. The valve pins are the ones of
the side ports (`valvePinLeft`, `valvePinRight`); a port without a valve replies at once
with an elapsed time of 0:

```{literalinclude} ../examples/files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Water calibration ("
```
