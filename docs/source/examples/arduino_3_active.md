## arduino_3_active.py

Arduino version of [bpod_3_active.py](bpod_3_active.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_3_active.py <files/arduino_3_active.py>`

```{literalinclude} files/arduino_3_active.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_ACTIVE` command, and
the trial runs in `runActive()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Active ("
:end-before: "// === Center initiated ("
```
