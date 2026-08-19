from __future__ import annotations

import traceback
from typing import Any

from gpiozero import DigitalInputDevice, DigitalOutputDevice

from village.classes.enums import GpioDirection
from village.custom_classes.task_base import TaskBase
from village.scripts.log import log
from village.settings import settings


class GpioBase:
    """Base class for using GPIO pin 27, either as an input or as an output.

    The direction is set by the GPIO27_DIRECTION setting (advanced settings):

    - IN (default): a background thread watches the pin and calls trigger_on
      when it goes from OFF (low) to ON (high), and trigger_off when it goes
      from ON to OFF. Override those two methods to react. set_on/set_off do
      nothing in this mode.

    - OUT: the pin is driven as an output. set_on() puts it HIGH and set_off()
      puts it LOW; call them from anywhere (a task, a trigger, direct
      functions, the screen sync...). start/stop do nothing in this mode, and
      the triggers never fire.

    You have access to self.task, so any variable or function of the running
    task can be used. The input watching runs only while a task is active (the
    manager starts it when the task starts and stops it when it ends).
    """

    def __init__(self) -> None:
        """Initializes the GpioBase instance (does not open the GPIO yet)."""
        self.name = "Gpio"
        self.task = TaskBase()
        self.pin = 27  # BCM number of the GPIO pin
        self.direction: GpioDirection = settings.get("GPIO27_DIRECTION")
        self.error = ""
        self._input: Any = None
        self._output: Any = None

    def start(self) -> None:
        """Starts watching the pin for level changes. Only in IN mode."""
        if self.direction != GpioDirection.IN or self._input is not None:
            return
        try:
            self._input = DigitalInputDevice(self.pin)
            self._input.when_activated = self.trigger_on  # OFF -> ON
            self._input.when_deactivated = self.trigger_off  # ON -> OFF
        except Exception:
            msg = "Could not open GPIO pin " + str(self.pin) + " as input"
            self.error = log.clean_text(traceback.format_exc(), msg)

    def stop(self) -> None:
        """Stops watching the pin and releases it. Only affects IN mode."""
        if self._input is not None:
            try:
                self._input.close()
            except Exception:
                pass
            self._input = None

    def set_on(self) -> None:
        """Drives the pin HIGH. Does nothing unless the pin is set to OUT."""
        self._write(True)

    def set_off(self) -> None:
        """Drives the pin LOW. Does nothing unless the pin is set to OUT."""
        self._write(False)

    def _write(self, high: bool) -> None:
        if self.direction != GpioDirection.OUT:
            return
        if self._output is None:
            try:
                self._output = DigitalOutputDevice(self.pin)
            except Exception:
                msg = "Could not open GPIO pin " + str(self.pin) + " as output"
                self.error = log.clean_text(traceback.format_exc(), msg)
                return
        if high:
            self._output.on()
        else:
            self._output.off()

    def trigger_on(self) -> None:
        """Called when the GPIO goes from OFF to ON (IN mode). Override me."""
        pass

    def trigger_off(self) -> None:
        """Called when the GPIO goes from ON to OFF (IN mode). Override me."""
        pass
