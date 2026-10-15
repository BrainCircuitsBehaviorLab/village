## System Settings

![Settings Training village screen](/_static/settings_screen.webp)

Some initial settings must be configured before the system can be used.  Navigate to the `SETTINGS` screen and adjust the following sections according to your laboratory setup:

*   **`MAIN SETTINGS`:**
    *   **`SYSTEM_NAME`:** Define a unique identifier for your setup. This name will be appended to all saved datasets, which is essential for distinguishing data source origins if your facility operates multiple Training Villages.
    *   **`Project Selection`:** This section allows you to select an active experimental project or initialize a new one. For now, keep the default project: **demo-village-project**.

*   **`CORRIDOR SETTINGS`:** The `USE_CORRIDOR` toggle at the top of the section decides whether the system uses the corridor (changing it requires a restart).
    *   **`ON`** (the default): the fully automated Training Village, where animals enter the operant box on their own through the corridor. Keep it ON unless you have a reason not to.
    *   **`OFF`:** for setups that only use the operant box, running tasks manually (e.g. tethered ephys or optogenetics recordings). The whole Corridor subsystem is disabled: RFID reader, scale, temperature sensor, door motors, lighting and the corridor camera. The Telegram bot is disabled and no alarms are sent, since without the corridor there is nothing to monitor remotely.

    With `USE_CORRIDOR` ON, the rest of the section is shown. Define `DAYTIME` and `NIGHTTIME` to set the hours used by the `Corridor Cycle` control's `AUTO` mode (see [Monitor & Hardware Setup][GUI]) to switch lighting and camera exposure/thresholds between day and night values. Adjust `DETECTION_COLOR` if you are tracking light-colored animals on a dark corridor background, and `MIN_WEIGHT_THRESHOLD`/`MAX_WEIGHT_THRESHOLD` to filter out invalid weight readings. `MOTOR3_CORRIDOR` and `MOTOR4_CORRIDOR` let you declare whether those optional motors are physically installed.

*   **`BOX SETTINGS`:** Likewise gated by `USE_BOX_BOARD` at the top of the section, which enables the Operant Box PCB. Once ON, declare which box hardware is physically present: `MOTOR1_BOX` through `MOTOR7_BOX`, `VISIBLE_LIGHT_BOX`, `IR_LIGHT_BOX`, `LED_STRIP_BOX`, and `SCALE_BOX`. Only the components you mark **ON** here get initialized and show up as controls on the `MONITOR` screen's `BOX` tab.

*   **`CONTROLLER SETTINGS`:** Select your primary behavioral control hardware architecture: `BPOD` (state machine construction, event/state logging and softcodes are all built in), or `OTHER` (any other microcontroller you talk to yourself from within the task, or no microcontroller at all if you control everything from the Raspberry Pi). `CONTROLLER_PORT` is only actually used when `BPOD` is selected, or when an `OTHER` task talks to an external microcontroller over serial.
    ```{admonition} Note
    :class: note
    The system automatically creates a symlink named `/dev/controller` pointing directly to any device connected to the bottom USB port adjacent to the Raspberry Pi's native RJ45 Ethernet jack.
    ```


*   **`CAMERA SETTINGS`:** Enable or disable real-time animal tracking for the operant box camera. If computer-vision-based tracking is not required for your paradigm, disabling it will significantly reduce CPU overhead. While resolution and frame-rate parameters are customizable, the default settings (**640x480 at 30 fps**) are highly optimized and thoroughly validated for low-latency processing.

*   **`SOUND SETTINGS`:** If your experimental protocols involve acoustic stimuli, enable `USE_SOUNDCARD` and select the **RPi DAC Pro** hardware profile from the `SOUND_DEVICE` dropdown menu.

*   **`SCREEN SETTINGS`:** If your behavioral arena features a display module or touchscreen interface for visual stimulus presentation, specify the hardware type in `USE_SCREEN` and calibrate the remaining parameters.

*   **`LED STRIP SETTINGS`:** Electrical configuration for the LED strip enabled via `LED_STRIP_BOX` in `BOX SETTINGS`: the `SPI_DEVICE` path, `NUMBER_OF_LEDS`, `SPI_SPEED_KHZ`, and the pixel color order (`PIXEL_TYPE`).

*   **`SYNC SETTINGS`:** Configure the destination for your external data synchronization, and how many days the videos are kept (`DAYS_OF_VIDEO_STORAGE`). Refer to the [Data Persistence Section][BACKUP].

*   **`TELEGRAM SETTINGS`:** Input your unique authentication keys to link the system with your [Telegram Bot][TELEGRAM] and the external [Remote Heartbeat][REMOTE] monitoring service. You can customize alarm triggers, adjust sensor thresholds, or silence specific diagnostic checks by consulting the [Alarm System Section][ALARM].

    ```{admonition} Security Alert
    :class: warning
    Never share or publish your TELEGRAM_TOKEN. To prevent accidental exposure on public GitHub repositories, all settings are stored in the user's configuration on the Raspberry Pi, outside of the repository directory.
    ```

*   **`ADVANCED SETTINGS`:** Settings that rarely need to be changed, such as the favourite task preselected when opening the `TASKS` screen (`FAVOURITE_TASK`) or the time before the GUI returns to the `MAIN` screen (`SCREENSAVE_TIME`), and the `VISUAL SETTINGS` (colors used in the GUI and on the camera images).


[BACKUP]: /preparation/backup.md
[TELEGRAM]: /preparation/telegram.md
[REMOTE]: /preparation/heartbeat.md
[ALARM]: /troubleshooting/alarm.md
[GUI]: /system_operation/corridor.md
