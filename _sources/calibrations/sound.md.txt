## Sound Calibration

Calibrates speaker output so a requested sound level in dB corresponds to an actual,
measured volume — per speaker (left/right) and per sound, so tasks can request a
sound in dB instead of a raw gain value.

```{admonition} Note
:class: note
Only available when `USE_SOUNDCARD` is **ON**.
```

```{admonition} Note
:class: note
The `SOUND` dropdown lists the functions in `sound_calibration_functions`, defined in
your project's `code/sound_functions.py`. Each function takes `gain` and `duration`
and returns a mono NumPy waveform array; see the demo-village-project for examples.
```

### Calibrating

Pick a sound and a speaker, enter a gain (0-1) and a duration in seconds, then click
`CALIBRATE` — the sound is played once through that speaker. Measure the resulting
volume with a sound level meter and enter it in dB, then click `ADD` to save the
point — it's added to the calibration curve, plotted immediately, and listed under
`CALIBRATION POINTS`, where each point can be removed individually with its `-`
button if it turns out to be an outlier. Repeat with a few different gain values per
speaker/sound pair (at least two points are required) to build a gain → dB curve. If
the sound device fails to play the sound, an error dialog is shown and the inputs are
reset instead of prompting for a measurement.

Once you're happy with the curve, click `SAVE CALIBRATION` to persist it. Any
speaker/sound pair left with fewer than two points is dropped from the save, with a
warning listing which ones. Saved calibrations are never overwritten — every save gets
a new `calibration_number` and the full history is kept, but tasks and the testing
panel always use the most recent one per speaker/sound pair. `DELETE CALIBRATION`
discards the points collected so far (after confirmation) without saving them.

### Testing

Check whether the latest saved calibration for a speaker/sound pair is still accurate.
Pick the sound and speaker, enter a target dB and a duration, then click `TEST` — the
panel looks up the gain the calibration curve predicts for that dB. If the pair hasn't
been calibrated yet, or the target dB falls outside the calibrated range, you get a
warning immediately and nothing is played. Otherwise the sound is played at that gain;
measure the actual dB the same way as during calibration and enter it back — the panel
shows the resulting error and plots the test point against the existing curve.

- If the error is acceptable, click `OK`. The measurement is recorded for reference
  (it does not affect `get_sound_gain`, since it's stored with `calibration_number`
  -1) and the panel is cleared for another test.
- If the error is too large, click `FAIL` instead. The measurement is recorded the
  same way, but it's also used as the first point of a brand-new calibration for that
  speaker/sound pair, so you can immediately continue adding points to it (as in
  Calibrating above) and save a corrected curve.

### Using it in tasks

```python
gain = self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)
```

Given a speaker (`0` = left, `1` = right), a target dB, and the sound's function name,
this interpolates the gain from that speaker/sound pair's most recent saved
calibration curve. `dB=0` always returns a gain of `0.0` without needing a
calibration. Otherwise, if the pair hasn't been calibrated yet, or `dB` falls outside
the calibrated range, it raises a `ValueError` explaining the problem so it's easy to
tell whether the sound needs calibrating or the requested dB needs adjusting.

Data is stored in `sound_calibration.csv` (columns: `date`, `speaker`, `sound_name`,
`gain`, `dB_obtained`, `calibration_number`, `dB_expected`, `error(%)`).

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
