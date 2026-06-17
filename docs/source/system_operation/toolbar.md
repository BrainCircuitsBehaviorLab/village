## Toolbar Controls

The top bar of the GUI contains a set of buttons for performing the following actions. The available actions change dynamically depending on the current system state.

### Sync Buttons

By default, the system synchronizes data with an external device or server after each session ends. While syncing, animals cannot be detected or enter the operant box. Once synchronization is complete, the system returns to WAIT state and animals can enter again.

- **`STOP SYNC`**: Stops the current synchronization. Useful during testing to avoid waiting for a sync after each test run — the sync will run automatically at the end of the next session.
- **`FORCE SYNC`**: Forces an immediate synchronization. Useful if the automatic sync did not run due to a connection failure, a network change, or any other issue.

### Task Running

- **`ONLINE PLOTS`**: Shows live plots while a task is running. The plots displayed are configurable by the user.
- **`STOP TASK`**: Stops a running task. In automatic mode, pressing this button disconnects the RFID reader to prevent new animals from entering, and the system waits for the current animal to exit the box. If you remove the animal manually, press GO TO WAIT STATE afterwards and re-enable the RFID reader.

### Manually Changing States

- **`GO TO WAIT STATE`**: Use this when the system believes a subject is inside the box but it is not. This can happen if a door does not close properly and the animal escapes back to the home cage without the system detecting it.
- **`SUBJECT IN BOX`**: Use this when the system believes there is no subject in the box (WAIT state) but there is one. This can happen if two mice enter the operant box simultaneously and the system detects one exiting, switching to WAIT state while the other is still inside.

### Exit

- **`EXIT`**: Shuts down the system.
