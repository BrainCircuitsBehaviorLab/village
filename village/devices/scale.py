"""
inspired by:
https://github.com/DFRobot/DFRobot_HX711_I2C
"""

import time
import traceback
from typing import Any

import smbus2

from village.classes.protocols import ScaleProtocol
from village.log import log
from village.settings import settings


class Scale(ScaleProtocol):

    def __init__(self, address: str) -> None:
        self.I2C_ADDR = int(address, 16)
        self.REG_DATA_GET_RAM_DATA = 0x66  # Get sensor raw data
        self.rxbuf = [0, 0, 0, 0]
        self.bus = 1
        self.calibration = settings.get("SCALE_CALIBRATION_VALUE")
        self.offset = 0.0
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.tare()

    # @time_utils.measure_time
    def tare(self) -> None:
        self.offset = self.average(5)

    def calibrate(self, weight: float) -> None:
        raw_value = self.get_weight() * self.calibration
        new_calibration = raw_value / weight
        self.calibration = new_calibration
        settings.set("SCALE_CALIBRATION_VALUE", new_calibration)

    # @time_utils.measure_time
    def get_weight(self) -> Any | float:
        value = self.average(1)
        return abs((value - self.offset) / self.calibration)

    def get_weight_string(self) -> str:
        weight = self.get_weight()
        return "{:.2f} g".format(weight)

    def get_value(self) -> int:
        data = self.read_reg(self.REG_DATA_GET_RAM_DATA, 4)
        value = 0
        if data[0] == 0x12:
            value = data[1]
            value = (value << 8) | data[2]
            value = (value << 8) | data[3]
        else:
            return 0
        return value ^ 0x800000

    def average(self, times) -> Any | float:
        sum = 0
        for i in range(times):
            data = self.get_value()
            if data == 0:
                times = times - 1
            else:
                sum = sum + data
        if times == 0:
            times = 1
        return float(sum) / times

    def read_reg(self, reg, len) -> list[int]:
        self.i2cbus.write_byte(self.I2C_ADDR, reg)
        time.sleep(0.03)
        for i in range(len):
            time.sleep(0.03)
            self.rxbuf[i] = self.i2cbus.read_byte(self.I2C_ADDR)
        return self.rxbuf


def get_scale(address: str) -> ScaleProtocol:
    try:
        scale = Scale(address=address)
        log.info("Scale successfully initialized")
        return scale
    except Exception:
        log.error("Could not initialize bpod", exception=traceback.format_exc())
        return ScaleProtocol()


scale = get_scale(settings.get("SCALE_ADDRESS"))
