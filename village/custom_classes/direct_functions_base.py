from village.custom_classes.task import Task
from village.devices.camera import cam_box
from village.devices.sound_device import sound_device


class DirectFunctionsBase:
    """
    Override this class in your project to define functions triggered directly.
    For example, you can trigger these functions from the behaviour controller, the
    camera trigger, or the GUI buttons.
    These functions can not accept arguments because they are triggered directly, but
    they can use self.task and then use some of the variables or settings of the
    task.

    Example:
        class DirectFunctions(DirectFunctionsBase):
            def function1(self):
                self.task.water_valve.open()

            def function2(self):
                self.task.screen.show_image("reward.png")

            def function3(self):
                self.
    """

    def __init__(self) -> None:
        self.task: Task = Task()
        print(cam_box)
        print(sound_device)
