## The Training Protocol

The purpose of the training protocol is to move the subjects forward through their
training. It is a class named `TrainingProtocol` that inherits from
`TrainingProtocolBase`, in a file named `training_protocol.py` inside your `code/`
folder, and it must define three methods:

- `__init__`, which only needs to call `super().__init__()`.
- `default_training_settings`, which sets the settings a subject has by default when
  it is created.
- `update_training_settings`, which runs after every session and updates the settings
  of the subject, for example to move it to the next stage.

A fourth method, `define_gui_tabs`, is optional.

The code on this page is taken from the training protocol of the example tasks
([training_protocol.py](../examples/training_protocol.md)), which moves each subject
through the six Bpod stages of *Follow the Light*, a 2AFC task, from habituation to a
delay discrimination task.

### Creating the class

```python
from village.custom_classes.training_protocol_base import TrainingProtocolBase


class TrainingProtocol(TrainingProtocolBase):
    """Moves each subject through the 6 Bpod training stages of Follow the Light,
    a 2AFC task in which the animal pokes the side port that lights up first,
    one after another:
    Bpod1Habituation -> Bpod2Passive -> Bpod3Active -> Bpod4CenterInitiated ->
    Bpod5IntroducePenalty -> Bpod6Delay
    """

    def __init__(self) -> None:
        """Required. It only needs to call super().__init__()."""
        super().__init__()
```

---

### `default_training_settings()`

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

```python
def default_training_settings(self) -> None:
    # Required parameters
    self.settings.next_task = "Bpod1Habituation"
    self.settings.refractory_period = 4 * 60 * 60  # 4 hours between sessions
    self.settings.minimum_duration = 10 * 60
    self.settings.maximum_duration = 15 * 60  # habituation lasts 15 min

    # Task-specific parameters (for bpod_1..6 or arduino 1..6, read the respective
    # task code to understand their usage)
    self.settings.reward_volume = 2  # microliters
    self.settings.reward_volume_large = 6  # microliters
    self.settings.led_intensity = 255  # 0-255
    self.settings.led_on_time = 5 * 60  # seconds
    self.settings.c_led_on_time = 5 * 60  # seconds
    self.settings.iti_time = 1  # seconds
    self.settings.timeout = 5  # seconds
    self.settings.noise_time = 1.5  # seconds
    self.settings.p = 0.0
    self.settings.curve_power = 3
    self.settings.delay_thresholds = {
        0: 0.75,
        0.1: 0.65,
        0.25: 0.50,
        0.5: 0.25,
        1: 0.001,
        40: 0.0,
    }
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
tasks.

```{admonition} The type of each setting comes from its default value
:class: note
The settings are saved as text (in `subjects.csv`, or typed in the GUI) and converted
back with the type of their default value. A setting whose default is a decimal
number (`noise_time = 1.5`) is always a `float`. One whose default is an integer
(`led_intensity = 255`) is an `int`, so it can be used in `range()` or as an index;
if it is given a value with decimals (`reward_volume = 2.5`), that value is kept as a
`float`, never truncated. So write as decimals the defaults of the settings that are
decimal by nature, like times or volumes, if your code needs them to be `float`.
```

---

### `update_training_settings()`

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


The first three stages of the example protocol show the usual kinds of criteria, from
the simplest to the most complete:

```python
def update_training_settings(self) -> None:
    if self.last_task == "Bpod1Habituation":
        # If the session we just completed is habituation, move to the next task.
        self.settings.next_task = "Bpod2Passive"
        self.settings.minimum_duration = 25 * 60
        self.settings.maximum_duration = 45 * 60

    elif self.last_task == "Bpod2Passive":
        # At least 2 passive sessions, and 100 trials in the last two.
        df2 = self.df[self.df["task"] == "Bpod2Passive"]
        sessions = df2["session"].unique()
        n_sessions = len(sessions)
        last_2_sessions = sessions[-2:]
        df2_last_2 = df2[df2["session"].isin(last_2_sessions)]
        trials_last_2_sessions = df2_last_2.shape[0]

        if n_sessions >= 2 and trials_last_2_sessions >= 100:
            self.settings.next_task = "Bpod3Active"
            self.settings.minimum_duration = 25 * 60
            self.settings.maximum_duration = 45 * 60

    elif self.last_task == "Bpod3Active":
        # At least 2 active sessions, and in the last two: 100 trials and
        # 70% of them correct.
        df3 = self.df[self.df["task"] == "Bpod3Active"]
        sessions = df3["session"].unique()
        n_sessions = len(sessions)
        last_2_sessions = sessions[-2:]
        df3_last_2 = df3[df3["session"].isin(last_2_sessions)]
        trials_last_2_sessions = df3_last_2.shape[0]
        correct_last_2_sessions = (df3_last_2["outcome"] == "correct").mean()

        if (
            n_sessions >= 2
            and trials_last_2_sessions >= 100
            and correct_last_2_sessions >= 0.70
        ):
            self.settings.next_task = "Bpod4CenterInitiated"
            self.settings.minimum_duration = 30 * 60
            self.settings.maximum_duration = 45 * 60
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

```python
def update_training_settings(self) -> None:
    # ... stages 1 to 5 ...
    elif self.last_task == "Bpod6Delay":
        # Last stage: the subject stays here. The next session starts from
        # the difficulty p reached in this one, minus 0.05.
        last_session = self.df["session"].max()
        df_last_session = self.df[self.df["session"] == last_session]
        p_values = df_last_session["p"].dropna()
        if len(p_values) > 0:
            p_next = max(float(p_values.iloc[-1]) - 0.05, 0.0)
            self.settings.p = round(p_next, 2)

    # Any other task was run manually: next_task is left as it was.
```

Any other task (one run manually, outside the progression) does not match any branch,
so `next_task` is left as it was. The complete protocol is in
[training_protocol.py](../examples/training_protocol.md).

---

### `define_gui_tabs()` *(optional)*

If your protocol has many variables, this method lets you organize them into named tabs
in the GUI panel that appears when launching a task manually. Variables not assigned to
any tab are placed in a default **General** tab. You can also use the reserved `"Hide"`
tab name to suppress a variable from the GUI entirely.

```python
def define_gui_tabs(self) -> None:
    """Optional. Groups the settings into tabs in the panel shown when a
    task is launched manually. Settings not listed in any tab go to the
    General tab, and a tab named "Hide" hides the settings listed in it.
    gui_tabs_restricted limits a setting to a list of values (shown as a
    dropdown); this protocol does not need it.
    """
    self.gui_tabs = {
        "Reward": [
            "reward_volume",
            "reward_volume_large",
        ],
        "Timing": [
            "led_intensity",
            "led_on_time",
            "c_led_on_time",
            "iti_time",
            "timeout",
            "noise_time",
        ],
        "Delay task (stage 6)": [
            "p",
            "curve_power",
            "delay_thresholds",
        ],
        "Touchscreen demo": [
            "long_duration",
            "short_duration",
        ],
    }
    self.gui_tabs_restricted = {}
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

To check a protocol against real data without changing anything, use the
`TEST THE TRAINING PROTOCOL` button of the `TASKS` screen (see
[Manual Task Execution](../system_operation/manual.md#testing-the-training-protocol)): it
shows the settings the protocol would compute for a subject's next session, without
saving them.

```{toctree}
:hidden:

Training Protocol Example <../examples/training_protocol.md>
```
