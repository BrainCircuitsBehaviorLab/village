## GUI Overview

Launch the GUI by entering the following command in a terminal:

```
village
```

When the GUI launches, the system automatically checks connections with essential components (such as cameras, temperature sensors, weight sensors, etc.). If any connection cannot be established, a warning message will display, and the Training Village will enter debug mode. For help resolving connection issues, refer to the [troubleshooting section][TROUBLE].

Once the GUI is active, a menu will appear at the top with the following options: `MAIN`, `MONITOR`, `SUBJECTS`, `TASKS`, `DATA`, `CALIBRATION` and `SETTINGS`.


---

### MAIN
![Main Training village screen](/_static/main_screen.png)

The default screen where the Raspberry Pi does not perform any rendering to display videos, although videos continue to be recorded and saved in the background. If there is no user activity for 5 minutes, the system automatically returns to this screen.

---

### MONITOR
![Monitor Training village screen](/_static/monitor_screen.png)

The `MONITOR` screen is used to track the system’s status, displaying real-time video feeds from both the corridor and the operant box. Here, you can view images captured by the two system cameras: one positioned above the corridor and another focused inside the operant box.

#### Primary Control Tabs
Depending on your active configuration, several control tabs are available at the center of the screen:

*   **`CORRIDOR`:** Provides manual and automated overrides for the RFID reader, doors, weighing scale, and temperature sensor. When the RFID system is toggled **OFF**,
    animal identification is disabled, and no subjects will be permitted to enter the operant box.

    *Lighting and camera exposure/thresholds are driven together by the `Corridor Cycle` control, which can be set to `DAY`, `NIGHT`, or `AUTO`. `DAY` turns the visible light **ON** and the IR light **OFF**, and applies the daytime camera exposure/threshold settings. `NIGHT` does the opposite: visible light **OFF**, IR light **ON**, and the nighttime camera exposure/threshold settings. `AUTO` switches automatically between `DAY` and `NIGHT` according to the actual time of day; the daytime/nighttime schedule can be customized under `SETTINGS` -> `CORRIDOR SETTINGS`.*

*   **`BOX`:** Provides dedicated controls for the lighting, scale and motor modules inside the operant box. If a Bpod is connected as the primary behavioral controller, this tab will also display dedicated
    buttons to manually trigger the port LEDs or deliver water rewards (1-second duration) directly to the behavior ports.

    *The `Visible Light` and `IR Light` modes can be set to `ON`, `OFF`, or `AUTO`. In `AUTO` mode, both visible and IR lights (if installed) are dynamically triggered: they switch ON automatically as soon as an animal enters the operant box and switch OFF once the subject leaves.*

*   **`FUNCTIONS`:** Allows you to execute custom, user-defined Python functions in real time (e.g., displaying specific visual stimuli, playing auditory cues, etc.). Step-by-step instructions
    for writing and deploying these scripts can be found in the [Protocol Creation][CREATE] section.

*   **`VIRTUAL MOUSE`:** Enables real-time simulation of animal behavior through software triggers—an invaluable tool for debugging task logic and testing system responsiveness.
    *   **Bpod Integration:** Simulate a nose-poke in any behavior port with a single click.
    *   **Touchscreen Integration:** Simulate screen-touch events by sending precise coordinate inputs $(x, y)$.
    *   **Position Tracking:** If real-time animal tracking is active within the operant box, you can simulate custom trajectories to verify location-based experimental triggers.


#### Secondary Diagnostic Tabs
A secondary group of tabs is located at the bottom of the screen to monitor system telemetry and history:

*   **`INFO`:** Displays a live stream of recent system events and operational logs. Double-clicking any logged event opens an expanded window with detailed diagnostic information.
*   **`PLOT`:** Renders an interactive graphical chart illustrating both successful entries and denied entry attempts for all subjects over the past seven days.
*   **`DETECTION SETTINGS`:** Provides fine-grained control over the computer vision and animal detection parameters for both the corridor and operant box tracking systems. A comprehensive breakdown of these parameters is available in the [Animal Detection Section][DETECTION].

---


### SUBJECTS
![Tasks Training Village screen](/_static/subjects_screen.png)
In this section you can create new subjects. Check the [Subject Management Section][SUBJECT].

---


### TASKS
![Tasks Training Village screen](/_static/tasks_screen.png)

From this screen, tasks can be launched manually at any time.

The active training protocol is displayed on the left side, along with a list of all available tasks. Clicking on the training protocol allows you to test its functionality (check the [Manual Task Execution][MANUAL] section to know how). When you click on a task, task information is displayed, along with an options menu that includes the following settings:

- `maximum_number_of_trials`: The task will automatically end once this number of trials is completed.
- `maximum_duration`: The task will automatically end when this timer is reached.

In addition to these settings, a list of all variables defined for this specific training protocol will appear. In the [Protocol Creation][CREATE] section, we explain how to create a protocol and define its variables.

Next to the `RUN TASK` button, which starts the task, the `Subject` selector opens a list of all available subjects, as well as the option "None." Selecting "None" runs the task without saving any data.

### DATA
![Main Training village screen](/_static/data_screen.png)

On this screen, saved data is displayed. The following tables are accessible:

*   **`EVENTS`:** A comprehensive system log that records animal entries, exits, and denied entry attempts. Selecting any specific event and clicking `VIDEO` opens the corresponding video recording of that moment.

*   **`SESSIONS SUMMARY`:** A historical list of all completed training sessions. Selecting an item from this list grants access to its corresponding CSV file (available in both standard `DATA` and raw `DATA_RAW` formats), the session's video file, `VIDEO` and a user-configurable behavioral plot `PLOT`.

*   **`TEMPERATURES`:** A chronological log of all recorded environmental temperature and humidity values within the system.

*   **`SESSION_RAW`:** Displays the session currently in progress or the most recently completed one, rendered in real time (one row per registered hardware/behavioral event). Clicking `PLOT` opens a user-configurable, real-time graphical chart of the session.

*   **`SESSION`:** Displays the session currently in progress or the most recently completed one, structured according to the final data storage format (parsed dynamically into one row per trial). Clicking `PLOT` opens a user-configurable, real-time graphical chart of the session.

*   **`CALIBRATION`:** Contains parameter data regarding all currently active system calibrations.


A more detailed description of these tables, including their exact database schemas and storage paths, can be found in the [Saved Data][DATA] section.

---

### CALIBRATION
![Calibration Training village screen](/_static/calibration_screen.png)

This screen provides a dedicated panel for each calibration tool available on the system. A left-side menu lists every calibration relevant to your current hardware configuration; selecting an entry opens its panel on the right.

Besides the calibration tools installed by default, you can create your own and have them appear here alongside the built-in ones — see the [Custom Calibrations][CALIBRATIONS] section for details.

*   **`BPOD_WATER_CALIBRATION`:** Calibrates the relationship between valve opening time and the volume of water actually delivered, per behavior port, and lets you test a calibration by requesting a target volume. Only available when the Bpod is the configured behavior controller. See [Bpod Water Calibration](/calibrations/bpod_water.md).

*   **`SOUND_CALIBRATION`:** Calibrates speaker output so a requested sound level corresponds to an actual, measured volume. Only available when `USE_SOUNDCARD` is **ON**. See [Sound Calibration](/calibrations/sound.md).

*   **`CAMERA_CALIBRATION`:** Generates a printable symmetric circle grid used to calibrate lens distortion for the system cameras. Always available. See [Camera Calibration](/calibrations/camera.md).

*   **`CORRIDOR_THRESHOLD_CALIBRATION`:** Lets you position the four corridor detection areas and tune their day/night pixel-detection thresholds while previewing the result against a recorded corridor video. Only available when `USE_CORRIDOR` is **ON**. See [Corridor Threshold Calibration](/calibrations/thresholds.md).

*   **`OPTOGRID_CALIBRATION`:** Provides a visual map of the OptoGrid device for composing an LED selection and inspecting it over Bluetooth. Always available. See [OptoGrid Calibration](/calibrations/optogrid.md).

---

### SETTINGS
![Main Training village screen](/_static/settings_screen.png)

This section displays a comprehensive list of all modifiable system settings, organized into distinct categories for streamlined configuration. You can hover over any individual parameter item to view a tooltip with more detailed information.

The most critical parameters from this list will be discussed and modified step-by-step in the next section.



[TROUBLE]: /troubleshooting/troubleshooting.md
[STATES]: /system_operation/system.md
[DETECTION]: /system_operation/detection.md
[SUBJECT]: /system_operation/subject.md
[MANUAL]: /system_operation/manual.md
[CREATE]: /protocols/creating.md
[DATA]: /system_operation/data.md
[CALIBRATIONS]: /advanced_customization/calibrations.md
