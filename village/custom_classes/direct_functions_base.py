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

from typing import Any


class DirectFunctionsBase:
    def __init__(self) -> None:
        self.task: Any = None
        self.behaviour_window: Any = None
        self.sound_calibration: Any = None
        self.water_calibration: Any = None

    def set_variables(
        self,
        task: Any,
        behaviour_window: Any,
        sound_calibration: Any,
        water_calibration: Any,
    ) -> None:
        self.task = task
        self.behaviour_window = behaviour_window
        self.sound_calibration = sound_calibration
        self.water_calibration = water_calibration
