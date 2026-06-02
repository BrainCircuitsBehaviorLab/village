## Custom AutoNoMouse

`AutoNoMouseBase` is a base class for running tasks automatically without a real animal. It is useful for testing and debugging your task code — you can simulate nose pokes, update a virtual animal position, and inject mock trial data, all without needing a physical subject in the box.

If the system detects a class inheriting from `AutoNoMouseBase` in your `project/code` folder, it will use your custom class instead of the default base class.

Read the base class in `village/custom_classes/auto_no_mouse_base.py` to understand the full interface before subclassing it.

---

### Creating a Custom AutoNoMouse Class

Your class should be declared as follows:

```python
from village.custom_classes.auto_no_mouse_base import AutoNoMouseBase

class AutoNoMouse(AutoNoMouseBase):
    """Automated task execution without a real animal."""

    def __init__(self) -> None:
        super().__init__()

    def run_trial(self) -> None:
        """Sequence of actions for one trial."""
        self.poke(port=1, duration=0.1)
        self.wait(1.0)
```

---

### Available Methods

Override or call these methods in your subclass:

- **`run_trial()`**: Called once per trial. Define the sequence of actions the virtual animal performs — pokes, position updates, waits. Override this in your subclass.
- **`inject_trial(p_correct_left, p_correct_right)`**: Appends a mock trial row directly to the session dataframe, bypassing the Bpod state machine. Useful for injecting synthetic data.
- **`inject_trials(n, p_correct_left, p_correct_right)`**: Calls `inject_trial` *n* times.
- **`poke(port, duration)`**: Simulates a nose-poke in and out on the given Bpod port.
- **`set_position(x, y)`**: Updates the virtual animal's position and trace, as seen by the camera tracking system.
- **`wait(seconds)`**: Pauses execution for the given duration, stopping early if the session is halted.
