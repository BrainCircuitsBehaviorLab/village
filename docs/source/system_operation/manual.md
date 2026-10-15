## Manual Task Execution

![Tasks Training Village screen](/_static/tasks_screen.webp)

To launch a task, navigate to the `TASKS` tab. If you have not yet created a new project,
you will be working within the `demo-village-project` by default. This project includes
several example tasks that cover a range of system functionalities.

### Demo Tasks

The following tasks are included. Note that some require additional hardware beyond
the Raspberry Pi itself.

**Requires a Bpod with 3 behavioral ports** (`BEHAVIOR_CONTROLLER` set to `BPOD`):
- The six training stages of *Follow the Light*, a 2AFC task in which the animal
  pokes the side port that lights up first: see
  [Task Examples (Bpod)](../examples/tasks_bpod.md).
- [bpod_area2_sound.py](../examples/bpod_area2_sound.md): entering box area 2 plays a
  sound and delivers water.
- [bpod_touchscreen.py](../examples/bpod_touchscreen.md): touching the rectangle that
  stays on screen gives water.
- Demos and tools, not training tasks:
  [bpod_global_timer.py](../examples/bpod_global_timer.md),
  [bpod_outputs_and_events.py](../examples/bpod_outputs_and_events.md)
  and [bpod_purge_ports.py](../examples/bpod_purge_ports.md) (to flush the water lines).

**Requires an Arduino** (`BEHAVIOR_CONTROLLER` set to `OTHER`):
- The same six stages of *Follow the Light*, each with its Arduino firmware: see
  [Task Examples (Arduino)](../examples/tasks_arduino.md).

**No external controller required** (`BEHAVIOR_CONTROLLER` set to `OTHER`):
- [raspberry_area1_sound.py](../examples/raspberry_area1_sound.md): entering box area 1
  plays a sound and lights an LED of the LED strip.
- [raspberry_touchscreen.py](../examples/raspberry_touchscreen.md): a menu of 6
  rectangles on the touchscreen, each one showing a different stimulus when touched.

**Training protocol** ([training_protocol.py](../examples/training_protocol.md)):
- Moves each subject through the six Bpod stages of *Follow the Light*, deciding the
  next task after every session.

---

### Launching a Task

The `TASKS` screen shows the active training protocol on the left, along with a list of
all available tasks. When you click on a task, its description (`self.info`) is
displayed, along with its settings, organized in the tabs defined by the training
protocol (see [The Training Protocol](../protocols/creating.md)). Two more fields are
shown:

- `maximum_number_of_trials`: The task will automatically end once this number of trials
  is completed. It only exists for manual runs: it is not a setting of the training
  protocol, it is not saved, and it has no effect on the sessions run automatically
  (to limit the trials in those, see
  [Stopping the task from your own logic](force-stop)).
- `maximum_duration`: The task will automatically end when this time is reached. Unlike
  the previous one, it is a setting of the training protocol, used in automatic
  sessions too.

You can optionally select a subject from the `Subject` selector, next to the `RUN TASK`
button, before running it:

- **No subject selected (`None`):** The task runs with the default settings defined in
  `training_protocol.py`. No data or video is saved.
- **Subject selected:** The task runs with the settings currently assigned to that
  subject. Once the session ends, the subject's settings are updated automatically by
  `training_protocol.py`.

```{warning}
When a subject is selected, the values you change before pressing `RUN TASK`
(`maximum_duration` or any other setting) are kept for that subject: they become its
settings for the next sessions, automatic ones included, unless
`update_training_settings()` reassigns them at the end of the session (see
[update_training_settings()](../protocols/creating.md#update_training_settings)).
```

Press `RUN TASK` to start.

---

### Testing the Training Protocol

Clicking `TEST THE TRAINING PROTOCOL` simulates what would happen if `training_protocol.py`
were applied to a specific subject right now, based on their existing session history.
The computed settings for the next session are displayed on screen.

This is intended as a validation tool: if you have modified `training_protocol.py`, you
can use this to verify that the updated code runs correctly against real subject data
without making any actual changes. The settings displayed are never saved or applied.
