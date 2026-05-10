"""
Override this class in your project to define functions triggered by softcodes
sent from the behavioral controller.

Example:
    class SoftcodeFunctions(SoftcodeFunctionsBase):
        def function1(self):
            self.task.water_valve.open()

        def function2(self):
            self.behaviour_window.show_image("reward.png")
"""

from village.custom_classes.task import Task


class DirectFunctionsBase:
    def __init__(self) -> None:
        self.task: Task = Task()
