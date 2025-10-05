import struct
import time
import traceback
from typing import List

import numpy as np
import smbus2

from village.classes.abstract_classes import ScaleBase
from village.log import log
from village.scripts import time_utils
from village.settings import settings


class Scale(ScaleBase):
    def __init__(self, address: str) -> None:
        self.I2C_ADDR = int(address, 16)
        self.REG_DATA_GET_RAM_DATA = 0x00  # Get sensor raw data
        self.bus = 1
        self.calibration: float = float(settings.get("SCALE_CALIBRATION_VALUE"))
        self.offset = 0.0
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.error_message_timer = time_utils.Timer(3600)
        self.i2cbus.write_i2c_block_data(self.I2C_ADDR, 0x01, [0x8C, 0x03])
        self.alarm_timer = time_utils.Timer(3600)
        self.tare()

    # @time_utils.measure_time
    def tare(self) -> None:
        try:
            self.offset = self.get_value(samples=5)
            log.info("The scale has been tared.")
        except Exception:
            log.error("Error taring scale", exception=traceback.format_exc())

    def calibrate(self, weight: float) -> None:
        try:
            raw_value: float = self.get_value(samples=5)
            if raw_value < 1:
                log.error("Error calibrating scale", exception=traceback.format_exc())
                return
            new_calibration = (raw_value - self.offset) / weight
            if new_calibration <= 0:
                log.error("Error calibrating scale", exception=traceback.format_exc())
                return
            self.calibration = new_calibration
            settings.set("SCALE_CALIBRATION_VALUE", new_calibration)
            settings.set("SCALE_WEIGHT_TO_CALIBRATE", weight)

        except Exception:
            log.error("Error calibrating scale", exception=traceback.format_exc())

    def get_value(self, samples: int = 1, interval_s: float = 0.005) -> int:
        values: List[int] = []
        for i in range(samples):
            data = self.i2cbus.read_i2c_block_data(
                self.I2C_ADDR, self.REG_DATA_GET_RAM_DATA, 2
            )
            v = struct.unpack(">h", bytes(data))[0]
            values.append(v)
            if interval_s > 0 and i < samples - 1:
                time.sleep(interval_s)
        median = int(np.median(values))
        if median == 0 and self.alarm_timer.has_elapsed():
            log.alarm("The scale is not working, please check the connection.")
        return median

    def get_weight(self) -> float:
        try:
            value = (self.get_value() - self.offset) / self.calibration
            return value if value >= -1 else -1.0

        except Exception:
            if self.error_message_timer.has_elapsed():
                log.error("Error getting weight", exception=traceback.format_exc())
            return 0.0


def get_scale(address: str) -> ScaleBase:
    try:
        scale = Scale(address=address)
        log.info("Scale successfully initialized")
        return scale
    except Exception:
        log.error("Could not initialize scale", exception=traceback.format_exc())
        return ScaleBase()


scale = get_scale(settings.get("SCALE_ADDRESS"))


def real_weight_inference(weight_array, threshold) -> tuple[bool, float]:
    """
    Conditions to call it a real weight:
     - standard deviation of the last 5 measurements is
        smaller than 10% of the threshold
    """
    if len(weight_array) < 8:
        return (False, 0.0)

    median_weight = np.median(weight_array[-5:])
    std_weight = np.std(weight_array[-5:])

    if std_weight < 0.1 * threshold or len(weight_array) > 100:
        return (True, median_weight)
    else:
        return (False, 0.0)
