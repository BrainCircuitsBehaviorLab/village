## arduino_4_center_initiated.py

Arduino version of [bpod_4_center_initiated.py](bpod_4_center_initiated.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_4_center_initiated.py <files/arduino_4_center_initiated.py>`

```{literalinclude} files/arduino_4_center_initiated.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_CENTER_INITIATED` command, and
the trial runs in `runCenterInitiated()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Center initiated ("
:end-before: "// === Introduce penalty ("
```
