## Receive and Respond to Telegram Alarms

### Interrogate the system
You can use various commands to retrieve information from the system. Simply type these commands in a private chat with the bot (only you will receive the response) or in the group channel where the bot is present (all participants will see the response).
All commands start with the / symbol:

- `/report ‘hours’`: Provides a summary of the behavioral box activity during the last specified hours (default is 24 hours).
- `/cam`: Sends a screenshot from both cameras.
- `/plot ‘days’`: Displays a plot of entrances and attempts over the last specified days (default is 3 days).



### Alarms
The system is designed to cover every potential scenario, resulting in an extensive list of alarms. While many of these alarms may never be triggered, some could only appear once every few months.


| Type                     | Name                           | Description                                                                                                              | Solution                                                                                     |
|--------------------------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Hourly System Check      | Low Temperature                | Temperature dropped below the configured threshold.                                                                      | Check HVAC, heating, and sensor calibration.                                                  |
| Hourly System Check      | High Temperature               | Temperature exceeded the configured threshold.                                                                           | Check HVAC, lights, airflow, and sensor calibration.                                          |
| Hourly System Check      | No Detection (X hours)         | No animal detected by RFID in the last X hours.                                                                          | Check Door 1, RFID reader, lighting, cabling, blockage, or system freeze.                    |
| Hourly System Check      | No Session (X hours)           | No session performed in the last X hours.                                                                                | Check corridor access, Door 1, RFID, and video footage for problems.                         |
| Hourly System Check      | Heartbeat Not Received         | The remote server did not receive the last heartbeat signal.                                                             | Check internet connection, Raspberry Pi status, or remote desktop access.                     |
| Subject Check            | Low Weight                     | Subject's weight is less than half its baseline.                                                                         | Verify scale calibration; examine animal health; check food/water.                            |
| Subject Check            | Low Water Intake (24h)         | Subject consumed less than the configured water threshold in the last 24 hours.                                          | Check water delivery, solenoid calibration, leaks, or clogging.                              |
| Subject Check            | No Detection (X hours)         | Subject has not been detected for X hours (active hours only).                                                           | Check RFID antennas, lighting, dirt, or cage connectivity.                                    |
| Subject Check            | No Session (X hours)           | Subject has not performed a session for X hours (active hours only).                                                     | Check corridor access, Door 1, RFID functionality, and behavior patterns.                     |
| Task Preparation Check   | Invalid subjects.csv           | Error reading subjects.csv due to formatting or missing values.                                                          | Fix CSV formatting, verify paths, correct missing values.                                     |
| Task Preparation Check   | Area4 Detection                | Unexpected pixels detected in Area 4, which should always be empty.                                                      | Check for dirt, lighting, stuck animals, or door malfunction.                                 |
| Task Preparation Check   | Error Launching Task           | Task could not be started due to code or hardware error.                                                                 | Inspect logs; debug task code; check device connections.                                      |
| Task Running Check       | Error Running Task             | Error occurred during task execution.                                                                                    | Inspect logs, hardware components, and restart the task.                                      |
| Task Running Check       | Min Time & Areas3-4 Detection  | Minimum task time elapsed but Areas 3–4 never cleared; Door 2 could not close.                                           | Check for a stuck subject, faulty door, or incorrect pixel threshold.                         |
| Task Running Check       | Wrong RFID Detection           | RFID detected in an invalid state — possible multiple animals in the corridor or subject mismatch.                        | Inspect corridor camera; verify RFIDs; adjust threshold; check door function.                |
| Task Running Check       | 2 Subjects in Box              | Pixel count suggests more than one animal entered the operant box.                                                       | Check camera for noise/dirt; adjust threshold; verify door control.                           |
| Task Running Check       | Subject in Prohibited Area     | Pixels detected in a restricted region.                                                                                  | Inspect video; adjust threshold or lighting; remove dirt.                                      |
| Post-Task Check          | Few Trials Completed           | Subject completed fewer trials than the configured minimum (or none).                                                    | Check task code, reward ports, sensors, and corridor video.                                   |
| Post-Task Check          | Large Dataframe                | Dataframe contains more than 100,000 rows, typically due to an abnormal high-frequency sensor event.                     | Inspect photogates, debounce settings, cable noise, or hardware malfunction.                  |
| Post-Task Check          | Subject in Box Too Long        | More than 1 hour has passed since task ended and the subject is still inside the box.                                    | Wake with Door 2 pulses or sound; inspect video; ensure exit path is clear.                   |




#### System Checks Performed Every Hour

These checks occur hourly and may trigger the following alarms:

- `Low Temperature`: The temperature has dropped below the configured threshold in [settings][SETTINGS].

- `High Temperature`: The temperature has exceeded the configured threshold in [settings][SETTINGS].

- `No Detection in 6h`: No animal has been detected by the RFID reader in the last 6 hours. This could indicate that the detection system is malfunctioning or that Door 1 is mistakenly closed.

- `No Session in 12h`: No animal has performed a session in the last 12 hours. This could indicate that the detection system is malfunctioning or that Door 1 is mistakenly closed.

- `Heartbeat Not Received`: The last heartbeat signal was not received. The system sends a heartbeat signal to an external server every hour. If the server does not receive the signal, it instructs the Telegram bot to send this alarm.

```{important}
 A missing heartbeat may result from a temporary internet outage, a power failure, or a system freeze.

In such cases, first attempt to connect remotely:
- If the system has restarted, simply relaunch Training Village.
- If the process is unresponsive, investigate the terminal error messages.
- If remote access fails, a physical check may be required to ensure the animals’ safety.
```

#### Subject Checks Performed Twice a Day

Whenever there is a transition between day and night, the system evaluates the state of the animals and generates a report containing the number of detections, sessions, water intake and average weight for all subjects.
A warning alarm is also sent if one or more subjects have a warning, with only the most critical warning shown for each subject.
Warnings are listed in order of severity, from least to most critical:

- `Low Weight`: The subject’s weight is less than half its baseline weight. Ensure there are no calibration or functionality problems with the scale.

- `Low Water Intake 24h`: The subject has consumed less than the configured water threshold in the last 24 hours. This threshold can be adjusted in [settings][SETTINGS].

- `No detection 12h`: The subject has not been detected by the RFID reader for the last 12 hours (considering only hours when the animal is active).

- `No session 24h`: The subject has not performed a session for the last 24 hours (considering only hours when the animal is active).

#### Checks Performed When a Subject is Detected, and the Task is Prepared

- `Invalid data in subjects.csv`: An error occurred while reading the subjects.csv file.

- `Area4 Detection`: Pixels are detected in Area 4, which should always be empty when the behavioral box is vacant. Check for dirt, lighting issues, or whether an animal has entered the corridor due to a malfunction (e.g., a faulty door).

- `Error Launching Task`: A problem in the task code prevents it from starting. The task is terminated, and the RFID reader is disabled.

#### Checks Performed While the Task is Running

- `Error Running Task`: An issue occurred during task execution, likely due to an error in the task code. The task is terminated, and the RFID reader is disabled.

- `Min Time & Areas3-4 Detection`: The minimum task time has elapsed, but Door 2 could not close because Areas 3 and 4 were never cleared. This could occur if the subject remained in the corridor without entering, there was a door malfunction allowing multiple animals into the corridor, or the pixel detection system was not functioning correctly. As a result, the task is terminated, and the RFID reader is disabled.

- `Wrong RFID Detection`: Two scenarios may trigger this alarm. In both cases, the task is terminated, and the RFID reader is disabled.
	1.	In the `RUN_CLOSED` state: RFID is detected when no animal should be in the corridor.
	2.	In `RUN_FIRST` or `RUN_OPENED` states: RFID is detected for an animal that is not performing the task, likely indicating two animals have entered the behavioral box..

- `2 Subjects in Box`: A high pixel count suggests multiple animals entered the behavioral box. Check remotely to determine if this is accurate or a false alarm caused by dirt or threshold misconfiguration.

- `Subject in Prohibited Area`: Pixels are detected in a restricted area. Verify if this is caused by an animal, dirt, or threshold issues.

```{important}
In certain critical situations, the task is terminated, and the RFID reader is disconnected to prevent other subjects from entering the behavioral box until the issue is resolved.

In these cases, the system waits for the subject currently in the box to exit and be weighed on the scale. Once this is completed, Door 2 is closed, and Door 1 is opened.

It is essential to connect remotely, verify that all animals are in the home cage, resolve the issue, and reactivate the RFID reader.
```

#### Checks Performed After the Task Finishes

- `Few Trials Completed`: This alarm is triggered if the subject completes fewer trials than the configured minimum (set in [settings][SETTINGS]). It will always trigger if no trials are completed, which may indicate an issue with the task code or hardware.

- `Large Dataframe`: The resulting dataframe contains over 100,000 rows, often caused by a malfunction (e.g., a photogate sending multiple signals per second).

- `Subject in Box Too Long`: An hour has passed since the task ended, and the subject remains inside the behavioral box. This usually indicates the subject fell asleep. The system attempts to wake the subject every 10 minutes by slightly opening and closing Door 2. You can also connect remotely to play a sound in the box to wake the animal.

```{important}
Always review videos corresponding to unusual alarms to identify the root cause, such as dirt, threshold issues, lighting errors, or hardware malfunctions.

To view a video:
1. Locate the alarm in `DATA` screen -> `EVENTS`.
2. Click the alarm row, then select `VIDEO` to watch the footage.

For common errors, such as multiple animals in the behavioral box or prolonged time inside, consult the [troubleshooting section][TROUBLE], which lists frequent issues and their solutions.
```

[SETTINGS]: /user_guide/GUI.md#settings
[TROUBLE]: /troubleshooting/troubleshooting.md
