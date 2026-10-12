## Project Structure

### Project Folders

Training data and code are organized into projects. The project folder structure is
created automatically when a new project is initialized.

```text
village_projects/
└── projectName/
    ├── code/
    ├── media/
    └── data/
```

- **`code/`**: All executable Python scripts for tasks and training logic.
- **`media/`**: *(Optional)* Audio, video, or image assets used by behavioral tasks.
- **`data/`**: All experimental outputs — raw and processed data files and videos.

The first time you run the Training Village, a `demo-village-project` is created
automatically with working example code you can use as a reference (see
[Manual Task Execution](../system_operation/manual.md) for the list of its tasks).

---

### Code Organization

A training protocol consists of one or more Python task scripts plus a mandatory
`training_protocol.py` file. The training protocol runs automatically every time a
subject finishes a session and contains the logic to advance or regress the subject
through the training stages — changing tasks, adjusting parameters, or both.

#### Typical code structures

```
# Example 1: Multiple sequential tasks
code/
├── habituation.py
├── lick_teaching.py
├── simple_task.py
├── final_task.py
└── training_protocol.py
```

```
# Example 2: One task with progressive difficulty
code/
├── behavioral_task.py
└── training_protocol.py
```

In Example 1, each script corresponds to a distinct training stage:

1. `habituation` — animals get acquainted with the operant box.
2. `lick_teaching` — animals learn to interact with the behavioral ports.
3. `simple_task` — a simplified version of the final task.
4. `final_task` — the full experimental task.

In Example 2, a single task is used throughout, but `training_protocol.py` adjusts its
parameters after every session to increase difficulty progressively.

Both approaches can be combined freely. In addition to task scripts and the training
protocol, the `code/` folder can contain files that customize other parts of the system:
functions that produce sounds and visual stimuli, reactions to the camera, the
touchscreen or the GPIO pin, plots, actions run after each session... This is, for
example, the `code/` folder of the demo project (shortened):

```
code/
├── bpod_1_habituation.py ... bpod_6_delay.py    # tasks
├── arduino_1_habituation.py ... arduino_6_delay.py
├── raspberry_area1_sound.py, raspberry_touchscreen.py
├── training_protocol.py
├── direct_functions.py, sound_functions.py, video_functions.py
├── camera_trigger.py, camera_draw.py, touch_trigger.py
├── gpio_trigger.py, scale_trigger.py
├── online_plot.py, session_plot.py, subject_plot.py
├── after_session.py, change_cycle.py, telegram_commands.py
├── led_calibration.py, auto_follow_the_light.py
└── arduino_firmware/
```

```{admonition} File and class names
:class: tip
Except for tasks, the names of these files and classes are up to you: when Village
starts, it reads every `.py` file in `code/` and recognizes each class by the base class
it inherits from (`TrainingProtocolBase`, `CameraTriggerBase`, `OnlinePlotBase`...).
Only one class of each kind is used per project. Tasks are the exception, in the sense
that the class name is the name of the task. The other exception is
`sound_functions.py`, which must have exactly that name (see
[Direct Sound & Video Functions](functions.md)).
```
