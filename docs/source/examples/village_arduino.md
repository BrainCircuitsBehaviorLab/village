## village_arduino.ino

The firmware for all the Arduino examples: the six `arduino_*` tasks and the
[water calibration](../advanced_customization/water_calibration_arduino.md). It is
uploaded once to the board (e.g. with the Arduino IDE), so the board does not need a
different firmware for every task.

```{admonition} Upload it again after updating the Training Village
:class: warning
The tasks and the firmware must be from the same version: the commands of the tasks
`arduino_2` to `arduino_6` now send their times in milliseconds as 32-bit integers
(before, 16-bit ones, which limited them to about one minute). With the old firmware
on the board, those tasks do not work.
```

Each task starts every trial with its own command (`CMD_HABITUATION`, `CMD_PASSIVE`...).
`loop()` reads the command byte first, waits until the whole message has arrived (its
size depends on the command, see `messageSize()`), and runs that task's trial function
(`runHabituation()`, `runPassive()`...). To add your own task, give it a new command, its
size in `messageSize()`, a `case` in `loop()` and its trial function.

{download}`Download village_arduino.ino <files/village_arduino/village_arduino.ino>`

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
```
