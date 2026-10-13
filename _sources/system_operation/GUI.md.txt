## GUI Overview

Launch the GUI by entering the following command in a terminal:

```
village
```

When the GUI launches, the system automatically checks connections with essential components (such as cameras, temperature sensors, weight sensors, etc.). If any connection cannot be established, a warning message will display, and the Training Village will enter debug mode. For help resolving connection issues, refer to the [troubleshooting section][TROUBLE].

Once the GUI is active, a menu will appear at the top with the following screens: `MAIN`, `MONITOR`, `SUBJECTS`, `TASKS`, `DATA`, `CALIBRATION` and `SETTINGS`, and a toolbar with the buttons described [below](#toolbar).

---

### MAIN
![Main Training village screen](/_static/main_screen.webp)

The default screen where the Raspberry Pi does not perform any rendering to display videos, although videos continue to be recorded and saved in the background. If there is no user activity for 5 minutes (`SCREENSAVE_TIME` in `SETTINGS` → `ADVANCED SETTINGS`), the system automatically returns to this screen.

---

### MONITOR
![Monitor Training village screen](/_static/monitor_screen.webp)

The live images of the corridor and box cameras, with the controls of the hardware (doors, scales, lights, RFID reader...), the direct functions, the virtual mouse, and the events and detection settings. See [Monitor & Hardware Setup][MONITOR].

---

### SUBJECTS
![Subjects Training Village screen](/_static/subjects_screen.webp)

In this section you can create new subjects and edit their settings. See [Subject Management][SUBJECT].

---

### TASKS
![Tasks Training Village screen](/_static/tasks_screen.webp)

Run any task manually, with or without a subject, and test the training protocol. See [Manual Task Execution][MANUAL].

---

### DATA
![Data Training village screen](/_static/data_screen.webp)

Browse the events, sessions, temperatures and calibrations, plot them and watch the videos. See [Data Visualization][DATAVIS].

---

### CALIBRATION
![Calibration Training village screen](/_static/calibration_screen.webp)

One panel for each calibration of the system. See [Calibration Overview][CALIBRATION].

---

### SETTINGS
![Settings Training village screen](/_static/settings_screen.webp)

All the system settings, organized into categories. Hover over any setting to see a tooltip with more detailed information. The ones to configure first are explained in [System Settings][SETTINGS].

---

### Toolbar

The top bar of the GUI contains a set of buttons for performing the following actions. Depending on the current system state, you will see different buttons available.

#### `CHANGE STATE`

Opens a dialog offering only the actions valid for the current state:

- While the system believes a subject is inside the box but it is not (e.g. a door did not close properly and the animal escaped back to the home cage without being detected), it offers **"All subjects are back home, go to WAIT state."**
- While the system is in the WAIT state, it offers **"Force data sync"** (forces an immediate synchronization, useful if the automatic sync did not run due to a connection failure, a network change, or any other issue) and **"Subject is inside the box"** (use this when the system believes there is no subject in the box but there is one — e.g. two mice entered the operant box simultaneously and the system detected one exiting, switching to WAIT while the other stayed inside).

#### `STOP SYNC`

By default, the system synchronizes data with an external device or server after each session ends. While syncing, animals cannot be detected or enter the operant box. `STOP SYNC` stops the current synchronization — useful during testing to avoid waiting for a sync after each test run, since it will run automatically at the end of the next session. Once synchronization is complete (or stopped), the system returns to the WAIT state and animals can enter again.

#### `STOP TASK`

Stops a running task. In automatic mode, pressing this button disconnects the RFID reader to prevent new animals from entering, and the system waits for the current animal to exit the box. If you remove the animal manually, use `CHANGE STATE` → "All subjects are back home, go to WAIT state" afterwards and re-enable the RFID reader.

#### `ONLINE PLOTS`

Shows live plots while a task is running. The plots displayed are configurable by the user. Only enabled while a task is actually running.

#### `CHECK MICE`

Confirms that the mice have been checked today. Shows `CHECK MICE` and turns orange until confirmed, either by clicking it or via the `/mice_checked` Telegram command; once confirmed, it shows `MICE OK` and stays disabled until the next reset, which happens at midnight. If the mice have not been checked by the time set in `SETTINGS` → `TELEGRAM SETTINGS` → `CHECK_MICE_TIME`, an alarm is triggered to remind you via Telegram.

#### `ALARM`

Shows the number of pending alarms and turns orange while any are pending (`NO ALARMS` when there are none). Clicking it acknowledges every pending alarm and stops their Telegram reminders.

#### `EXIT`

Shuts down the system.



[TROUBLE]: /troubleshooting/troubleshooting.md
[MONITOR]: /system_operation/corridor.md
[SUBJECT]: /system_operation/subject.md
[MANUAL]: /system_operation/manual.md
[DATAVIS]: /system_operation/data_visualization.md
[CALIBRATION]: /calibrations/overview.md
[SETTINGS]: /system_operation/settings.md
