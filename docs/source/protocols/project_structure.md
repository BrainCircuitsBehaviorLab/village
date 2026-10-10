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

The first time you run the Training Village, a `village-demo-project` is created
automatically with working example code you can use as a reference.

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
protocol, a typical `code/` folder contains helper modules for plotting, sound or video
generation, and direct hardware functions:

```
code/
├── __init__.py
├── habituation.py
├── follow_the_light.py
├── training_protocol.py
├── session_plot.py
├── subject_plot.py
├── online_plot.py
├── direct_functions.py
├── sound_functions.py
├── LICENSE
└── README.md
```
