## arduino_6_delay.py

Arduino version of [bpod_6_delay.py](bpod_6_delay.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_6_delay.py <files/arduino_6_delay.py>`

```{literalinclude} files/arduino_6_delay.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_DELAY` command, and
the trial runs in `runDelay()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Delay ("
:end-before: "// === Water calibration ("
```
