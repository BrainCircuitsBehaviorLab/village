## Toolbar Controls

The top bar of the GUI contains a set of buttons for performing the following actions. Depending on the current system state, you will see different buttons available.

### `CHANGE STATE`

Opens a dialog offering only the actions valid for the current state:

- While the system believes a subject is inside the box but it is not (e.g. a door did not close properly and the animal escaped back to the home cage without being detected), it offers **"All subjects are back home, go to WAIT state."**
- While the system is in the WAIT state, it offers **"Force data sync"** (forces an immediate synchronization, useful if the automatic sync did not run due to a connection failure, a network change, or any other issue) and **"Subject is inside the box"** (use this when the system believes there is no subject in the box but there is one — e.g. two mice entered the operant box simultaneously and the system detected one exiting, switching to WAIT while the other stayed inside).

### `STOP SYNC`

By default, the system synchronizes data with an external device or server after each session ends. While syncing, animals cannot be detected or enter the operant box. `STOP SYNC` stops the current synchronization — useful during testing to avoid waiting for a sync after each test run, since it will run automatically at the end of the next session. Once synchronization is complete (or stopped), the system returns to the WAIT state and animals can enter again.

### `STOP TASK`

Stops a running task. In automatic mode, pressing this button disconnects the RFID reader to prevent new animals from entering, and the system waits for the current animal to exit the box. If you remove the animal manually, use `CHANGE STATE` → "All subjects are back home, go to WAIT state" afterwards and re-enable the RFID reader.

### `ONLINE PLOTS`

Shows live plots while a task is running. The plots displayed are configurable by the user. Only enabled while a task is actually running.

### `CHECK MICE`

Confirms that the mice have been checked today. Turns orange until confirmed, either by clicking it or via the `/mice_checked` Telegram command; once confirmed, it shows `MICE OK` and stays disabled until the next reset, which happens at midnight. If the mice have not been checked by the time set in `SETTINGS` → `TELEGRAM SETTINGS` → `CHECK_MICE_TIME`, an alarm is triggered to remind you via Telegram.

### `ALARMS`

Shows the number of pending alarms and turns orange while any are pending. Clicking it acknowledges every pending alarm and stops their Telegram reminders.

### `EXIT`

Shuts down the system.
