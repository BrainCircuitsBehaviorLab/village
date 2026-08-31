## Sound Calibration

Calibrates speaker output so a requested sound level in dB corresponds to an actual,
measured volume — per speaker (left/right) and per sound.

```{admonition} Note
:class: note
Only available when `USE_SOUNDCARD` is **ON**.
```

### Calibrating

For a speaker and a sound, play it at a range of gain values (0-1) and measure the
resulting dB with a sound level meter, entering the readings back into the panel. The
panel builds a gain → dB curve per speaker/sound pair (at least two points needed) and
plots it, so you can see the relationship across the calibrated range.

### Testing

Enter a target dB and let the panel compute and play the gain it predicts, then
measure the actual dB and enter it back. A test point with too much error can be kept
as a new calibration point instead of being discarded.

### Using it in tasks

```python
gain = self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)
```

`get_sound_gain` interpolates the gain needed to reach a target dB, for a given
speaker and sound, from the most recent calibration — and raises if that sound hasn't
been calibrated or the requested dB is outside the calibrated range.

Data is stored in `sound_calibration.csv` (columns: `date`, `speaker`, `sound_name`,
`gain`, `dB_obtained`, `calibration_number`, `dB_expected`, `error(%)`).

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
