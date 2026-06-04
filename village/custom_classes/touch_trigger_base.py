from village.custom_classes.task import Task


class TouchTriggerBase:
    """Base class for defining custom touch trigger behavior.

    Override this class to implement specific actions when a touch event
    is received on the touchscreen.

    You have access to self.task, so any variable or function defined in the
    task can be used to specify the actions to perform.
    """

    def __init__(self) -> None:
        """Initializes the TouchTriggerBase instance."""
        self.name = "Touch Trigger"
        self.task = Task()

    def trigger(self, x: int, y: int, timestamp: float) -> None:
        """Called whenever a touch event passes the debounce interval.

        Args:
            x (int): Touch x position in screen pixels.
            y (int): Touch y position in screen pixels.
            timestamp (float): Monotonic timestamp of the touch event (seconds).
        """
        self.task.cam_box.write_text(f"Touch: {x}, {y}")
