## Requirements

**1. Remote Access:**
The institution must allow the use of a remote desktop system (e.g., VNC, X2Go, AnyDesk, or TeamViewer) as the system needs to be controlled remotely.

**2. Data Storage:**
An external server or an external hard drive must be configured to store the data, since the SD card only supports up to 256 GB (approximately one week of video).

**3. Notifications:**
A Telegram bot and channel must be created and configured to receive automatic system messages.

**4. System Health Monitoring:**
A health-check web page is required to continuously verify that the system is active and connected to the internet.

**5. Lighting:**
Stable, uniform, and glare-free lighting is required in both the corridor and the operant box. Illumination must be consistent to prevent video-tracking errors.

*   **Corridor:** The system includes integrated visible and infrared (IR) lighting.
*   **Operant Box:** Requires either visible or IR light depending on the experimental paradigm. The box hardware includes dedicated connectors for white LED strips and individual IR LEDs.

**6. Data Format:**
The system uses a standardized data format. Existing analysis scripts may require updates to maintain compatibility.

*   **Behavioral Data:** Generated as one CSV file per session, structured with one row per trial. The system automatically appends these session logs into a master **Global Subject CSV**, maintaining a continuous, complete longitudinal history of the animal's performance.
*   **Tracking Data:** Generated as one CSV file per session. It logs precise camera frame numbers and timestamps alongside the subject’s spatial detection coordinates (X and Y positions) for detailed trajectory and position analysis.

**7. Initial Adjustment Period:**
During the first days, problems often arise: misconfigured detection areas, poorly calibrated sensors, lighting issues, or animals reluctant to enter the box. For this reason, it is essential to monitor the system every few hours until everything is confirmed to be working correctly.

**8. Alarm Monitoring:**
Telegram alarms must always be checked while the system is running (including weekends if the animals are allowed to train on weekends). Some rare errors may cause an animal to remain inside the operant box without access to water. Therefore, any alarm must be addressed within 24 hours or less.


<br>
