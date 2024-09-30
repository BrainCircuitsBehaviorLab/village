from typing import Tuple

import smbus2


class TempSensor:
    def __init__(self) -> None:
        self.I2C_ADDR = 0x45  # I2C device address
        self.bus = 1
        self.i2cbus = smbus2.SMBus(self.bus)
        self.start()

    def start(self) -> None:
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0x23, 0x34)

    def get_temperature(self) -> Tuple[float, float]:
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0xE0, 0x0)
        data = self.i2cbus.read_i2c_block_data(self.I2C_ADDR, 0x0, 6)
        rawT = ((data[0]) << 8) | (data[1])
        rawR = ((data[3]) << 8) | (data[4])
        temp = -45 + rawT * 175 / 65535
        RH = 100 * rawR / 65535
        return temp, RH

    def get_temperature_string(self) -> str:
        temp, RH = self.get_temperature()
        temp_string = "{:.2f}ºC".format(temp)
        RH_string = "{:.2f}%".format(RH)
        return temp_string + " / " + RH_string


temp_sensor = TempSensor()
