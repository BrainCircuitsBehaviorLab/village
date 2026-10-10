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

---

### The Training Protocol

The training protocol must live in a file named exactly `training_protocol.py` inside
your `code/` folder. It defines a class called `TrainingProtocol` that inherits from
`TrainingProtocolBase`.

The code on this page is taken from the training protocol of the example tasks
([training_protocol.py](../examples/training_protocol.md)), which moves each subject
through six Bpod stages, from habituation to a delay discrimination task:

<!-- The code on this page is included from docs/source/examples/files/training_protocol.py,
selected by method name (pyobject) and by some lines of text (start-at / end-before).
If those lines change there, update them here too, and check the page: a block whose
text is not found can come out empty. -->

```{literalinclude} ../examples/files/training_protocol.py
:language: python
:end-before: "    def default_training_settings"
```

Every `TrainingProtocol` must define `default_training_settings` and
`update_training_settings`; `define_gui_tabs` is optional.

---

#### `default_training_settings()`

This method defines all training variables and their initial values. It is called once
when a new subject is created. The variables defined here are accessible from within
any task via `self.settings.<variable_name>`.

For example, you might have a variable like `delay` or `stim_size`. As training
progresses, these can be adjusted to fine-tune the difficulty of the task.

```{admonition} Warning
:class: warning
Every variable you want to use in your tasks must be defined here. This way, each
subject ends up with its own list of settings tied to its training. Every subject
starts out with these default values, and its settings change as training
progresses.
```

After creation, a subject's settings can be modified in three ways: manually from the
`SUBJECTS` tab or from the `TASKS` tab when launching a task manually; in real time from
within a running task; or automatically by `update_training_settings()` at the end of
each session.

```{literalinclude} ../examples/files/training_protocol.py
:language: python
:pyobject: TrainingProtocol.default_training_settings
:start-at: "# Required parameters"
:dedent: 8
```

The first four settings are required. `next_task` determines the first task run for a
newly created subject. `refractory_period` controls how long a subject must wait after
finishing a session before it is allowed back into the operant box — important in
multi-animal setups to prevent individual animals from monopolizing access.
`minimum_duration` is when door 2 opens and the animal can choose to leave;
`maximum_duration` is when the task stops unconditionally and the system waits for the
animal to return home (door 2 is already open at this point, so
`maximum_duration` ≥ `minimum_duration` always).

The rest are the settings your tasks read — here, the ones used by the six example
tasks (each task lists the ones it needs in its own code).

---

#### `update_training_settings()`

This method runs automatically at the end of every session. It looks at the subject's
history and updates whichever settings should change based on performance: typically
`next_task`, to move the subject to the next stage, and any setting that changes with
it. The updated values are stored back into `subjects.csv` and used in the subject's
next session.

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

Available attributes:
- `self.subject` — name of the current subject.
- `self.last_task` — name of the task that has just finished.
- `self.df` — every trial this subject has ever done, in all its sessions and tasks:
  **one row per trial**, including the session that has just finished. The
  `session` column tells the sessions apart (it is numbered per subject), the `task`
  column says which task each trial belongs to, and every value the tasks registered
  with `register_value` is a column too (`outcome`, `water`...).

Because `self.df` has one row per trial, a criterion like "100 trials in the last two
sessions" is computed by filtering rows:

- `df2 = self.df[self.df["task"] == "Bpod2Passive"]` — the trials of one task.
- `df2["session"].unique()` — its sessions, in order (so `[-2:]` are the last two).
- `df2[df2["session"].isin(last_2_sessions)]` — the trials of those sessions; its
  number of rows is the number of trials.
- `(df3_last_2["outcome"] == "correct").mean()` — the fraction of those trials whose
  `outcome` was `"correct"` (a value registered by the task in `after_trial`).

The first three stages of the example protocol show the usual kinds of criteria, from
the simplest to the most complete:

```{literalinclude} ../examples/files/training_protocol.py
:language: python
:pyobject: TrainingProtocol.update_training_settings
:start-at: if self.last_task == "Bpod1Habituation":
:end-before: elif self.last_task == "Bpod4CenterInitiated":
:dedent: 8
```

- **After habituation**, the subject always moves on: one session is enough.
- **After the passive stage**, it needs at least 2 sessions, and at least 100 trials
  between the last two.
- **After the active stage**, it also needs at least 70% of those trials to be correct.

When the subject moves on, the protocol sets the next task and the settings that change
with it (here, longer sessions). If the criterion is not met, nothing is changed, so
`next_task` stays the same and the subject repeats the stage. Stages 4 and 5 follow the
same pattern, with 200 trials, and stage 5 also turns on the penalty settings.

The last stage shows another use: carrying a value over from one session to the next.
The delay task adapts its difficulty `p` during the session and registers it in every
trial; the protocol makes the next session start from the last value, minus 0.05:

```{literalinclude} ../examples/files/training_protocol.py
:language: python
:pyobject: TrainingProtocol.update_training_settings
:start-at: elif self.last_task == "Bpod6Delay":
:dedent: 8
```

Any other task (one run manually, outside the progression) does not match any branch,
so `next_task` is left as it was. The complete protocol is in
[training_protocol.py](../examples/training_protocol.md).

---

#### `define_gui_tabs()` *(optional)*

If your protocol has many variables, this method lets you organize them into named tabs
in the GUI panel that appears when launching a task manually. Variables not assigned to
any tab are placed in a default **General** tab. You can also use the reserved `"Hide"`
tab name to suppress a variable from the GUI entirely.

```{literalinclude} ../examples/files/training_protocol.py
:language: python
:pyobject: TrainingProtocol.define_gui_tabs
:dedent: 4
```

You can additionally restrict the allowed values of a variable in
`self.gui_tabs_restricted`, which shows a dropdown menu instead of a free-text field.
The example protocol doesn't need it; it would look like this:

```python
self.gui_tabs_restricted = {
    "reward_side": ["left", "right", "both"],  # illustrative, not a real setting
}
```

---

### Summary

Every `TrainingProtocol` class implements these methods:

| Method | When it runs | Purpose |
| :--- | :--- | :--- |
| `__init__` | At import | Initialize the class |
| `default_training_settings` | When a new subject is created | Define initial parameter values |
| `update_training_settings` | After every session ends | Update parameters based on performance |
| `define_gui_tabs` *(optional)* | When the settings are shown in the GUI | Organize the settings into tabs |

```{toctree}
:hidden:

Training Protocol Example <../examples/training_protocol.md>
```
