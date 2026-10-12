## Custom GPIO Interaction

```{admonition} Note
:class: note
The input pin is `GPIO_IN` (BCM 26) and the output pin is `GPIO_OUT` (BCM 27); they
are fixed. See [GPIO](../system_operation/gpio.md) for what a GPIO pin is, the voltage
it works at, and how to wire one.
```

The system watches an input pin (`GPIO_IN`) while a task is running. Every time
it goes from OFF (low) to ON (high) the `trigger_on` method of `GpioTriggerBase`
is called; every time it goes from ON back to OFF, `trigger_off` is called. By
default both do nothing. You can override them to react to an external signal
(an optogenetics TTL, a lickometer, another box, ...).

```{admonition} Note
:class: note
The output pin (`GPIO_OUT`) is unrelated to the trigger and available at all
times — see [Using the output pin](../system_operation/gpio.md#using-the-output-pin).
```

---

### Creating a custom GpioTrigger

Create a file inside your project's `code` directory (e.g. `gpio_trigger.py`) and define
a class (e.g. `GpioTrigger`) that inherits from `GpioTriggerBase`. The file and class names are
up to you: the system detects the class by what it inherits from, and uses it
instead of the default base class. Only one such class is used per project.

```python
from village.custom_classes.gpio_trigger_base import GpioTriggerBase


class GpioTrigger(GpioTriggerBase):

    def __init__(self) -> None:
        super().__init__()

    def trigger_on(self) -> None:
        """Called when the input pin goes from OFF to ON.

        Available via self.task:
        - self.task.cam_box      — box camera (write_text, areas, position, …)
        - self.task.bpod         — Bpod controller (send_softcode_to_bpod, …)
        - self.task.gpio         — set_on()/set_off() for the output pin
        - any attribute defined in the task class
        """
        self.task.cam_box.write_text("GPIO: ON")
        self.task.bpod.send_softcode_to_bpod(1)

    def trigger_off(self) -> None:
        """Called when the input pin goes from ON to OFF."""
        self.task.cam_box.write_text("GPIO: OFF")
```

```{admonition} Note
:class: note
`trigger_on`/`trigger_off` run in the GPIO reader thread, not in the task
thread. Keep them fast and avoid blocking calls.
```

A complete example, which records the pin in the trial data of any task:
[gpio_trigger.py](../examples/gpio_trigger.md).

```{toctree}
:hidden:

GPIO Trigger Example <../examples/gpio_trigger.md>
```
