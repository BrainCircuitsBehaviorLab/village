## Manual Task Execution

To launch a task, navigate to the `TASKS` tab. If you have not yet created a new project,
you will be working within the `demo-village-project` by default. This project includes
several example tasks that cover a range of system functionalities.

### Demo Tasks

The following tasks are included. Note that some require additional hardware beyond the
Raspberry Pi itself.

**No external hardware required:**
- A minimal task that performs no actions — useful as a blank template.
- A task that plays sounds when the subject enters a defined area.
- A task that presents stimuli on a touchscreen and waits for the subject's response.

**Requires Bpod with 3 behavioral ports:**
- A task that delivers water whenever the subject pokes any of the three ports.
- A task that plays a sound on a center poke and requires the subject to choose one of
  the two side ports.
- A task that presents a visual stimulus when the subject is detected within a circular
  region around a defined point.

**Requires Arduino:**
- A task that switches an LED on and off using Arduino.

**Training protocol** (`training_protocol.py`):
- The training protocol contains the following logic: TODO

---

### Launching a Task

Select a task from the list. You can optionally select a subject from the subject
selector before running it:

- **No subject selected (`None`):** The task runs with the default settings defined in
  `training_protocol.py`. No data or video is saved.
- **Subject selected:** The task runs with the settings currently assigned to that
  subject. Once the session ends, the subject's settings are updated automatically by
  `training_protocol.py`.

Press `RUN TASK` to start.

---

### Testing the Training Protocol

Clicking `TEST THE TRAINING PROTOCOL` simulates what would happen if `training_protocol.py`
were applied to a specific subject right now, based on their existing session history.
The computed settings for the next session are displayed on screen.

This is intended as a validation tool: if you have modified `training_protocol.py`, you
can use this to verify that the updated code runs correctly against real subject data
without making any actual changes. The settings displayed are never saved or applied.
