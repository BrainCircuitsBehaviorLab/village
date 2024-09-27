"""
inspired by:
https://github.com/DFRobot/DFRobot_HX711_I2C
"""

import struct
import time
from typing import Any, Literal

import smbus2


class DFRobot_HX711_I2C(object):
    I2C_ADDR = 0x64  # I2C device address
    REG_DATA_GET_RAM_DATA = 0x66  # Get sensor raw data
    REG_DATA_GET_CALIBRATION = 0x67  # Gets the automatic calibration value
    REG_DATA_SET_CALIBRATION = 0x68  # Obtain peeling position
    REG_DATA_GET_PEEL_FLAG = 0x69  # Module initialization
    REG_SET_CAL_THRESHOLD = 0x71  # Set the calibration trigger threshold
    REG_SET_TRIGGER_WEIGHT = 0x72  # Set calibration weight

    rxbuf = [0, 0, 0, 0]
    _calibration = 2210.0
    _offset = 0.0

    def __init__(self, bus, address) -> None:
        self.i2cbus = smbus2.SMBus(bus)
        self._addr = address
        self.idle = 0

    def begin(self) -> None:
        self._offset = self.average(20)
        time.sleep(0.05)

    def read_weight(self, times) -> Any | float:
        value = self.average(times)
        time.sleep(0.05)
        ppFlag = self.peel_flag()
        if ppFlag == 1:
            self._offset = self.average(times)
        elif ppFlag == 2:
            b = self.get_calibration()
            self._calibration = b[0]
        return (value - self._offset) / self._calibration

    def get_calibration(self) -> tuple[Any, ...]:
        data = self.read_reg(self.REG_DATA_GET_CALIBRATION, 4)
        aa = bytearray(data)
        return struct.unpack(">f", aa)

    def set_calibration(self, value) -> None:
        self._offset = self.average(15)
        self._calibration = value

    def peel_flag(self) -> Literal[1] | Literal[2] | Literal[0]:
        data = self.read_reg(self.REG_DATA_GET_PEEL_FLAG, 1)
        if data[0] == 0x01 or data[0] == 129:
            return 1
        elif data[0] == 0x02:
            return 2
        else:
            return 0

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

    def set_cal_weight(self, triWeight) -> None:
        txData = [0, 0]
        txData[0] = triWeight >> 8
        txData[1] = triWeight & 0xFF
        self.write_data(self.REG_SET_TRIGGER_WEIGHT)
        self.write_data(txData[0])
        self.write_data(txData[1])
        time.sleep(0.05)

    def set_threshold(self, threshold) -> None:
        txData = [0, 0]
        txData[0] = threshold >> 8
        txData[1] = threshold & 0xFF
        self.write_data(self.REG_SET_CAL_THRESHOLD)
        self.write_data(txData[0])
        self.write_data(txData[1])
        time.sleep(0.05)

    def peel(self) -> None:
        self._offset = self.average(15)
        self.write_data(0x73)

    def enable_cal(self) -> None:
        time.sleep(0.1)
        self.write_data(0x74)
        time.sleep(0.1)

    def get_cal_flag(self) -> bool:
        ppFlag = self.peel_flag()
        if ppFlag == 2:
            return True
        else:
            return False

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

    def write_data(self, data) -> None:
        self.i2cbus.write_byte(self._addr, data)

    def write_reg(self, reg, data) -> None:
        self.i2cbus.write_byte(self._addr, reg)
        self.i2cbus.write_byte(self._addr, data)

    def read_reg(self, reg, len) -> list[int]:
        self.i2cbus.write_byte(self._addr, reg)
        time.sleep(0.03)
        for i in range(len):
            time.sleep(0.03)
            self.rxbuf[i] = self.i2cbus.read_byte(self._addr)
        return self.rxbuf


scale = DFRobot_HX711_I2C(1, 0x64)
print("begin")
scale.begin()
print("get_calibration")
scale.get_calibration()
print("read_weight")
value = scale.read_weight(5)
print("value: ", value)


# class Scale:
#     def __init__(self) -> None:
#         self.calibration: float = 4.0
#         self.weight: float = 0.0

#     def get(self) -> float:
#         return self.weight


# scale = Scale()
