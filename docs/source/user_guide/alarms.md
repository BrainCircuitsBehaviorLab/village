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

- `Low Water Intake 24h`
- `No detection 24h`
- `No session 24h`

---

## Alarms
The system is designed to cover all potential scenarios, resulting in an extensive list of alarms. While many may never appear, some occur rarely but are critical.

---

# **System Alarms**

```{list-table} System Alarms
:widths: 20 50 30
:header-rows: 1

* - **Alarm**
  - **Description**
  - **Solution**

* - Invalid data in subjects.csv
  - Error reading *subjects.csv*: malformed rows, inconsistent number of columns, stray spaces or line breaks.
  - Verify file integrity: ensure consistent columns per row and remove extra whitespace. Fix or recreate if needed.

* - Detection in area4 when it should be empty
  - Pixels detected in Area 4 when the box is empty and RFID detection occurs.
  - Check lighting, clean corridor, remove objects, or review video for door or threshold malfunction.

* - Error running task
  - A task execution error occurred (exception in the task code).
  - Inspect event logs and traceback to identify the problematic line.

* - Wrong RFID detection
  - Caused by: (1) a different subject detected during another subject’s task; or (2) the correct subject detected in the corridor while door 2 was closed.
  - Review corridor videos for door malfunction, threshold errors, lighting issues, or multi-animal entry.

* - Maximum time reached and areas 3 or 4 were never empty
  - Door 2 could not close because areas 3–4 never cleared before maximum task duration.
  - Check lighting, clean corridor, ensure subject did not fall asleep, and review videos for malfunction.

* - The subject has been in the box for too long
  - More than 1 hour passed since the task ended and the subject remains inside.
  - Verify via video if asleep. Confirm scale and servo motors operate correctly to allow exit.
