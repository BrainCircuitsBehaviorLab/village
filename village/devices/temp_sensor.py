import traceback

import smbus2

from village.classes.abstract_classes import TempSensorBase
from village.scripts.log import log
from village.settings import settings


class TempSensor(TempSensorBase):
    """Interface for a temperature and humidity sensor via I2C.

    Attributes:
        I2C_ADDR (int): The I2C address.
        bus (int): The I2C bus number.
        i2cbus (smbus2.SMBus): The I2C bus connection.
        error (str): Error message.
    """

    def __init__(self, address: str) -> None:
        """Initializes the TempSensor.

        Args:
            address (str): The I2C address as a hex string.
        """
        self.I2C_ADDR = int(address, 16)
        self.bus = 1
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.start()

    def start(self) -> None:
        """Configures the sensor to start measurement."""
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0x23, 0x34)

    def get_temperature(self) -> tuple[float, float, str]:
        """Reads temperature and humidity from the sensor.

        Returns:
            tuple[float, float, str]: A tuple containing temperature (float),
                                      humidity (float), and a formatted string (str).
        """
        self.i2cbus.write_byte_data(self.I2C_ADDR, 0xE0, 0x0)
        data = self.i2cbus.read_i2c_block_data(self.I2C_ADDR, 0x0, 6)
        rawT = ((data[0]) << 8) | (data[1])
        rawR = ((data[3]) << 8) | (data[4])
        temp = -45 + rawT * 175 / 65535
        RH = 100 * rawR / 65535
        temp = round(temp, 2)
        RH = round(RH, 2)

        temp_string = "{:.2f}ºC".format(temp)
        RH_string = "{:.2f}%".format(RH)
        temp_RH_string = temp_string + " / " + RH_string

        log.info("temperature and humidity: " + temp_RH_string)
        log.temperature(temp, RH)

        return temp, RH, temp_RH_string


def get_temp_sensor(address: str) -> TempSensorBase:
    """Factory function to initialize the TempSensor.

    Args:
        address (str): The I2C address.

    Returns:
        TempSensorBase: An initialized TempSensor or base class on failure.
    """
    try:
        temp_sensor = TempSensor(address=address)
        log.info("Temp sensor successfully initialized")
        return temp_sensor
    except Exception:
        log.error("Could not initialize temp sensor", exception=traceback.format_exc())
        return TempSensorBase()


temp_sensor = get_temp_sensor(address=settings.get("TEMP_SENSOR_ADDRESS"))
