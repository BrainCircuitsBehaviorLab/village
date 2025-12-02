## Receive and Respond to Telegram Alarms

### Interrogate the system
You can use various commands to retrieve information from the system. Simply type these commands in a private chat with the bot (only you will receive the response) or in the group channel where the bot is present (all participants will see the response).
All commands start with the / symbol:

- `/report ‘hours’`: Provides a summary of the behavioral box activity during the last specified hours (default is 24 hours).
- `/cam`: Sends a screenshot from both cameras.
- `/plot ‘days’`: Displays a plot of entrances and attempts over the last specified days (default is 3 days).



### Alarms
The system is designed to cover every potential scenario, resulting in an extensive list of alarms. While many of these alarms may never be triggered, some could only appear once every few months.



## System Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| Invalid data in subjects.csv | An error occurred while reading subjects.csv. The file may contain malformed rows, inconsistent numbers of columns, or unintended spaces or line breaks. | Verify that the CSV structure is correct: all rows must contain the same number of columns, without stray spaces, tabs, or newline characters. Fix or recreate the file if needed. |
| Detection in area4 when it should be empty | When the operant box is empty and a subject is detected by the RFID reader, pixels are also detected in Area 4, which should be empty. | Check corridor illumination and remove any dirt or objects causing false detection. If an animal is actually present, review previous videos to determine the cause (door malfunction, incorrect threshold settings). |
| Error running task | A task execution error occurred, likely caused by an exception in the task code. | Inspect the event logs to obtain the full traceback and identify the problematic line of code. |
| Wrong RFID detection | Caused by: (1) A different subject detected during another subject’s task; or (2) The correct subject detected in the corridor despite door 2 being closed. | Review corridor video footage to determine the cause (door malfunction, lighting issues, threshold errors, or multiple animals entering). |
| Maximum time reached and areas 3 or 4 were never empty | Door 2 should close once areas 3 and 4 are empty. If the maximum task duration is reached and these areas never cleared, the alarm is triggered. | Check lighting, clean the corridor, verify that the animal did not fall asleep or hesitate to enter the box, and check for door malfunction or threshold issues. |
| The subject has been in the box for too long | More than one hour has passed since the task ended and the subject is still inside the operant box. | Check via video if the subject is asleep. Verify that the scale and door servos are functioning properly to allow the subject to exit. |


## Hardware Failure Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| Camera not responding | The camera restarts after failing to deliver frames for 10 seconds, usually due to intermittent connection or low signal quality. | Check the ribbon cable and connectors. Ensure the cable is not bent, damaged, or too long. |
| Scale not responding | The scale continuously reports 0.0 g, indicating invalid readings from the load cell. | Check scale wiring and connectors. Ensure all cables are firmly attached and the external 5V supply reaches the board. |


## Hourly System Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| Low/High temperature | Temperature has risen above or fallen below the configured threshold. | Verify the room temperature with an independent sensor and apply the appropriate corrective measures. |
| No detections in the set interval | No subject detected by RFID during the last X hours (configured by the user). | Ensure corridor access is unobstructed (door 1 open). Check RFID wiring and confirm the external 5V supply reaches the reader. |
| No sessions in the set interval | No session performed within the last X hours. | Check corridor access, RFID functionality, and ensure that the cameras are not falsely detecting pixels due to lighting or threshold issues. |
| Heartbeat Not Received | The remote server did not receive the latest heartbeat signal. | Check whether the system is accessible remotely; it may have frozen or lost internet connectivity. If the system is unresponsive, attempt to restart it. If uncertain whether it's a system failure or an internet outage, perform a physical inspection to ensure no subject is trapped without food or water. |
| Low disk space (less than 10GB) | The SD card is almost full. | Videos are stored for X days (configurable) and deleted only after proper synchronization. Check rsync_logs and data_removal_logs. Reduce the number of stored days if needed. |


## Twice-Daily Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| Subjects with low water intake in the last 24h | The subject consumed less than the configured water threshold in the last 24 hours. | Verify that the water delivered in each trial is being correctly registered. Check water delivery, valve/solenoid calibration, and confirm that the task is functioning correctly. |
| Subjects with no session in the last 24h | The subject has not performed a session during the last 24 hours (only for subjects that were active). | Verify corridor access, door 1 operation, RFID functionality, and camera-based detection. |
| Subjects not detected in the last 24h | The subject has not been detected by RFID for 24 hours. | Check corridor access, door 1 status, and the correct functioning and power supply of the RFID system. |
| No data sync in the last 24h | No data has been synchronized with the external server/drive during the last 24 hours. | Check the rsync_logs to identify the source of the error and verify network connectivity and remote storage availability. |


## Task Running Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| 2 Subjects in Box | Pixel count suggests more than one subject has entered the operant box. | Connect remotely and verify. If true, carefully open/close doors 1 and 2 to let animals exit safely. Stop the task (disables RFID). Restore the correct corridor state and reactivate RFID. If false alarm, adjust lighting, cleanliness, and thresholds. |
| Subject in Prohibited Area | Pixels detected in a restricted region. | Connect remotely to confirm whether detection is real or false. If false alarm, inspect illumination, cleanliness, and threshold settings. |
| Error in sound device | An error occurred when attempting to play a sound. | Check the event log to see the traceback and identify the cause. |
| Error in video worker | An error occurred when attempting to display video or visual stimuli. | Inspect the event log and traceback to determine the source of the issue. |


## Saving Data Alarms

| Alarm | Description | Solution |
|-------|-------------|-----------|
| Error saving the task | The task data could not be saved. | Check the events log and traceback to identify the cause. |
| Error updating the training settings | Training settings could not be updated; the subject keeps its previous configuration. | Check the event log. The update logic is delicate and may fail due to unexpected CSV formatting. Test this function from the TASKS tab after modifying the code. |
| The session file is very large | The session CSV contains more than 100,000 rows, often caused by a high-frequency sensor malfunction. | Inspect photogates, wiring, and hardware for noise or malfunction. |
| No water was drunk | The subject did not drink any water during the task. (Optional check) | Verify water logging, water delivery, solenoid calibration, and task operation. |
| No trials were recorded | The subject did not complete any trials. (Optional check) | Confirm the subject entered the operant box and did not fall asleep. Check task logic and hardware functionality. |




```{important}
 A missing heartbeat may result from a temporary internet outage, a power failure, or a system freeze.

In such cases, first attempt to connect remotely:
- If the system has restarted, simply relaunch Training Village.
- If the process is unresponsive, investigate the terminal error messages.
- If remote access fails, a physical check may be required to ensure the animals’ safety.
```

#### Subject Checks Performed Twice a Day

Whenever there is a transition between day and night, the system evaluates the state of the animals and generates a report containing the number of detections, sessions, water intake and average weight for all subjects.
A warning alarm is also sent if one or more subjects have a warning.
Warnings are listed in order of severity, from least to most critical:

- `Low Water Intake 24h`, `No detection 24h`, `No session 24h`



```{important}
In certain critical situations, the task is terminated, and the RFID reader is disconnected to prevent other subjects from entering the behavioral box until the issue is resolved.

In these cases, the system waits for the subject currently in the box to exit and be weighed on the scale. Once this is completed, Door 2 is closed, and Door 1 is opened.

It is essential to connect remotely, verify that all animals are in the home cage, resolve the issue, and reactivate the RFID reader.
```



```{important}
Always review videos corresponding to unusual alarms to identify the root cause, such as dirt, threshold issues, lighting errors, or hardware malfunctions.

To view a video:
1. Locate the alarm in `DATA` screen -> `EVENTS`.
2. Click the alarm row, then select `VIDEO` to watch the footage.


[SETTINGS]: /user_guide/GUI.md#settings
[TROUBLE]: /troubleshooting/troubleshooting.md
