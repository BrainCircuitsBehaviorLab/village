## System Settings

Some initial settings must be configured before the system can be used.  Navigate to the `SETTINGS` screen and adjust the following sections according to your laboratory setup:

*   **`MAIN SETTINGS`:**
    *   **`SYSTEM_NAME`:** Define a unique identifier for your setup. This name will be appended to all saved datasets, which is essential for distinguishing data source origins if your facility operates multiple Training Villages.
    *   **`USE_CORRIDOR`:** Must be toggled **ON** for standard automated operations.
    *   **`USE_BOX_BOARD`:** Set to **ON** or **OFF** depending on whether your configuration utilizes auxiliary servo motors or dedicated illumination modules inside the operant chamber.
    *   **`Project Selection`:** This section allows you to select an active experimental project or initialize a new one. For now, keep the default project: **demo-village-project**.

*   **`CORRIDOR SETTINGS`:** Define the DAYTIME and NIGHTTIME parameters to set the specific hours you want the lights to turn on and off, the automated visible and IR lighting modules will cycle accordingly. Additionally, adjust the `DETECTION COLOR` parameter if you are tracking light-colored animals on a dark corridor background.

*   **`CONTROLLER SETTINGS`:** Select your primary behavioral control hardware architecture. If integrating a Bpod system, specify the target communication ports.
    ```{admonition} Note
    :class: tip
    The system automatically creates a symlink named `/dev/controller` pointing directly to any device connected to the bottom USB port adjacent to the Raspberry Pi's native RJ45 Ethernet jack.
    ```


*   **`CAMERA SETTINGS`:** Enable or disable real-time animal tracking for the operant box camera. If computer-vision-based tracking is not required for your paradigm, disabling it will significantly reduce CPU overhead. While resolution and frame-rate parameters are customizable, the default settings (**640x480 at 30 fps**) are highly optimized and thoroughly validated for low-latency processing.

*   **`SOUND SETTINGS`:** If your experimental protocols involve acoustic stimuli, enable `USE_SOUNDCARD` and select the **RPi DAC Pro** hardware profile from the `SOUND_DEVICE` dropdown menu.

*   **`SCREEN SETTINGS`:** If your behavioral arena features a display module or touchscreen interface for visual stimulus presentation, specify the hardware type in `USE_SCREEN` and calibrate the remaining parameters.

*   **`SYNC SETTINGS`:** Configure the destination for your external data synchronization. Refer to the [Data Persistence Section][BACKUP].

*   **`TELEGRAM SETTINGS`:** Input your unique authentication keys to link the system with your [Telegram Bot][TELEGRAM] and the external [Remote Heartbeat][REMOTE] monitoring service. You can customize alarm triggers, adjust sensor thresholds, or silence specific diagnostic checks by consulting the [Alarm System Section][ALARM].

    ```{admonition} Security Alert
    :class: warning
    Never share or publish your TELEGRAM_TOKEN. To prevent accidental exposure on public GitHub repositories, all local configuration parameters are automatically stored in a private .INI file located strictly outside of the main repository directory.
    ```

*   **`ADVANCED SETTINGS`:** Advanced settings and gui colors.

*   **`DEVICE ADDRESSES`:** Hardware indexing parameters. Use this section to remap camera IDs or servo motors IDs.


[BACKUP]: /system_operation/system.md
[TELEGRAM]: /preparation/telegram.md
[REMOTE]: /preparation/heartbeat.md
[ALARM]: /troubleshooting/alarm.md
