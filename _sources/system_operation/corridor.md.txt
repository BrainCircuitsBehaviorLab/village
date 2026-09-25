## Corridor Hardware Setup

The corridor elements must be calibrated. Navigate to the `MONITOR` Screen:

1. **Set Door Motor Angles**: Select the `CORRIDOR` tab in the center of the screen. Each installed motor has its own `MOTORx VALUES` button (`MOTOR1`/`MOTOR2` are always shown; `MOTOR3`/`MOTOR4` only appear if enabled in `SETTINGS` → `CORRIDOR SETTINGS`). Clicking it opens a dialog with the `Open angle`/`Open time (ms)` and `Close angle`/`Close time (ms)` fields, a `Hold position` checkbox, plus `OPEN`/`CLOSE` buttons to move the motor immediately and test the values before committing. The closing angle should allow the door to gently touch the top without pushing further.
```{admonition} Note
:class: tip
Due to the symmetrical placement of the servomotors, the opening angle will be greater than the closing angle for one servo, while the opposite will apply to the other. Typically, the angular displacement between the open and closed positions is approximately 25° to 30°. The most straightforward way to calibrate the gates is by following these steps:
1. Temporarily detach the plastic gate from the servo horn.
2. Click **CLOSE** in the dialog, then manually place and secure the plastic gate in its physical "fully closed" position.
3. Modify the `Open angle` field by just a few degrees (either above or below the closed angle value). Click **OPEN** to verify that the servo rotates in the expected direction.
4. Adjust the final `Open angle` incrementally until the gate allows the animal to pass through easily when open.
5. Once you are happy with the angles and times, click **SAVE** to persist them (or **DISCARD** to revert to the values the motor had before opening the dialog).
```
```{admonition} Hold position
:class: tip
`Hold position` sets what the motor does **after** it arrives, and it is saved per motor along with the angles and times:

- **Checked** (the default): the servo stays powered and keeps its holding torque, so it resists a load — but it hums continuously and warms up.
- **Unchecked**: the PWM signal is cut once the motor has arrived, so the servo goes quiet and cool — but anything pushing on it can move it out of position.

Corridor doors normally want it checked, since the door has to stay where it was put. A mechanism that latches on its own, or one that only has to reach a position and then be left alone, is better off unchecked.

The checkbox takes effect immediately on `OPEN`/`CLOSE`, so you can hear the difference before saving. It only sets the **default**: task code can override it for a single movement (see [Motors](motors.md)).
```
2. **Calibrate the Scale**: Use the `CALIBRATE SCALE` button with a known weight to calibrate the scale, `TARE SCALE` to zero it, and verify functionality by pressing `GET WEIGHT`.
3. **Check Temperature and Humidity**: Use the `GET TEMPERATURE` button to check temperature and humidity readings.

```{admonition} Note
:class: tip
If you are using motors in the operant box, calibrate them the same way from the `BOX` tab: each active motor (up to `MOTOR1`-`MOTOR7`, as enabled in `SETTINGS` → `BOX SETTINGS`) has its own `MOTORx VALUES` button opening the same angle/time dialog. If a box scale is enabled (`SCALE_BOX`), the `BOX` tab also has its own `CALIBRATE SCALE`, `TARE SCALE`, and `GET WEIGHT` buttons, calibrated independently from the corridor scale.
```

```{warning}
If the `CORRIDOR` or `BOX` tabs are not visible, it is because the corresponding options `USE_CORRIDOR` or `USE_BOX_BOARD` are disabled in `SETTINGS` → `CORRIDOR SETTINGS` / `BOX SETTINGS`.
```
