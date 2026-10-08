## arduino_3_active.py

Arduino version of [bpod_3_active.py](bpod_3_active.md): the same task and states (see its diagram), run by an Arduino that reports every state and poke to the Raspberry Pi. The ITI and the penalty, if any, are timed by the Raspberry Pi.

### Task

{download}`Download arduino_3_active.py <files/arduino_3_active.py>`

```{literalinclude} files/arduino_3_active.py
:language: python
```

### Arduino firmware

{download}`Download arduino_3_active.ino <files/arduino_firmware/arduino_3_active.ino>`

```{literalinclude} files/arduino_firmware/arduino_3_active.ino
:language: cpp
```
