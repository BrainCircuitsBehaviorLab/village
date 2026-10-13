## Manual Task Execution

To launch a task, navigate to the `TASKS` tab. If you have not yet created a new project,
you will be working within the `demo-village-project` by default. This project includes
several example tasks that cover a range of system functionalities.

### Demo Tasks

The following tasks are included; each one links to its code and explanation. Note that
some require additional hardware beyond the Raspberry Pi itself.

**No external controller required** (`BEHAVIOR_CONTROLLER` set to `OTHER`):
- [raspberry_area1_sound.py](../examples/raspberry_area1_sound.md): entering box area 1
  plays a sound and lights an LED of the LED strip.
- [raspberry_touchscreen.py](../examples/raspberry_touchscreen.md): a menu of 6
  rectangles on the touchscreen, each one showing a different stimulus when touched.

**Requires a Bpod with 3 behavioral ports** (`BEHAVIOR_CONTROLLER` set to `BPOD`):
- The six training stages, from
  [bpod_1_habituation.py](../examples/bpod_1_habituation.md) to
  [bpod_6_delay.py](../examples/bpod_6_delay.md): habituation, passive and active
  learning, center-initiated trials, penalty for the wrong side, and a delay task whose
  difficulty adapts to the animal.
- [bpod_area2_sound.py](../examples/bpod_area2_sound.md): entering box area 2 plays a
  sound and delivers water.
- [bpod_touchscreen.py](../examples/bpod_touchscreen.md): touching the rectangle that
  stays on screen gives water.
- Demos and tools, not training tasks:
  [bpod_example_global_timer.py](../examples/bpod_example_global_timer.md),
  [bpod_example_outputs_and_events.py](../examples/bpod_example_outputs_and_events.md)
  and [bpod_purge_ports.py](../examples/bpod_purge_ports.md) (to flush the water lines).

**Requires an Arduino** (`BEHAVIOR_CONTROLLER` set to `OTHER`):
- The same six training stages, run by an Arduino, from
  [arduino_1_habituation.py](../examples/arduino_1_habituation.md) to
  [arduino_6_delay.py](../examples/arduino_6_delay.md), each with its Arduino firmware.

**Training protocol** ([training_protocol.py](../examples/training_protocol.md)):
- Moves each subject through the six Bpod training stages, one after another, deciding
  the next task after every session from the subject's performance. The other tasks are
  run manually and don't change the subject's next task.

See [Task Examples (Bpod)](../examples/tasks_bpod.md),
[Task Examples (Arduino)](../examples/tasks_arduino.md) and
[Task Examples (Raspberry Pi only)](../examples/tasks_raspberry.md) for a summary of
each one.

---

### Launching a Task

![Tasks Training Village screen](/_static/tasks_screen.webp)

The `TASKS` screen shows the active training protocol on the left, along with a list of
all available tasks. When you click on a task, its description (`self.info`) is
displayed, along with its settings, organized in the tabs defined by the training
protocol (see [The Training Protocol](../protocols/creating.md)). Two more settings are
added for manual runs:

- `maximum_number_of_trials`: The task will automatically end once this number of trials
  is completed.
- `maximum_duration`: The task will automatically end when this time is reached.

You can optionally select a subject from the `Subject` selector, next to the `RUN TASK`
button, before running it:

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
