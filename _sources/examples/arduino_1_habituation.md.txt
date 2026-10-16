## arduino_1_habituation.py

Arduino version of [bpod_1_habituation.py](bpod_1_habituation.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi.

### Task

{download}`Download arduino_1_habituation.py <files/arduino_1_habituation.py>`

```{literalinclude} files/arduino_1_habituation.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_HABITUATION` command, and
the trial runs in `runHabituation()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Habituation ("
:end-before: "// === Passive ("
```
