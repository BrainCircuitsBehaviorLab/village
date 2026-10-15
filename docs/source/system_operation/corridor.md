## Monitor & Hardware Setup

![Monitor Training village screen](/_static/monitor_screen.webp)

The `MONITOR` screen is used to track the system’s status, displaying real-time video feeds from both the corridor and the operant box, and to control and set up the hardware.

### Control Tabs
Several control tabs are available at the center of the screen. Which ones are shown depends on your configuration:

*   **`CORRIDOR`:** only if `USE_CORRIDOR` is ON (`SETTINGS` → `CORRIDOR SETTINGS`).
*   **`BOX`:** only if `USE_BOX_BOARD` is ON (`SETTINGS` → `BOX SETTINGS`) or the behavioral controller is a Bpod.
*   **`FUNCTIONS`:** always.
*   **`VIRTUAL MOUSE`:** only if the behavioral controller is a Bpod or the box camera tracking is enabled.

#### `CORRIDOR`

```{image} /_static/corridor_menu.webp
:alt: CORRIDOR tab
:width: 380px
```

Provides manual control of the corridor hardware (RFID reader, doors, weighing scale and temperature sensor), and is where the corridor elements are set up.

*   **`RFID Reader`:** When it is toggled **OFF**, animal identification is disabled, and no subjects will be permitted to enter the operant box.
*   **`Corridor Cycle`:** Lighting and camera exposure/thresholds are driven together by this control, which can be set to `DAY`, `NIGHT`, or `AUTO`. `DAY` turns the visible light **ON** and the IR light **OFF**, and applies the daytime camera exposure/threshold settings. `NIGHT` does the opposite: visible light **OFF**, IR light **ON**, and the nighttime camera exposure/threshold settings. `AUTO` switches automatically between `DAY` and `NIGHT` according to the actual time of day; the daytime/nighttime schedule can be customized under `SETTINGS` → `CORRIDOR SETTINGS`.

##### Door motors

The `OPEN MOTORx` / `CLOSE MOTORx` buttons move each door with its saved values. To set those values, each installed motor has its own `MOTORx VALUES` button (`MOTOR1`/`MOTOR2` are always shown; `MOTOR3`/`MOTOR4` only appear if enabled in `SETTINGS` → `CORRIDOR SETTINGS`). Clicking it opens a dialog with the `Open angle`/`Open time (ms)` and `Close angle`/`Close time (ms)` fields, a `Hold position` checkbox, plus `OPEN`/`CLOSE` buttons to move the motor immediately and test the values before committing. The closing angle should allow the door to gently touch the top without pushing further.

Due to the symmetrical placement of the servomotors, the opening angle will be greater than the closing angle for one servo, while the opposite will apply to the other. Typically, the angular displacement between the open and closed positions is approximately 25° to 30°. The most straightforward way to calibrate the gates is by following these steps:

1. Temporarily detach the plastic gate from the servo horn.
2. Click **CLOSE** in the dialog, then manually place and secure the plastic gate in its physical "fully closed" position.
3. Modify the `Open angle` field by just a few degrees (either above or below the closed angle value). Click **OPEN** to verify that the servo rotates in the expected direction.
4. Adjust the final `Open angle` incrementally until the gate allows the animal to pass through easily when open.
5. Once you are happy with the angles and times, click **SAVE** to persist them (or **DISCARD** to revert to the values the motor had before opening the dialog).

```{admonition} Hold position
:class: note
`Hold position` sets what the motor does **after** it arrives, and it is saved per motor along with the angles and times:

- **Checked** (the default): the servo stays powered and keeps its holding torque, so it resists a load — but it hums continuously and warms up.
- **Unchecked**: the PWM signal is cut once the motor has arrived, so the servo goes quiet and cool — but anything pushing on it can move it out of position.

Corridor doors normally want it checked, since the door has to stay where it was put. A mechanism that latches on its own, or one that only has to reach a position and then be left alone, is better off unchecked.

The checkbox takes effect immediately on `OPEN`/`CLOSE`, so you can hear the difference before saving. It only sets the **default**: task code can override it for a single movement (see [Motors](../devices/motors.md)).
```

```{admonition} A motor stops responding
:class: note
If a motor stops responding to `OPEN`/`CLOSE` after being physically disconnected and
reconnected, restart Village rather than assuming it's broken — see
[Troubleshooting](../troubleshooting/troubleshooting.md).
```

##### Scale

Use the `CALIBRATE SCALE` button with a known weight to calibrate the scale, `TARE SCALE` to zero it, and verify functionality by pressing `GET WEIGHT`.

##### Temperature sensor

Use the `GET TEMPERATURE` button to check temperature and humidity readings.

#### `BOX`

```{image} /_static/box_menu.webp
:alt: BOX tab
:width: 380px
```

Provides dedicated controls for the lighting, scale and motor modules inside the operant box (as enabled in `SETTINGS` → `BOX SETTINGS`).

*   **`Visible Light` / `IR Light`:** Can be set to `ON`, `OFF`, or `AUTO`. In `AUTO` mode, both visible and IR lights (if installed) are dynamically triggered: they switch ON automatically as soon as an animal enters the operant box and switch OFF once the subject leaves.

    ```{admonition} The box must never be completely dark
    :class: warning
    The box camera is watched all the time, even between sessions, to check that no
    animal is left inside. If its image stays completely black for 10 seconds, the system
    treats the camera as failed and restarts it. Setting both lights to `AUTO` is only
    safe if the box gets some light from another source (light coming in from outside, a
    photogate, a port LED...), enough for the image not to be fully black. If that is not
    the case, set the `IR Light` (or the `Visible Light`) to `ON` instead of `AUTO`.
    ```

*   **Motors and scale:** They work like the ones in the `CORRIDOR` tab. Each active motor (up to `MOTOR1`-`MOTOR7`, as enabled in `SETTINGS` → `BOX SETTINGS`) has its own `MOTORx VALUES` button opening the same angle/time dialog. If a box scale is enabled (`SCALE_BOX`), the tab also has its own `CALIBRATE SCALE`, `TARE SCALE`, and `GET WEIGHT` buttons, calibrated independently from the corridor scale.

*   **`LEDx` / `WATERx`:** Only if a Bpod is the behavioral controller. They turn on the LED of a behavior port, or deliver water (1-second valve opening) to it.

#### `FUNCTIONS`

```{image} /_static/functions_menu.webp
:alt: FUNCTIONS tab
:width: 380px
```

Allows you to execute custom, user-defined Python functions in real time (e.g., displaying specific visual stimuli, playing auditory cues, etc.). Step-by-step instructions for writing and deploying these functions can be found in the [Direct Functions](../protocols/functions.md) section.

#### `VIRTUAL MOUSE`

```{image} /_static/virtual_menu.webp
:alt: VIRTUAL MOUSE tab
:width: 380px
```

Enables real-time simulation of animal behavior through software triggers—an invaluable tool for debugging task logic and testing system responsiveness.

*   **Bpod Integration (`POKE1`-`POKE8`):** Simulate a nose-poke in any behavior port with a single click.
*   **Touchscreen Integration:** Simulate screen-touch events by sending precise coordinate inputs $(x, y)$ (`Touch the screen`).
*   **AutoNoMouse:** If the box camera tracking is enabled, `AutoNoMouse` starts and stops a virtual animal that performs the running task by itself, and `Inject Trials` adds `N inject` simulated trials to the session data (one every `Interval (s)` seconds), to fill a session quickly and test the plots or the training protocol. See [Custom AutoNoMouse](../advanced_customization/auto.md).

---

### Bottom Tabs
A secondary group of tabs is located at the bottom of the screen to monitor system telemetry and history:

*   **`INFO`:** Displays a live stream of recent system events and operational logs. Double-clicking any logged event opens an expanded window with detailed diagnostic information.
*   **`PLOT`:** Only with `USE_CORRIDOR` ON. Renders an interactive graphical chart illustrating both successful entries and denied entry attempts for all subjects over the past seven days.
*   **`DETECTION SETTINGS`:** Provides fine-grained control over the computer vision and animal detection parameters for both the corridor and operant box tracking systems. A comprehensive breakdown of these parameters is available in the [Animal Detection & Tracking](detection.md).
*   **`EXTRA`:** Only with `CORRIDOR_AREA_EXTRA` ON (`SETTINGS` → `ADVANCED SETTINGS`). Configures the extra corridor area used to check that the passage between the two homecages is not blocked. See [Homecage Camera Control](../advanced_customization/homecage_camera_control.md).
