## Bpod Water Calibration

Calibrates the relationship between how long a valve is open and how much water it
actually delivers, per behavior port — so tasks can request a volume in microliters
instead of a raw opening time.

```{admonition} Note
:class: note
Only available when the Bpod is the configured behavior controller
(`BEHAVIOR_CONTROLLER` → `BPOD`).
```

### Calibrating

For each active port (`BPOD_BEHAVIOR_PORTS`), enter a valve opening time and a number
of iterations, run it, then weigh the total water collected and enter it back — the
panel computes microliters delivered per opening and plots it. Repeat with a few
different opening times per port (at least two points are required) to build a
time → volume curve.

### Testing

Enter a target volume in microliters and a number of iterations to open the valve for
the time the calibration predicts, then weigh the result the same way. If the measured
error is too large, use that test point as a new calibration point instead of
discarding it — no need to redo the whole calibration from scratch.

### Using it in tasks

Every method on the panel is reachable from any task via `self.calibrations`:

```python
time_s = self.calibrations.bpod_water_calibration.get_valve_time(port, volume_ul)
```

`get_valve_time` interpolates the opening time for a target volume from the most
recent calibration of that port, and raises if the port hasn't been calibrated or the
volume falls outside the calibrated range.

Data is stored in `bpod_water_calibration.csv` (columns: `date`, `port_number`,
`time(s)`, `water_delivered(ul)`, `calibration_number`, `water_expected(ul)`,
`error(%)`).

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
