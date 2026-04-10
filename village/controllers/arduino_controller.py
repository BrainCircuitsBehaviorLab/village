from typing import Callable

from village.classes.enums import ControllerEnum
from village.controllers.controller import Controller


class ArduinoController(Controller):
    def __init__(self) -> None:
        super().__init__()

        self.type = ControllerEnum.ARDUINO
        self.check_connection()

    def check_connection(self):
        self.error = ""

    def connect(self, functions: list[Callable]) -> None:
        """Connects to the Arduino and initializes session.

        Args:
            functions (list[Callable]): List of callback functions for softcodes.
        """
        self.functions = functions
        self.connected = True
