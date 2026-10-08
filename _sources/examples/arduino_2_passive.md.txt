## arduino_2_passive.py

Arduino version of [bpod_2_passive.py](bpod_2_passive.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_2_passive.py <files/arduino_2_passive.py>`

```{literalinclude} files/arduino_2_passive.py
:language: python
```

### Arduino firmware

{download}`Download arduino_2_passive.ino <files/arduino_firmware/arduino_2_passive.ino>`

```{literalinclude} files/arduino_firmware/arduino_2_passive.ino
:language: cpp
```
