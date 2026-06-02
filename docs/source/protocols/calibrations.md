## Custom Calibrations

There are two ways to handle calibrations in Village. The simplest option is to write a standalone script outside of Village, run it independently, and store the results in a format you can read from your tasks. The second option is to create a calibration class that integrates directly with the GUI, stores data as a `.csv` file, and makes calibration values accessible from any task.

This page describes the second approach.

---

### Creating a Calibration Class

Create a Python file inside your `project/code` folder with a class that inherits from `CalibrationBase`. Inside this class, define a data structure using `create_data_collection`. You will typically also need a task class (inheriting from `Task`) that runs the calibration procedure, and a small GUI to interact with calibration parameters.

Three built-in calibration examples are included in the Village codebase under `village/calibration/`:

- `sound_calibration.py`
- `bpod_water_calibration.py`
- `camera_calibration.py`

These are a good starting point for understanding how calibration classes work.

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
