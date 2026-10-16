## Water Calibration

![Water calibration screen](/_static/calibration_screen.webp)

Calibrates the relationship between how long a valve (or a pump) is open and how much
water it actually delivers, per behavior port — so tasks can request a volume in
microliters instead of a raw opening time.

Always available in the `CALIBRATION` screen.

Every time you click `CALIBRATE` or `TEST`, the panel runs a small task that opens each
selected valve for its time, one after the other, and repeats the whole sequence the
number of iterations you entered. That task depends on the controller:

- **With Bpod** (`BEHAVIOR_CONTROLLER` → `BPOD`), it is built in: there is nothing to
  set up.
- **With any other controller**, you have to write it: a class inheriting from
  `WaterCalibrationTaskBase` (`village.custom_classes.water_calibration_task_base`), in
  the project's code directory, that runs the same sequence on that controller. For an
  Arduino, a ready-to-use example is in
  [Water Calibration with Arduino](../advanced_customization/water_calibration_arduino.md).

### Calibrating

You can calibrate one port at a time or several at once. If you are using Bpod, only the
ports enabled in `BPOD_BEHAVIOR_PORTS` appear in the panel.
For each port you want to calibrate, enter a valve opening time and a shared number of
iterations, then click `CALIBRATE` — the selected valves each open that many
times for that long. Weigh the total water collected per port and enter it back; the
panel converts the weight to microliters delivered per iteration (assuming a water
density of 1 g/ml) and shows it next to each port. Click `ADD` to save the point — it's
added to the calibration curve, plotted immediately, and listed under
`CALIBRATION POINTS`, where each point can be removed individually with its
`-` button if it turns out to be an outlier. Repeat with a few different opening times
per port (at least two points are required) to build a time → volume curve.

Once you're happy with the curve, click `SAVE CALIBRATION` to persist it.
Saved calibrations are never overwritten — every save gets a new `calibration_number`
and the full history is kept, but tasks and the `TESTING` panel always use the most
recent one per port. `DELETE CALIBRATION` discards the points collected so far (after
confirmation) without saving them.

```{admonition} Tip
:class: note
If you're not sure what time to start with, begin with a short opening time (a few
ms). You can always delete points later that turn out to be far outside the range of
interest for your tasks.
```

### Testing

Check whether the latest saved calibration for a port is still accurate. Enter a
target volume in microliters and a number of iterations; the panel looks up the
opening time the calibration curve predicts for that volume and, on `TEST`, opens the
valve that many times for that long. Weigh the result the same way as during
calibration — the panel shows the measured volume per iteration and the resulting
error compared to the target, and plots the test point against the existing curve.

- If the error is acceptable, click `OK`. The measurement is recorded for reference.
- If the error is too large, click `FAIL` instead. The measurement is used as the first point of a brand-new calibration for that port, so you can immediately continue adding points to it (as in Calibrating above) and save a corrected curve.


### Using it in tasks

Every method on the panel is reachable from any task via `self.calibrations`:

```python
time_s = self.calibrations.water_calibration.get_valve_time(port, volume_ul)
```

Given a (1-indexed) port number and a target volume in microliters, this interpolates
the valve opening time from that port's most recent saved calibration curve. If the
port hasn't been calibrated yet, or `volume_ul` falls outside the calibrated range, it
raises a `ValueError` explaining the problem so it's easy to tell whether the port
needs calibrating or the requested volume needs adjusting.

Data is stored in `water_calibration.csv` (columns: `date`, `port_number`,
`time(s)`, `water_delivered(ul)`, `calibration_number`, `water_expected(ul)`,
`error(%)`).
