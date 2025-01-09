import traceback

import smbus2

from village.classes.protocols import TempSensorProtocol
from village.log import log
from village.settings import settings


class TempSensor(TempSensorProtocol):
    def __init__(self, address: str) -> None:
        self.I2C_ADDR = int(address, 16)
        self.bus = 1
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.start()

    def start(self) -> None:
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0x23, 0x34)

    def get_temperature(self) -> tuple[float, float, str]:
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0xE0, 0x0)
        data = self.i2cbus.read_i2c_block_data(self.I2C_ADDR, 0x0, 6)
        rawT = ((data[0]) << 8) | (data[1])
        rawR = ((data[3]) << 8) | (data[4])
        temp = -45 + rawT * 175 / 65535
        RH = 100 * rawR / 65535

        temp_string = "{:.2f}ºC".format(temp)
        RH_string = "{:.2f}%".format(RH)
        temp_RH_string = temp_string + " / " + RH_string

        return temp, RH, temp_RH_string


def get_temp_sensor(address: str) -> TempSensorProtocol:
    try:
        temp_sensor = TempSensor(address=address)
        log.info("Temp sensor successfully initialized")
        return temp_sensor
    except Exception:
        log.error("Could not initialize temp sensor", exception=traceback.format_exc())
        return TempSensorProtocol()


temp_sensor = get_temp_sensor(address=settings.get("TEMP_SENSOR_ADDRESS"))
