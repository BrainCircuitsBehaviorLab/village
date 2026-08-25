## System Settings

Some initial settings must be configured before the system can be used.  Navigate to the `SETTINGS` screen and adjust the following sections according to your laboratory setup:

*   **`MAIN SETTINGS`:**
    *   **`SYSTEM_NAME`:** Define a unique identifier for your setup. This name will be appended to all saved datasets, which is essential for distinguishing data source origins if your facility operates multiple Training Villages.
    *   **`FAVOURITE_TASK`:** A task preselected when opening the `TASKS` tab, so you can start a session immediately. Set to `None` to disable preselection.
    *   **`Project Selection`:** This section allows you to select an active experimental project or initialize a new one. For now, keep the default project: **demo-village-project**.

*   **`CORRIDOR SETTINGS`:** These settings only appear once `USE_CORRIDOR` (at the top of this section) is toggled **ON**; turning it off hides the rest of the section and disables the whole Corridor subsystem (RFID, scale, temperature sensor, motors, lighting, and the dedicated corridor camera). Define `DAYTIME` and `NIGHTTIME` to set the hours used by the `Corridor Cycle` control's `AUTO` mode (see the [GUI][GUI] section) to switch lighting and camera exposure/thresholds between day and night values. Adjust `DETECTION_COLOR` if you are tracking light-colored animals on a dark corridor background, and `MIN_WEIGHT_THRESHOLD`/`MAX_WEIGHT_THRESHOLD` to filter out invalid weight readings. `MOTOR3_CORRIDOR` and `MOTOR4_CORRIDOR` let you declare whether those optional motors are physically installed.

    ```{admonition} Note
    :class: tip
    Turning `USE_CORRIDOR` **OFF** also hides `TELEGRAM SETTINGS`. `USE_CORRIDOR` should only be OFF for setups running tasks manually rather than through the fully automated corridor pipeline, and without the corridor there is nothing for Telegram to monitor or alert on remotely.
    ```

*   **`BOX SETTINGS`:** Likewise gated by `USE_BOX_BOARD` at the top of the section, which enables the Operant Box PCB. Once ON, declare which box hardware is physically present: `MOTOR1_BOX` through `MOTOR7_BOX`, `VISIBLE_LIGHT_BOX`, `IR_LIGHT_BOX`, `LED_STRIP_BOX`, and `SCALE_BOX`. Only the components you mark **ON** here get initialized and show up as controls on the `MONITOR` screen's `BOX` tab.

*   **`CONTROLLER SETTINGS`:** Select your primary behavioral control hardware architecture (`BPOD`, `ARDUINO`, or `RASPBERRY`). `CONTROLLER_PORT` only appears for `BPOD`/`ARDUINO`, since `RASPBERRY` needs no external controller.
    ```{admonition} Note
    :class: tip
    The system automatically creates a symlink named `/dev/controller` pointing directly to any device connected to the bottom USB port adjacent to the Raspberry Pi's native RJ45 Ethernet jack.
    ```


*   **`CAMERA SETTINGS`:** Enable or disable real-time animal tracking for the operant box camera. If computer-vision-based tracking is not required for your paradigm, disabling it will significantly reduce CPU overhead. While resolution and frame-rate parameters are customizable, the default settings (**640x480 at 30 fps**) are highly optimized and thoroughly validated for low-latency processing.

*   **`SOUND SETTINGS`:** If your experimental protocols involve acoustic stimuli, enable `USE_SOUNDCARD` and select the **RPi DAC Pro** hardware profile from the `SOUND_DEVICE` dropdown menu.

*   **`SCREEN SETTINGS`:** If your behavioral arena features a display module or touchscreen interface for visual stimulus presentation, specify the hardware type in `USE_SCREEN` and calibrate the remaining parameters.

*   **`LED STRIP SETTINGS`:** Electrical configuration for the LED strip enabled via `LED_STRIP_BOX` in `BOX SETTINGS`: the `SPI_DEVICE` path, `NUMBER_OF_LEDS`, `SPI_SPEED_KHZ`, and the pixel color order (`PIXEL_TYPE`).

*   **`SYNC SETTINGS`:** Configure the destination for your external data synchronization. Refer to the [Data Persistence Section][BACKUP].

*   **`TELEGRAM SETTINGS`:** Input your unique authentication keys to link the system with your [Telegram Bot][TELEGRAM] and the external [Remote Heartbeat][REMOTE] monitoring service. You can customize alarm triggers, adjust sensor thresholds, or silence specific diagnostic checks by consulting the [Alarm System Section][ALARM].

    ```{admonition} Security Alert
    :class: warning
    Never share or publish your TELEGRAM_TOKEN. To prevent accidental exposure on public GitHub repositories, all local configuration parameters are automatically stored in a private .INI file located strictly outside of the main repository directory.
    ```

*   **`ADVANCED SETTINGS`:** Advanced settings and gui colors.


[BACKUP]: /preparation/backup.md
[TELEGRAM]: /preparation/telegram.md
[REMOTE]: /preparation/heartbeat.md
[ALARM]: /troubleshooting/alarm.md
[GUI]: /system_operation/GUI.md
