from village.custom_classes.gpio_trigger_base import GpioTriggerBase
from village.scripts.time_utils import time_utils


class GpioTrigger(GpioTriggerBase):
    """Records the input pin (GPIO_IN) in the trial data of any running task.

    Every time the pin goes ON, a "GpioOn" event is registered, and every time
    it goes back OFF, a "GpioOff" event. They are Raspberry Pi events, so they
    are saved with the Raspberry Pi clock whether or not the task uses a
    controller. Events that arrive between trials are not recorded.

    It works with any task, so an external signal (an optogenetics TTL, a
    lickometer, another box...) ends up in the data next to the task events
    without changing the task code. The change is also written on the box
    camera, so it shows up in the video.
    """

    def __init__(self) -> None:
        super().__init__()

    def trigger_on(self) -> None:
        self.task.register_raspberry_event("GpioOn", time_utils.now_timestamp())
        self.task.cam_box.write_text("GPIO: ON")

    def trigger_off(self) -> None:
        self.task.register_raspberry_event("GpioOff", time_utils.now_timestamp())
        self.task.cam_box.write_text("GPIO: OFF")
