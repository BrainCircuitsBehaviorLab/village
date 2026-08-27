from village.custom_classes.task_base import TaskBase


class GpioTriggerBase:
    """Base class for defining custom GPIO trigger behavior.

    Override trigger_on and trigger_off to react to the GPIO input pin
    (GPIO_IN, in DEVICE ADDRESSES) going from OFF (low) to ON (high) and back.
    The watching runs only while a task is active (the manager starts it when
    the task starts and stops it when it ends).

    You have access to self.task, so any variable or function of the running
    task can be used.
    """

    def __init__(self) -> None:
        """Initializes the GpioTriggerBase instance."""
        self.name = "Gpio Trigger"
        self.task = TaskBase()

    def trigger_on(self) -> None:
        """Called when the input pin goes from OFF to ON. Override me."""
        pass

    def trigger_off(self) -> None:
        """Called when the input pin goes from ON to OFF. Override me."""
        pass
