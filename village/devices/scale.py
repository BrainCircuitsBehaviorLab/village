"""
inspired by:
https://github.com/DFRobot/DFRobot_HX711_I2C
"""

import time
import traceback

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
        self.calibration: float = float(settings.get("SCALE_CALIBRATION_VALUE"))
        self.ratio: float = float(settings.get("WEIGHT_DEVIATION_RATIO"))
        self.offset = 0.0
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.tare()

    # @time_utils.measure_time
    def tare(self) -> None:
        try:
            self.offset = self.average(5)[0]
            log.info("The scale has been tared.")
        except Exception:
            log.error("Error taring scale", exception=traceback.format_exc())

    def calibrate(self, weight: float) -> None:
        try:
            raw_value: float = self.average(5)[0]
            if raw_value < 1:
                log.error("Error calibrating scale", exception=traceback.format_exc())
                return
            new_calibration = (raw_value - self.offset) / weight
            self.calibration = new_calibration
            settings.set("SCALE_CALIBRATION_VALUE", new_calibration)
            settings.set("SCALE_WEIGHT_TO_CALIBRATE", weight)

        except Exception:
            log.error("Error calibrating scale", exception=traceback.format_exc())

    def get_weight_string(self) -> str:
        weight = self.get_weight()
        return "{:.2f} g".format(weight)

    def get_weight(self) -> float:
        try:
            value, correct = self.average(5)
            if correct:
                return abs((value - self.offset) / self.calibration)
            else:
                return 0.0
        except Exception:
            log.error("Error getting weight", exception=traceback.format_exc())
            return 0.0

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

    def average(self, times: int) -> tuple[float, bool]:
        weights: list[float] = []
        for i in range(times):
            weights.append(self.get_value())
        weights = [x for x in weights if x != 0]
        average = sum(weights) / len(weights)
        variance = sum([((x - average) ** 2) for x in weights]) / len(weights)
        sd: float = variance**0.5
        correct = (sd / average) < self.ratio
        return average, correct

    def read_reg(self, reg: int, len: int) -> list[int]:
        self.i2cbus.write_byte(self.I2C_ADDR, reg)
        time.sleep(0.1)
        for i in range(len):
            time.sleep(0.1)
            self.rxbuf[i] = self.i2cbus.read_byte(self.I2C_ADDR)
        return self.rxbuf


def get_scale(address: str) -> ScaleProtocol:
    try:
        scale = Scale(address=address)
        log.info("Scale successfully initialized")
        return scale
    except Exception:
        log.error("Could not initialize scale", exception=traceback.format_exc())
        return ScaleProtocol()


scale = get_scale(settings.get("SCALE_ADDRESS"))
