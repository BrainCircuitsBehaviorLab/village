## arduino_2_passive.py

Arduino version of [bpod_2_passive.py](bpod_2_passive.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_2_passive.py <files/arduino_2_passive.py>`

```{literalinclude} files/arduino_2_passive.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_PASSIVE` command, and
the trial runs in `runPassive()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Passive ("
:end-before: "// === Active ("
```
