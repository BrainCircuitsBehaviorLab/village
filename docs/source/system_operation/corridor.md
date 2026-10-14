## Monitor & Hardware Setup

![Monitor Training village screen](/_static/monitor_screen.webp)

The `MONITOR` screen is used to track the system’s status, displaying real-time video feeds from both the corridor and the operant box, and to control and set up the hardware.

### Control Tabs
Depending on your active configuration, several control tabs are available at the center of the screen:

*   **`CORRIDOR`:** Provides manual and automated overrides for the RFID reader, doors, weighing scale, and temperature sensor. When the RFID system is toggled **OFF**,
    animal identification is disabled, and no subjects will be permitted to enter the operant box.

    ```{image} /_static/corridor_menu.webp
    :alt: CORRIDOR tab
    :width: 380px
    ```

    *Lighting and camera exposure/thresholds are driven together by the `Corridor Cycle` control, which can be set to `DAY`, `NIGHT`, or `AUTO`. `DAY` turns the visible light **ON** and the IR light **OFF**, and applies the daytime camera exposure/threshold settings. `NIGHT` does the opposite: visible light **OFF**, IR light **ON**, and the nighttime camera exposure/threshold settings. `AUTO` switches automatically between `DAY` and `NIGHT` according to the actual time of day; the daytime/nighttime schedule can be customized under `SETTINGS` -> `CORRIDOR SETTINGS`.*

*   **`BOX`:** Provides dedicated controls for the lighting, scale and motor modules inside the operant box. If a Bpod is connected as the primary behavioral controller, this tab will also display dedicated
    buttons to manually trigger the port LEDs or deliver water rewards (1-second duration) directly to the behavior ports.

    ```{image} /_static/box_menu.webp
    :alt: BOX tab
    :width: 380px
    ```

    *The `Visible Light` and `IR Light` modes can be set to `ON`, `OFF`, or `AUTO`. In `AUTO` mode, both visible and IR lights (if installed) are dynamically triggered: they switch ON automatically as soon as an animal enters the operant box and switch OFF once the subject leaves.*

    ```{admonition} The box must never be completely dark
    :class: warning
    The box camera is watched all the time, even between sessions, to check that no
    animal is left inside. If its image stays completely black for 10 seconds, the system
    treats the camera as failed and restarts it. Setting both lights to `AUTO` is only
    safe if the box gets some light from another source (light coming in from outside, a
    photogate, a port LED...), enough for the image not to be fully black. If that is not
    the case, set the `IR Light` (or the `Visible Light`) to `ON` instead of `AUTO`.
    ```

    ```{admonition} A motor stops responding
    :class: note
    If a motor stops responding to `OPEN`/`CLOSE` after being physically disconnected and
    reconnected, restart Village rather than assuming it's broken — see
    [Troubleshooting](../troubleshooting/troubleshooting.md).
    ```

*   **`FUNCTIONS`:** Allows you to execute custom, user-defined Python functions in real time (e.g., displaying specific visual stimuli, playing auditory cues, etc.). Step-by-step instructions
    for writing and deploying these functions can be found in the [Direct Functions](../protocols/functions.md) section.

    ```{image} /_static/functions_menu.webp
    :alt: FUNCTIONS tab
    :width: 380px
    ```

*   **`VIRTUAL MOUSE`:** Enables real-time simulation of animal behavior through software triggers—an invaluable tool for debugging task logic and testing system responsiveness (see also [Custom AutoNoMouse](../advanced_customization/auto.md), a virtual animal that performs a task by itself).

    ```{image} /_static/virtual_menu.webp
    :alt: VIRTUAL MOUSE tab
    :width: 380px
    ```
    *   **Bpod Integration:** Simulate a nose-poke in any behavior port with a single click.
    *   **Touchscreen Integration:** Simulate screen-touch events by sending precise coordinate inputs $(x, y)$.
    *   **Position Tracking:** If real-time animal tracking is active within the operant box, you can simulate custom trajectories to verify location-based experimental triggers.


### Bottom Tabs
A secondary group of tabs is located at the bottom of the screen to monitor system telemetry and history:

*   **`INFO`:** Displays a live stream of recent system events and operational logs. Double-clicking any logged event opens an expanded window with detailed diagnostic information.
*   **`PLOT`:** Renders an interactive graphical chart illustrating both successful entries and denied entry attempts for all subjects over the past seven days.
*   **`DETECTION SETTINGS`:** Provides fine-grained control over the computer vision and animal detection parameters for both the corridor and operant box tracking systems. A comprehensive breakdown of these parameters is available in the [Animal Detection & Tracking](detection.md).

---

### Setting Up the Hardware

The corridor elements must be calibrated from the `MONITOR` screen:

1. **Set Door Motor Angles**: Select the `CORRIDOR` tab in the center of the screen. Each installed motor has its own `MOTORx VALUES` button (`MOTOR1`/`MOTOR2` are always shown; `MOTOR3`/`MOTOR4` only appear if enabled in `SETTINGS` → `CORRIDOR SETTINGS`). Clicking it opens a dialog with the `Open angle`/`Open time (ms)` and `Close angle`/`Close time (ms)` fields, a `Hold position` checkbox, plus `OPEN`/`CLOSE` buttons to move the motor immediately and test the values before committing. The closing angle should allow the door to gently touch the top without pushing further.
```{admonition} Note
:class: note
Due to the symmetrical placement of the servomotors, the opening angle will be greater than the closing angle for one servo, while the opposite will apply to the other. Typically, the angular displacement between the open and closed positions is approximately 25° to 30°. The most straightforward way to calibrate the gates is by following these steps:
1. Temporarily detach the plastic gate from the servo horn.
2. Click **CLOSE** in the dialog, then manually place and secure the plastic gate in its physical "fully closed" position.
3. Modify the `Open angle` field by just a few degrees (either above or below the closed angle value). Click **OPEN** to verify that the servo rotates in the expected direction.
4. Adjust the final `Open angle` incrementally until the gate allows the animal to pass through easily when open.
5. Once you are happy with the angles and times, click **SAVE** to persist them (or **DISCARD** to revert to the values the motor had before opening the dialog).
```
```{admonition} Hold position
:class: note
`Hold position` sets what the motor does **after** it arrives, and it is saved per motor along with the angles and times:

- **Checked** (the default): the servo stays powered and keeps its holding torque, so it resists a load — but it hums continuously and warms up.
- **Unchecked**: the PWM signal is cut once the motor has arrived, so the servo goes quiet and cool — but anything pushing on it can move it out of position.

Corridor doors normally want it checked, since the door has to stay where it was put. A mechanism that latches on its own, or one that only has to reach a position and then be left alone, is better off unchecked.

The checkbox takes effect immediately on `OPEN`/`CLOSE`, so you can hear the difference before saving. It only sets the **default**: task code can override it for a single movement (see [Motors](../devices/motors.md)).
```
2. **Calibrate the Scale**: Use the `CALIBRATE SCALE` button with a known weight to calibrate the scale, `TARE SCALE` to zero it, and verify functionality by pressing `GET WEIGHT`.
3. **Check Temperature and Humidity**: Use the `GET TEMPERATURE` button to check temperature and humidity readings.

```{admonition} Note
:class: note
If you are using motors in the operant box, calibrate them the same way from the `BOX` tab: each active motor (up to `MOTOR1`-`MOTOR7`, as enabled in `SETTINGS` → `BOX SETTINGS`) has its own `MOTORx VALUES` button opening the same angle/time dialog. If a box scale is enabled (`SCALE_BOX`), the `BOX` tab also has its own `CALIBRATE SCALE`, `TARE SCALE`, and `GET WEIGHT` buttons, calibrated independently from the corridor scale.
```

```{warning}
If the `CORRIDOR` or `BOX` tabs are not visible, it is because the corresponding options `USE_CORRIDOR` or `USE_BOX_BOARD` are disabled in `SETTINGS` → `CORRIDOR SETTINGS` / `BOX SETTINGS`.
```
