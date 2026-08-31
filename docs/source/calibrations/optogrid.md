## OptoGrid Calibration

Provides a visual map of the OptoGrid optogenetic stimulation device (a wireless,
64-LED array) for composing an LED selection and inspecting the device over
Bluetooth.

```{admonition} Note
:class: note
Always available. Requires `bleak` for Bluetooth scanning — if it isn't installed,
scanning/connecting is unavailable but the rest of the panel still works.
```

### Scanning and connecting

**SCAN** looks for nearby OptoGrid devices over Bluetooth Low Energy. Selecting one
and connecting reads back its current parameters and battery level (mV and estimated
percentage) — useful to check the device is alive and see what it's currently
configured with before a session.

### Selecting LEDs

Click or drag on the interactive brain map to toggle individual LEDs on or off. The
selection is a 64-bit mask (`led_selection`) mapping directly to anatomical
coordinates on the map, so you can compose exactly which LEDs a stimulation should
target by eye instead of working out bit positions by hand.

### Stimulation parameters

The panel also lists the device's stimulation parameters for reference: sequence
length, LED selection, duration, period, pulse width, amplitude, PWM frequency, and
ramp up/down — the same parameters a task sets when driving the device via
`village.devices.optogrid.OptoGrid`.

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
