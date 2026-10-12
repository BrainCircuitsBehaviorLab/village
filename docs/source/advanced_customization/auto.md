## Custom AutoNoMouse

`AutoNoMouseBase` is a base class for running tasks automatically without a real animal. It is useful for testing and debugging your task code — you can simulate nose pokes, update a virtual animal position, and inject mock trial data, all without needing a physical subject in the box.

Each virtual animal is a class that inherits from `AutoNoMouseBase`, written in any
file of your project's `code` folder. Its `TASK_NAME` says which task it is for (the
task's class name), so a project can have one for each task. A class without
`TASK_NAME` is used for any task that has no virtual animal of its own.

It is started and stopped from the `VIRTUAL MOUSE` tab of the `MONITOR` screen while the
task is running, where its parameters (`PARAMS`) can also be changed. The same tab can
inject simulated trials directly into the session data, without running the task's
state machine, to fill a session quickly and test the plots or the training protocol.

Read the base class in `village/custom_classes/auto_no_mouse_base.py` to understand the full interface before subclassing it.

---

### Creating a Custom AutoNoMouse Class

```python
from village.custom_classes.auto_no_mouse_base import AutoNoMouseBase, AutonomouseParam


class MyVirtualAnimal(AutoNoMouseBase):
    """Automated task execution without a real animal."""

    TASK_NAME = "Bpod1Habituation"  # the task it is for

    # Parameters shown (and editable) in the VIRTUAL MOUSE tab:
    # name, type, default, label, min, max, tooltip
    PARAMS = [AutonomouseParam("pause", float, 1.0, "pause (s)", 0.0, 10.0)]

    def run_trial(self) -> None:
        """Sequence of actions for one trial."""
        self.poke(port=1, duration=0.1)
        self.wait(self.pause)
```

A complete example, for the delay task of the demo project:
[auto_follow_the_light.py](../examples/auto_follow_the_light.md).

---

### Available Attributes and Methods

Define these in your subclass:

- **`TASK_NAME`**: The class name of the task it is for. Leave it empty for any task.
- **`PARAMS`**: A list of `AutonomouseParam` (name, type, default, label, minimum,
  maximum, tooltip). Each one becomes an attribute (`self.<name>`) and a control in the
  `VIRTUAL MOUSE` tab.
- **`run_trial()`**: Called over and over while the virtual animal runs, once per trial.
  Define the sequence of actions the virtual animal performs — pokes, position updates,
  waits. `self.task` is the running task, so it can read what the task decided for the
  trial (e.g. the correct side).
- **`inject_trial(**params)`**: Appends one simulated trial row directly to the session
  data (`self.task.session_df`), bypassing the state machine. It receives the current
  values of `PARAMS`.

And call these:

- **`inject_trials(n, interval=1.0, **params)`**: Calls `inject_trial` *n* times, one every
  `interval` seconds.
- **`poke(port, duration=0.1)`**: Simulates a nose-poke in and out on the given Bpod port
  (only with Bpod).
- **`set_position(x, y)`**: Updates the virtual animal's position and trace, as seen by
  the camera tracking system.
- **`wait(seconds)`**: Pauses execution for the given duration, stopping early if the
  virtual animal is stopped.

```{toctree}
:hidden:

AutoNoMouse Example <../examples/auto_follow_the_light.md>
```
