"""
inspired by:
https://github.com/DFRobot/DFRobot_HX711_I2C
"""

import traceback

import smbus2

from village.classes.protocols import ScaleProtocol
from village.log import log
from village.scripts import time_utils
from village.settings import settings
import numpy as np


class Scale(ScaleProtocol):
    def __init__(self, address: str) -> None:
        self.I2C_ADDR = int(address, 16)
        self.REG_DATA_GET_RAM_DATA = 0x00  # Get sensor raw data
        self.bus = 1
        self.calibration: float = float(settings.get("SCALE_CALIBRATION_VALUE"))
        self.deviation: float = float(settings.get("WEIGHT_DEVIATION"))
        self.offset = 0.0
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.error_message_timer = time_utils.Timer(settings.get("ALARM_REPEAT_TIME"))
        self.i2cbus.write_i2c_block_data(self.I2C_ADDR, 0x01, [0x8C, 0x03])
        self.tare()

    # @time_utils.measure_time
    def tare(self) -> None:
        try:
            self.offset = self.get_value()
            log.info("The scale has been tared.")
        except Exception:
            log.error("Error taring scale", exception=traceback.format_exc())

    def calibrate(self, weight: float) -> None:
        try:
            raw_value: float = self.get_value()
            if raw_value < 1:
                log.error("Error calibrating scale", exception=traceback.format_exc())
                return
            new_calibration = (raw_value - self.offset) / weight
            self.calibration = new_calibration
            settings.set("SCALE_CALIBRATION_VALUE", new_calibration)
            settings.set("SCALE_WEIGHT_TO_CALIBRATE", weight)

        except Exception:
            log.error("Error calibrating scale", exception=traceback.format_exc())

    def get_value(self) -> int:
        data = self.i2cbus.read_i2c_block_data(
            self.I2C_ADDR, self.REG_DATA_GET_RAM_DATA, 2
        )
        return (data[0] << 8) | data[1]

    def get_weight(self) -> float:
        try:
            print("------")
            print(self.get_value())
            print(self.offset)
            print(self.calibration)
            value = (self.get_value() - self.offset) / self.calibration
            return value if value >= 0 else 0.0

        except Exception:
            if self.error_message_timer.has_elapsed():
                log.error("Error getting weight", exception=traceback.format_exc())
            return 0.0


def get_scale(address: str) -> ScaleProtocol:
    try:
        scale = Scale(address=address)
        log.info("Scale successfully initialized")
        return scale
    except Exception:
        log.error("Could not initialize scale", exception=traceback.format_exc())
        return ScaleProtocol()


scale = get_scale(settings.get("SCALE_ADDRESS"))


def real_weight_inference(weight_array, threshold):
    """
    Conditions to call it a real weight:
     - minimum of 5 measurements
     - median larger than threshold
     - standard deviation of the last 3 measurements is
        smaller than 10% of the threshold
    """
    if len(weight_array) < 5:
        return False
    
    median_weight = np.median(weight_array[-5:])
    std_weight = np.std(weight_array[-3:])
    
    if median_weight > threshold and std_weight < 0.1 * threshold:
        return True
    else:
        return False