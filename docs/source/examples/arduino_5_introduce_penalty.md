## arduino_5_introduce_penalty.py

Arduino version of [bpod_5_introduce_penalty.py](bpod_5_introduce_penalty.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_5_introduce_penalty.py <files/arduino_5_introduce_penalty.py>`

```{literalinclude} files/arduino_5_introduce_penalty.py
:language: python
```

### Arduino firmware

All the Arduino examples use the same firmware, [village_arduino.ino](village_arduino.md),
uploaded once to the board. This task starts every trial with the `CMD_INTRODUCE_PENALTY` command, and
the trial runs in `runIntroducePenalty()`:

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
:start-at: "// === Introduce penalty ("
:end-before: "// === Delay ("
```
