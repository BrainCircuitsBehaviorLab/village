## Protocol Creation

### Project Structure

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

1. `habituation` — animals get acquainted with the behavioral box.
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

---

### The Training Protocol

The training protocol must live in a file named exactly `training_protocol.py` inside
your `code/` folder. It defines a class called `TrainingProtocol` that inherits from
`TrainingProtocolBase`:

```python
from village.classes.training import TrainingProtocolBase

class TrainingProtocol(TrainingProtocolBase):
    """
    Defines the automated training logic for the project.

    Runs every time a session ends and determines:
    - Which task the subject will run next
    - How training parameters are updated based on performance
    - How long the subject must wait before its next session (refractory period)

    Required methods:
    - __init__
    - default_training_settings
    - update_training_settings

    Optional method:
    - gui_tabs
    """

    def __init__(self) -> None:
        super().__init__()
```

---

#### `default_training_settings()`

This method defines all training variables and their initial values. It is called once
when a new subject is created. The variables defined here are accessible from within
any task via `self.settings.<variable_name>`.

After creation, a subject's settings can be modified in three ways: manually from the
`SUBJECTS` tab or from the `TASKS` tab when launching a task manually; in real time from
within a running task; or automatically by `update_training_settings()` at the end of
each session.

```{admonition} Warning
:class: warning
`update_training_settings()` always starts from the settings the subject had at the
moment the session ended — including any values that were changed manually before or
during the session. Only the variables explicitly reassigned inside
`update_training_settings()` will be overwritten; all others will retain whatever value
they had when the session finished. Keep this in mind if you change a setting manually
and do not want it to persist: make sure `update_training_settings()` resets it
explicitly.
```

```python
    def default_training_settings(self) -> None:
        """
        Define all initial training parameters for new subjects.

        Required parameters:
        - next_task (str): Name of the first task the subject will run.
        - refractory_period (int): Seconds the subject must wait between sessions.
        - minimum_duration (int): Seconds before door 2 opens (subject may leave).
        - maximum_duration (int): Seconds before the task stops automatically.

        Any additional task-specific parameters can be defined below.
        """

        # Required parameters
        self.settings.next_task = "Habituation"
        self.settings.refractory_period = 3600 * 4   # 4 hours between sessions
        self.settings.minimum_duration = 600          # 10 min minimum session length
        self.settings.maximum_duration = 900          # 15 min maximum session length

        # Task-specific parameters
        self.settings.reward_amount_ml = 0.08
        self.settings.stage = 1
        self.settings.light_intensity_high = 255      # Port light intensity (0–255)
        self.settings.light_intensity_low = 50
        self.settings.trial_types = ["left_easy", "right_easy",
                                     "left_hard", "right_hard"]
        self.settings.punishment_time = 1             # seconds
        self.settings.iti_time = 2                    # inter-trial interval, seconds
        self.settings.response_time = 10              # seconds before timeout
```

`next_task` determines the first task run for a newly created subject. `refractory_period`
controls how long a subject must wait after finishing a session before it is allowed back
into the operant box — important in multi-animal setups to prevent individual animals from
monopolizing access. `minimum_duration` is when door 2 opens and the animal can choose to
leave; `maximum_duration` is when the task stops unconditionally and the system waits for
the animal to return home (door 2 is already open at this point, so
`maximum_duration` ≥ `minimum_duration` always).

---

#### `update_training_settings()`

This method runs automatically at the end of every session. It receives the subject's
full session history as a DataFrame and updates whichever settings should change based
on performance. The updated values are stored back into `subjects.csv` and used in the
subject's next session.

Available attributes:
- `self.subject` — name of the current subject
- `self.last_task` — name of the task that just finished
- `self.df` — DataFrame with all historical session data for this subject

```python
    def update_training_settings(self) -> None:

        if self.last_task == "Habituation":
            df_habituation = self.df[self.df["task"] == "Habituation"]

            if len(df_habituation) >= 2:
                trials_last_session = df_habituation.iloc[-1]["trial"].iloc[-1]

                if trials_last_session >= 100:
                    self.settings.next_task = "FollowTheLight"
                    self.settings.reward_amount_ml = 0.07

        elif self.last_task == "FollowTheLight":
            df_ftl = self.df[self.df["task"] == "FollowTheLight"]

            if len(df_ftl) >= 2:
                perf_last = df_ftl.iloc[-1]["correct"].mean()
                perf_prev = df_ftl.iloc[-2]["correct"].mean()
                trials_last = df_ftl.iloc[-1]["trial"].iloc[-1]
                trials_prev = df_ftl.iloc[-2]["trial"].iloc[-1]

                if (perf_last >= 0.85 and perf_prev >= 0.85 and
                        trials_last >= 100 and trials_prev >= 100):
                    self.settings.stage = 2
                    self.settings.reward_amount_ml = 0.05
```

---

#### `gui_tabs()` *(optional)*

If your protocol has many variables, this method lets you organize them into named tabs
in the GUI panel that appears when launching a task manually. Variables not assigned to
any tab are placed in a default **General** tab. You can also use the reserved `"Hide"`
tab name to suppress a variable from the GUI entirely.

You can additionally restrict the allowed values for any variable, which causes a
dropdown menu to appear instead of a free-text field.

```python
    def gui_tabs(self) -> None:

        self.gui_tabs = {
            "Port_variables": ["reward_amount_ml",
                               "light_intensity_high",
                               "light_intensity_low"],
            "Other_variables": ["stage",
                                "trial_types",
                                "punishment_time",
                                "iti_time",
                                "response_time"],
        }

        # Restrict allowed values — renders as a dropdown in the GUI
        self.gui_tabs_restricted = {
            "trial_types": ["left_easy", "right_easy", "left_hard", "right_hard"],
        }
```

---

### Summary

Every `TrainingProtocol` class must implement three methods:

| Method | When it runs | Purpose |
| :--- | :--- | :--- |
| `__init__` | At import | Initialize the class |
| `default_training_settings` | When a new subject is created | Define initial parameter values |
| `update_training_settings` | After every session ends | Update parameters based on performance |

The optional `gui_tabs` method controls how parameters are displayed when launching a
task manually from the GUI.
