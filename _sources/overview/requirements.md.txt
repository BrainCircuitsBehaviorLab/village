## System Requirements

Before installing a Training Village, make sure the following requirements can be
met.

### 1. Network & Internet

The Raspberry Pi must be connected to the internet: remote access, the Telegram
alarms, the heartbeat monitoring and the data synchronization with a server all
depend on it.

### 2. Remote Access

The institution must allow the use of a
[remote desktop system](../preparation/access.md) (e.g., VNC, X2Go, AnyDesk, or
TeamViewer), since the system needs to be controlled remotely.

### 3. Data Storage

An [external server or an external hard drive](../preparation/backup.md) must be
configured to store the data, since the SD card only supports up to 256 GB
(approximately one week of video).

### 4. Notifications

A [Telegram bot and a group chat](../preparation/telegram.md) (with the bot and the
lab members who must receive the alarms) must be created to receive automatic system
messages and alarms.

### 5. System Health Monitoring

A free account on [healthchecks.io](https://healthchecks.io/) is required: the system
sends it a signal every hour, and if the signals stop (power cut, no internet...) the
team is alerted ([how to set it up](../preparation/heartbeat.md)).

### 6. Animals

Every animal must be implanted with an RFID microchip, which the corridor reader uses
to identify it.

### 7. Lighting

Stable, uniform, and glare-free lighting is required in both the corridor and the
operant box. Illumination must be consistent to prevent video-tracking errors.

- **Corridor:** The system includes integrated visible and infrared (IR) lighting.
- **Operant Box:** Requires either visible or IR light depending on the experimental
  paradigm. The Box Board includes dedicated connectors for internal visible and IR
  lighting.

### 8. Calibrations

The [water valves](../calibrations/water.md) (and the
[speakers](../calibrations/sound.md), if the tasks use sound) must be calibrated before
the first task is run: tasks ask for volumes in microliters and sound levels in dB,
and the calibrations convert them into valve times and gains.

### 9. Data Format

The system uses a standardized data format. Existing analysis scripts may require
updates to maintain compatibility.

- **Behavioral Data:** Generated as one CSV file per session, structured with one row
  per trial, plus a raw CSV file with one row per event. The system automatically
  appends the sessions into a master **Global Subject CSV**, maintaining a continuous,
  complete longitudinal history of the animal's performance.
- **Tracking Data:** Generated as one CSV file per video. It logs precise camera frame
  numbers and timestamps alongside the subject's spatial detection coordinates (X and
  Y positions) for detailed trajectory and position analysis.
- **System Data:** Events, temperature and humidity, and a summary of all sessions,
  among others.

All the files are described in [Saved Data and Video](../system_operation/data.md).

### 10. Initial Adjustment Period

```{admonition} Monitor the system closely during the first days
:class: warning
During the first days, problems often arise: misconfigured detection areas, poorly
calibrated sensors, lighting issues, or animals reluctant to enter the box. For this
reason, it is essential to monitor the system every few hours until everything is
confirmed to be working correctly.
```

### 11. Alarm Monitoring

```{admonition} Alarms must be addressed within 24 hours
:class: warning
Telegram alarms must always be checked while the system is running (including
weekends if the animals are allowed to train on weekends). Some rare errors may cause
an animal to remain inside the operant box without access to water. Therefore, any
alarm must be addressed within 24 hours or less.
```
