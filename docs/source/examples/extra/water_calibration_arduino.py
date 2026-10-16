import struct
import time

import serial

from village.custom_classes.water_calibration_task_base import (
    WaterCalibrationTaskBase,
)
from village.scripts.time_utils import time_utils
from village.settings import settings

# Water calibration with an Arduino instead of Bpod.
#
# Copy this file to your project's code directory: the Water Calibration
# panel then runs this class instead of the built-in Bpod sequence. Keep only
# one WaterCalibrationTaskBase subclass in the project. The board must
# understand CMD_OPEN_VALVE, as the firmware of the Arduino examples does.
#
# Protocol (see openValve() in village_arduino/village_arduino.ino):
#
# Pi -> Arduino, 6 raw bytes, once per valve opening:
#   [CMD_OPEN_VALVE, port, time_us (uint32, little-endian)]
#   Opens the valve of that port (1-based) for time_us microseconds. The
#   Arduino times the opening itself, so the USB latency does not change
#   the volume delivered.
#
# Arduino -> Pi, 6 raw bytes, once the valve is closed again:
#   [EVENT_VALVE_CLOSED, port, elapsed_us (uint32, little-endian)]
#   elapsed_us is how long the valve was actually open.
CMD_OPEN_VALVE = 20
EVENT_VALVE_CLOSED = 4

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop gets re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes
STARTUP_WAIT = 2.0  # seconds; opening the port resets most Arduino boards
WAIT_BETWEEN_VALVES = 0.1  # seconds, as in the built-in Bpod sequence


class WaterCalibrationArduino(WaterCalibrationTaskBase):
    """The same sequence as the built-in Bpod one: every trial opens each
    valve in self.indices (0-based ports) for its time in self.times
    (seconds), one after the other. The panel creates the task with those
    lists and with maximum_number_of_trials set to the number of iterations,
    so __init__ is inherited unchanged."""

    def start(self):
        """Opens the serial connection to the Arduino."""

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        # Opening the port resets most Arduino boards: wait for the sketch
        # to be running, or the first command would be lost.
        time.sleep(STARTUP_WAIT)
        self.serial_port.reset_input_buffer()

    def create_trial(self):
        """Opens each valve for its time, waiting for the Arduino to report
        it closed before going on to the next one."""

        for index, valve_time in zip(self.indices, self.times, strict=False):
            if self.should_stop:
                return
            port = index + 1
            time_us = round(valve_time * 1_000_000)
            self.serial_port.write(struct.pack("<BBI", CMD_OPEN_VALVE, port, time_us))
            # The deadline is only a safety net for a lost message.
            self.wait_valve_closed(time_utils.now_timestamp() + valve_time + 1.0)
            time.sleep(WAIT_BETWEEN_VALVES)

    def wait_valve_closed(self, deadline):
        """Waits for EVENT_VALVE_CLOSED, the task to stop or the deadline."""

        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                continue  # nothing arrived within READ_TIMEOUT; keep waiting
            buffer += chunk
            if len(buffer) < MESSAGE_SIZE:
                continue
            event, _, _ = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            if event == EVENT_VALVE_CLOSED:
                return

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
