from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any

from gpiozero import DigitalInputDevice, DigitalOutputDevice

from village.scripts.log import log
from village.settings import settings

if TYPE_CHECKING:
    from village.custom_classes.gpio_trigger_base import GpioTriggerBase


class Gpio:
    """Controls two GPIO pins: one input and one output.

    Both work at the same time, since they are different pins (set by the
    GPIO_IN and GPIO_OUT settings, in DEVICE ADDRESSES):

    - Input (GPIO_IN, default 27): while a task is running the pin is watched
      and self.trigger.trigger_on() is called when it goes from OFF (low) to
      ON (high), and self.trigger.trigger_off() when it goes from ON to OFF.
      The watching runs only while a task is active (the manager starts it
      when the task starts and stops it when it ends). See GpioTriggerBase to
      customize what happens on trigger_on/trigger_off.

    - Output (GPIO_OUT, default 26): set_on() drives the pin HIGH and set_off()
      drives it LOW. Call them from anywhere (a task, a trigger, direct
      functions, the screen sync...); they work regardless of the input.
    """

    def __init__(self) -> None:
        """Initializes the Gpio instance (does not open the GPIO yet)."""
        self.name = "Gpio"
        self.pin_in = int(settings.get("GPIO_IN"))  # BCM number, input
        self.pin_out = int(settings.get("GPIO_OUT"))  # BCM number, output
        self.error = ""
        self.trigger: GpioTriggerBase | None = None
        self._input: Any = None
        self._output: Any = None

    def start(self) -> None:
        """Starts watching the input pin for level changes."""
        if self._input is not None:
            return
        try:
            self._input = DigitalInputDevice(self.pin_in)
            self._input.when_activated = self._trigger_on  # OFF -> ON
            self._input.when_deactivated = self._trigger_off  # ON -> OFF
        except Exception:
            msg = "Could not open GPIO pin " + str(self.pin_in) + " as input"
            self.error = log.clean_text(traceback.format_exc(), msg)

    def stop(self) -> None:
        """Stops watching the input pin and releases it."""
        if self._input is not None:
            try:
                self._input.close()
            except Exception:
                pass
            self._input = None

    def set_on(self) -> None:
        """Drives the output pin HIGH."""
        self._write(True)

    def set_off(self) -> None:
        """Drives the output pin LOW."""
        self._write(False)

    def _write(self, high: bool) -> None:
        if self._output is None:
            try:
                self._output = DigitalOutputDevice(self.pin_out)
            except Exception:
                msg = "Could not open GPIO pin " + str(self.pin_out) + " as output"
                self.error = log.clean_text(traceback.format_exc(), msg)
                return
        if high:
            self._output.on()
        else:
            self._output.off()

    def _trigger_on(self) -> None:
        if self.trigger is not None:
            self.trigger.trigger_on()

    def _trigger_off(self) -> None:
        if self.trigger is not None:
            self.trigger.trigger_off()


gpio = Gpio()
