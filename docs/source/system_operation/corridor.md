## Corridor Calibration

The corridor elements must be calibrated. Navigate to the `MONITOR` Screen:

1. **Set Door Motor Angles**: Select the `CORRIDOR` tab in the center of the screen and use the `CHANGE MOTOR ANGLES` button to correctly set the opening and closing angles for each door. The closing angle should allow the door to gently touch the top without pushing further.
```{admonition} Note
:class: tip
Due to the symmetrical placement of the servomotors, the opening angle will be greater than the closing angle for one servo, while the opposite will apply to the other. Typically, the angular displacement between the open and closed positions is approximately 25° to 30°. The most straightforward way to calibrate the gates is by following these steps:
1. Temporarily detach the plastic gate from the servo horn.
2. Click the **CLOSE** button in the interface, then manually place and secure the plastic gate in its physical "fully closed" position.
3. Modify the `OPEN` angle parameter by just a few degrees (either above or below the closed angle value). Click **OPEN** to verify that the servo rotates in the expected direction.
4. Adjust the final `OPEN` angle incrementally until the gate allows the animal to pass through easily when open.
```
2. **Calibrate the Scale**: Use the `CALIBRATE SCALE` button with a known weight to calibrate the scale, and verify functionality by pressing `GET WEIGHT`.
3. **Check Temperature and Humidity**: Use the `GET TEMPERATURE` button to check temperature and humidity readings.

```{admonition} Note
:class: tip
If you are using motors in the operant box, you can calibrate them by navigating to the `BOX` tab and selecting the `CHANGE MOTOR ANGLES` button in that tab.
```

```{warning}
If the `CORRIDOR` or `BOX` tabs are not visible, it is because the corresponding options `USE_CORRIDOR` or `USE_BOX_BOARD` are disabled in `SETTINGS` → `MAIN SETTINGS`.
```
