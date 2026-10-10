## Custom Calibrations

There are two ways to handle calibrations in Village. The simplest option is to write a standalone script outside of Village, run it independently, and store the results in a format you can read from your tasks. The second option is to create a calibration class that integrates directly with the GUI, stores data as a `.csv` file, and makes calibration values accessible from any task.

This page describes the second approach.

---

### Creating a Calibration Class

Create a Python file inside your `project/code` folder with a class that inherits from `CalibrationBase`. Inside this class, define a data structure using `create_data_collection`, and a small GUI to interact with calibration parameters. If the hardware has to do something while you measure (open a valve, play a sound, turn on a LED...), you will also need a task that inherits from `CalibrationTaskBase` (see [Running a Task from the Calibration](#running-a-task-from-the-calibration)).

Three built-in calibration examples are included in the Village codebase under `village/calibration/`:

- `sound_calibration.py`
- `water_calibration.py`
- `camera_calibration.py`

These are a good starting point for understanding how calibration classes work.
A complete custom calibration, small enough to read in one go, is
[led_calibration.py](../examples/led_calibration.md): a panel that turns on a
port LED to measure it, a `.csv` file to keep the measurements and a method that
tasks call.

The `name` given to `create_data_collection` is also the name of the
attribute in `self.calibrations` (`self.calibrations.led_calibration`), and it
must not be the name of a built-in calibration (`water_calibration`,
`sound_calibration`, `camera_calibration`, `corridor_threshold_calibration`,
`optogrid_calibration`).

---

### Defining the Data Structure


Use `create_data_collection` in `__init__` to define the columns and types of your calibration data. The example below shows how `SoundCalibration` class is declared:

```python
from village.custom_classes.calibration_base import CalibrationBase

class SoundCalibration(CalibrationBase):
    """Sound speaker calibration and testing panel."""

    def __init__(self) -> None:
        super().__init__()

        name = "sound_calibration"
        columns = [
            "date",
            "speaker",
            "sound_name",
            "gain",
            "dB_obtained",
            "calibration_number",
            "dB_expected",
            "error(%)",
        ]
        types = [str, int, str, float, float, int, float, float]

        self.create_data_collection(name=name, columns=columns, types=types)
```

---

### Running a Task from the Calibration

A calibration task inherits from `CalibrationTaskBase`
(`village.custom_classes.calibration_task_base`), which is a `TaskBase` with a
few differences:

- It does not appear in the TASKS tab, and its `__init__` can take the
  arguments the panel needs (the port, the time, the intensity...).
- Without Bpod, `register_start_trial` is optional.
- `start`, `after_trial` and `close` do nothing by default, and it runs one
  trial. Usually only `create_trial` has to be written.

The panel launches it with `self.run_task(task)` (it returns `False`, without
launching it, if a task is already running), and can stop it with
`self.stop_task()`. `self.task_running()` is `True` until the task has finished;
check it in `update_gui`, which is called periodically, to know when the
measurement can be entered:

```python
class LedCalibrationTask(CalibrationTaskBase):

    def __init__(self, port: int, intensity: int) -> None:
        super().__init__()
        self.port = port
        self.intensity = intensity

    def create_trial(self) -> None:
        self.bpod.add_state(
            state_name="led_on",
            state_timer=20,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[("PWM" + str(self.port), self.intensity)],
        )


class LedCalibration(CalibrationBase):
    ...

    def turn_on(self) -> None:  # called by a button of the panel
        if self.run_task(LedCalibrationTask(port=2, intensity=100)):
            self.led_on = True

    def update_gui(self) -> None:
        if self.led_on and not self.task_running():
            self.led_on = False
            # the LED is off again: ask for the measurement
```

The built-in water calibration works the same way, with
`WaterCalibrationTaskBase`, see [Water Calibration](../calibrations/water.md).

---

### Querying Calibration Values from a Task

It is useful to add methods to your calibration class that retrieve the values needed during a task. For example, `SoundCalibration` provides `get_sound_gain()`, which takes a speaker, a target level in dB, and a sound name, and returns the gain value required to reach that level based on the stored calibration data:

```python
def get_sound_gain(self, speaker: int, dB: float, sound_name: str) -> float:
    try:
        if dB == 0:
            return 0.0
        calibration_df = self.df[self.df["speaker"] == speaker]
        calibration_df = calibration_df[calibration_df["sound_name"] == sound_name]
        max_calibration = calibration_df["calibration_number"].max()
        calibration_df = calibration_df[
            calibration_df["calibration_number"] == max_calibration
        ]
        val = get_x_value_interp(
            calibration_df["gain"].values,
            calibration_df["dB_obtained"].values,
            dB,
        )
        if val is None:
            raise ValueError
        return val
    except Exception:
        raise ValueError(
            f"\n\n\t--> SOUND CALIBRATION PROBLEM !!!!!!\n\n"
            f"Cannot provide a valid gain for {dB} dB, "
            f"speaker {speaker}, sound {sound_name}.\n"
            f"1. Make sure you have calibrated the sound you are using.\n"
            f"2. Make sure the dB is within calibration range.\n"
            f"3. Check sound_calibration.csv in 'data'.\n"
        )
```

Any method defined in your calibration class is accessible from any task via the `calibrations` object:

```python
self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)
```
