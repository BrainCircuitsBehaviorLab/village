## Receive and Respond to Telegram Alarms

### Interrogate the system
You can use various commands to retrieve information from the system. Simply type these commands in a private chat with the bot (only you will receive the response) or in the group channel where the bot is present (all participants will see the response).
All commands start with the `/` symbol:

- `/report ‘hours’`: Provides a summary of the behavioral box activity for the last specified hours (default = 24h).
- `/cam`: Sends a screenshot from both cameras.
- `/plot ‘days’`: Shows a plot of entrances and attempts over the specified days (default = 3 days).

---

### Subject Checks Performed Twice a Day

Whenever there is a transition between day and night, the system evaluates the state of the animals and generates a report containing the number of detections, sessions, water intake and average weight for all subjects.

A warning alarm is also sent if one or more subjects present an issue.
Warnings (from least to most critical):

- `Subjects with low water intake in the last 24h`
- `Subjects with no session in the last 24h`
- `Subjects not detected in the last 24h`

---

### Alarms
The system is designed to cover all potential scenarios, resulting in an extensive list of alarms. While many may never appear, some occur rarely but are critical.


```{important}
Always check the events log to determine which error occurred. If the error originates from the code, inspect the traceback to understand what happened.
Always review the video recordings associated with unusual alarms to identify the root cause (e.g., lighting, thresholds, dirt, hardware).

To view the details of an error (including traceback when available):
1. Open the `DATA` screen → `EVENTS`.
2. Double-click the alarm row.

To view a corridor video:
1. Open the `DATA` screen → `EVENTS`.
2. Select the alarm row.
3. Click `VIDEO` to watch the footage.

To view a session video:
1. Open the `DATA` screen → `SESSIONS_SUMMARY`.
2. Select the session row.
3. Click `VIDEO` to watch the footage.
```

---
#### System Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Invalid data in subjects.csv
  - An error occurred while reading subjects.csv. The file may contain malformed rows, inconsistent numbers of columns, or unintended spaces or line breaks.
  - Verify that the CSV structure is correct: all rows must contain the same number of columns, without stray spaces, tabs, or newline characters. Fix or recreate the file if needed.

* - Detection in area4 when it should be empty
  - When the operant box is empty and a subject is detected by the RFID reader, pixels are also detected in Area 4, which should be empty.
  - Check corridor illumination and remove any dirt or objects that may cause false detection. If an animal is actually present in area 4 when it should not be, review the previous videos to determine the cause (e.g., door malfunction, lightning issues, inaccurate camera thresholding).

* - Error running task ⚠️
  - A task execution error occurred, likely caused by an exception in the task code.
  - Inspect the event logs to obtain the full traceback and identify the line of code that triggered the error.

* - Wrong RFID detection ⚠️
  - This alarm has two possible causes. 1) A different subject was detected in the corridor while the main subject was performing the task. 2) The correct subject was detected in the corridor even though door 2 was already closed and the subject should not be there.
  - Review the previous videos to determine the cause (e.g., door malfunction, lightning issues, inaccurate camera thresholding).

* - Maximum time reached and areas 3 or 4 were never empty ⚠️
  - After a subject enters the operant box, door 2 should close once areas 3 and 4 are empty. If the maximum task duration is reached and these areas were never cleared, the alarm is triggered.
  - Check lighting and remove any dirt or objects in the corridor. Verify whether the animal fell asleep in the corridor or hesitated to enter the operant box. Review previous videos to check for door malfunction or issues with pixel detection.

* - The subject has been in the box for too long
  - More than one hour has passed since the task ended, and the animal remains inside the operant box.
  - Verify via video that the animal is still inside—often it is simply asleep. Confirm that both the scale and door servos are functioning correctly; if they fail, the subject may be unable to exit the box.
```

```{important}
Some critical alarms disable the RFID reader and halt new entries to protect other subjects.

The system waits for the current subject to exit and be weighed, then closes Door 2 and opens Door 1.

You must connect remotely, verify all animals are in the home cage, resolve the issue, and reactivate the RFID reader.
```
#### Hardware Failure Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Camera not responding
  - The camera automatically restarts after failing to deliver frames for 10 seconds. This usually indicates an intermittent connection or insufficient signal quality along the camera cable.
  - Check the camera ribbon cable and its connectors on both ends. Ensure that the cable is not bent, damaged, or excessively long, as long cables can occasionally cause frame dropouts.

* - Scale not responding
  - The scale is continuously returning a weight of 0.0 grams, indicating that it is not receiving valid readings from the load cell.
  - Inspect the scale wiring and connectors, ensuring all cables are firmly attached. Verify that the external 5V power supply is reaching the board.
```
#### Hourly System Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Low/High temperature
  - Temperature has risen above or fallen below the configured threshold.
  - Verify the room temperature using an independent sensor and take the appropriate corrective measures.

* - No detections in the set interval
  - No animal has been detected by the RFID system during the last X hours (X defined in settings).
  - Ensure that animals have unobstructed access to the corridor (no blockage, door 1 open). Check RFID cabling and confirm that the external 5V power supply is reaching the board.

* - No sessions in the set interval
  - No session has been performed within the last X hours.
  - Verify corridor access and correct RFID operation. Ensure the cameras are not falsely detecting pixels when the corridor is empty (check illumination and threshold configuration).

* - Heartbeat Not Received ⚠️
  - The remote server did not receive the latest heartbeat signal.
  - Check whether the system is accessible remotely; it may have frozen or lost internet connectivity. If the system is unresponsive, attempt to restart it. If you cannot confirm whether the issue is due to a system failure or an internet outage, a physical inspection is required to ensure animal safety—an animal may be trapped inside the operant box without access to food or water.

* - Low disk space (less than 10GB)
  - The disk is nearly full.
  - Videos are kept on the Raspberry Pi’s SD card for X days (user-defined in settings) and are automatically deleted only after proper synchronization with an external server or drive. Review rsync_logs and data_removal_logs to confirm that files are being synchronized and deleted correctly. If necessary, reduce the number of days for which videos are stored.
```

```{important}
A missing heartbeat may be caused by temporary internet loss, a power outage, or a system freeze.

Before acting:
- Attempt to connect remotely.
- If the system restarted, simply relaunch Training Village.
- If unresponsive, inspect terminal logs.
- If remote access fails, perform a physical check to ensure animal safety.
```
#### Twice-Daily Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Subjects with low water intake in the last 24h
  - The subject consumed less than the configured water-intake threshold during the last 24 hours.
  - Verify that the water delivered in each trial is being correctly registered. Check water delivery, valve/solenoid calibration, and confirm that the task is functioning correctly.

* - Subjects with no session in the last 24h
  - The subject has not performed a session during the last 24 hours (this alarm is triggered only for subjects that were active during this period). This check can be enabled or disabled in the settings.
  - Verify corridor access, door 1 operation, RFID functionality, and camera-based detection.

* - Subjects not detected in the last 24h
  - The subject has not been detected by the RFID system for the last 24 hours. This check can be enabled or disabled in the settings.
  - Check corridor access, door 1 status, and the correct functioning and power supply of the RFID system.

* - No data sync in the last 24h
  - No data has been successfully synchronized with the external server or hard drive during the last 24 hours.
  - Check the rsync_logs to identify the source of the error and verify network connectivity and remote storage availability.
```
#### Task Running Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - 2 Subjects in Box
  - The pixel count suggests that more than one animal has entered the operant box.
  - Connect remotely to verify whether this is a true event or a false alarm. If two animals are indeed inside the box, carefully open and close door 2 and door 1 to allow them to exit safely. Stop the task (this will automatically disable the RFID reader), and once everything is back to normal, ensure that door 2 is closed and door 1 is open, then reactivate the RFID reader. If this was a false alarm, check illumination, cleanliness, and pixel-detection thresholds to prevent future false detections.

* - Subject in Prohibited Area
  - Pixels are detected in a region where no animal should be present.
  - Connect remotely to confirm whether the detection is real or a false alarm. If the alarm was false, inspect illumination, cleanliness, and pixel-detection thresholds to reduce the likelihood of recurring false positives.

* - Error in sound device
  - An error occurred while attempting to play a sound.
  - Check the events log to see the traceback and identify the exact cause of the error.

* - Error in video worker
  - An error occurred while attempting to display video or visual stimuli.
  - Check the events log to inspect the traceback and determine the source of the problem.
```
#### Saving Data Alarms
```{list-table}
:widths: 20 40 40
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Error saving the task
  - The task data could not be saved.
  - Check the events log to inspect the traceback and identify the cause of the error.

* - Error updating the training settings
  - The training settings could not be updated, so the subject will keep its previous configuration.
  - Check the events log to inspect the traceback. The code that updates the training settings is delicate and may fail if the format of the CSV has changed unexpectedly (e.g., a column that is now a string instead of an integer). After modifying this part of the code, you can test it from the TASKS tab.

* - The session file is very large
  - The session CSV contains more than 100,000 rows, typically caused by an abnormally high-frequency sensor event.
  - Inspect photogates, check for cable noise, and verify that no hardware component is malfunctioning.

* - No water was drunk
  - The subject did not drink any water during the task. This check can be enabled or disabled in the settings.
  - Verify that the water delivered in each trial is being correctly registered. Check water delivery, valve/solenoid calibration, and confirm that the task is functioning properly.

* - No trials were recorded
  - The subject did not complete any trials. This check can be enabled or disabled in the settings.
  - Confirm that the animal entered the operant box and did not fall asleep. Inspect the task logic and verify that all hardware components are functioning correctly.
```
