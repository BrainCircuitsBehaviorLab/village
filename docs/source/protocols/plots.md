## Custom Plotting

Village provides three plot classes you can subclass to add custom visualizations.
Each one is triggered at a different point in the data lifecycle:

| Class | When it runs | Data available |
|---|---|---|
| `OnlinePlotBase` | During the session, in the window opened with `ONLINE PLOTS` | Current session trials so far |
| `SessionPlotBase` | With `PLOT` on a session of `DATA` → `SESSIONS_SUMMARY` | Full session CSV |
| `SubjectPlotBase` | With `PLOT` on a subject of the `SUBJECTS` screen | All sessions for that subject |

Create a file anywhere inside your project's `code` directory and define a subclass of
the base class (e.g. `OnlinePlot` in `online_plot.py`; the file and class names are up to
you). The system detects it automatically at startup and uses it instead of the
default. Only one subclass of each base class is used per project.

---

### OnlinePlotBase

`OnlinePlotBase` lets you monitor the session in real time. The plot is shown in a
separate window, opened with the `ONLINE PLOTS` button of the toolbar, and updated when
new trials have finished (at most every `UPDATE_TIME_TABLE` seconds).

Override two methods:

- **`create_figure_and_axes()`** — called once when the figure is first needed.
  Create `self.fig` and any axes you need (store them as instance attributes).
- **`update_plot(df)`** — called when the plot is updated, with the growing session DataFrame.
  Clear and redraw your axes here.

```{admonition} Note
:class: note
Do not call `plt.show()` or `fig.savefig()` — the figure is managed by the GUI.
Always clear the axes at the start of `update_plot` to avoid stacking traces.
```

**`df` columns** (one row per completed trial, grows after each trial):

*Fixed columns (always present)*

- `trial` — trial number (1-based integer).
- `date` — session start timestamp string.
- `subject` — subject name.
- `task` — task class name.
- `system_name` — name of the Village system.
- `TRIAL_START` / `TRIAL_END` — absolute timestamps of the start and end of the trial.
- `ordered_list_of_events` — event names in the order they occurred.

*State and event columns*

- One column per state (`STATE_<name>_START` / `STATE_<name>_END`) and per event
  (e.g. `Port1In`, `Port1Out`, `Tup`, ...): the ones Bpod records automatically, or the
  ones the task registers itself without Bpod. Each cell is a **list** of the
  timestamps of that trial (see `self.trial_data` in [Tasks (Bpod)](tasks_bpod.md)).

The saved session file (and so the `df` of `SessionPlotBase`) also has `run_mode`
(`"Manual"` or `"Auto"`) and `session` (the session index within the subject's
history), added when the session is saved; the online `df` doesn't.

*Custom columns*

Any value registered with `self.register_value(name, value)` inside `after_trial`
appears as an additional column.

**Example** — plot accuracy and reaction time trial by trial:

```python
from village.custom_classes.online_plot_base import OnlinePlotBase

class OnlinePlot(OnlinePlotBase):

    def create_figure_and_axes(self) -> None:
        import matplotlib.pyplot as plt
        self.fig, (self.ax_acc, self.ax_rt) = plt.subplots(
            2, 1, figsize=(10, 6), sharex=True
        )
        self.fig.tight_layout(pad=2)

    def update_plot(self, df) -> None:
        self.ax_acc.clear()
        self.ax_rt.clear()

        if df.empty or "correct" not in df.columns:
            return

        self.ax_acc.plot(df["trial"], df["correct"].rolling(10).mean(), color="steelblue")
        self.ax_acc.set_ylabel("Accuracy (10-trial rolling mean)")
        self.ax_acc.set_ylim(0, 1)

        if "response_time" in df.columns:
            self.ax_rt.plot(df["trial"], df["response_time"], "o", color="salmon", ms=4)
            self.ax_rt.set_ylabel("Response time (s)")
            self.ax_rt.set_xlabel("Trial")
```

---

### SessionPlotBase

`SessionPlotBase` produces a static figure shown in the GUI when the user clicks on
a finished session in the Sessions table.

Override **`create_plot(df, weight, width, height)`** and return a `matplotlib.figure.Figure`.

**Arguments:**

- `df` — the full session CSV as a DataFrame. Same columns as `OnlinePlotBase.df`
  (see above) plus `run_mode` and `session`, with all trials already present.
- `weight` — body weight of the subject at the time of the session (float, grams).
  `0.0` if not recorded.
- `width`, `height` — figure size in inches requested by the GUI.

**Example** — plot trial outcome over time with body weight in the title:

```python
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from village.custom_classes.session_plot_base import SessionPlotBase

class SessionPlot(SessionPlotBase):

    def create_plot(self, df, weight, width=10, height=8) -> Figure:
        fig, ax = plt.subplots(figsize=(width, height))

        if "correct" in df.columns:
            ax.plot(df["trial"], df["correct"].rolling(10).mean(), color="steelblue")
            ax.set_ylabel("Accuracy (10-trial rolling mean)")
            ax.set_ylim(0, 1)

        title = f"Session — {df['task'].iloc[0]}"
        if weight:
            title += f"  |  weight: {weight:.1f} g"
        ax.set_title(title)
        ax.set_xlabel("Trial")
        return fig
```

---

### SubjectPlotBase

`SubjectPlotBase` produces a static figure shown when the user clicks on a subject
in the Subjects table. It has access to the subject's full history across all sessions.

Override **`create_plot(df, summary_df, width, height)`** and return a `matplotlib.figure.Figure`.

**Arguments:**

- `df` — all trials for this subject, concatenated across sessions. Same trial-level
  columns as above, plus a `session` column (integer, 1-based) that identifies which
  session each trial belongs to.
- `summary_df` — one row per session for this subject, from `sessions_summary.csv`.
  Columns:

  | Column | Description |
  |--------|-------------|
  | `date` | Session start timestamp |
  | `subject` | Subject name |
  | `tag` | RFID tag |
  | `weight` | Body weight (g) at session start |
  | `task` | Task name |
  | `duration` | Session duration in seconds |
  | `trials` | Number of completed trials |
  | `water` | Water delivered (µL) |
  | `settings` | JSON string of the settings used |

- `width`, `height` — figure size in inches.

**Example** — accuracy per session and weight evolution:

```python
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from village.custom_classes.subject_plot_base import SubjectPlotBase

class SubjectPlot(SubjectPlotBase):

    def create_plot(self, df, summary_df, width=10, height=8) -> Figure:
        fig, (ax_acc, ax_w) = plt.subplots(2, 1, figsize=(width, height), sharex=True)

        if "correct" in df.columns:
            acc = df.groupby("session")["correct"].mean()
            ax_acc.plot(acc.index, acc.values, "o-", color="steelblue")
            ax_acc.set_ylabel("Mean accuracy per session")
            ax_acc.set_ylim(0, 1)

        if not summary_df.empty and "weight" in summary_df.columns:
            ax_w.plot(
                range(1, len(summary_df) + 1),
                summary_df["weight"].values,
                "s-",
                color="salmon",
            )
            ax_w.set_ylabel("Weight (g)")
            ax_w.set_xlabel("Session")

        fig.suptitle(df["subject"].iloc[0])
        fig.tight_layout()
        return fig
```
