## village_arduino.ino

The firmware for all the Arduino examples: the six `arduino_*` tasks and the
[water calibration](../advanced_customization/water_calibration_arduino.md). It is
uploaded once to the board (e.g. with the Arduino IDE), so the board does not need a
different firmware for every task.

Each task starts every trial with its own command (`CMD_HABITUATION`, `CMD_PASSIVE`...).
`loop()` reads the command byte first, waits until the whole message has arrived (its
size depends on the command, see `messageSize()`), and runs that task's trial function
(`runHabituation()`, `runPassive()`...). To add your own task, give it a new command, its
size in `messageSize()`, a `case` in `loop()` and its trial function.

{download}`Download village_arduino.ino <files/village_arduino/village_arduino.ino>`

```{literalinclude} files/village_arduino/village_arduino.ino
:language: cpp
```
