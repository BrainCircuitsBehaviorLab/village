from village.custom_classes.task_base import TaskBase


class ScaleTriggerBase:
    """Base class for defining custom box scale behavior.

    While a task is running, the box scale (SCALE_BOX, only when USE_BOX_BOARD
    is ON) is read in its own thread every self.period seconds, and
    on_weight is called with every measurement. Override on_weight to react
    to it. The reading runs only while a task is active.

    on_weight runs in the scale reader thread, not in the task thread: keep it
    fast, the next reading waits until it returns.

    You have access to self.task, so any variable or function of the running
    task can be used.
    """

    def __init__(self) -> None:
        """Initializes the ScaleTriggerBase instance."""
        self.name = "Scale Trigger"
        self.task = TaskBase()
        # Seconds between readings. The scale gives ~10 new values per
        # second, so reading faster than 0.1 s just repeats values.
        self.period = 0.1

    def on_weight(self, weight: float, timestamp: float) -> None:
        """Called after every reading of the box scale. Override me.

        Args:
            weight (float): The weight in grams.
            timestamp (float): Raspberry timestamp of the reading, the same
                clock as time_utils.now_timestamp(), so it can be passed to
                self.task.register_raspberry_event.
        """
        pass
