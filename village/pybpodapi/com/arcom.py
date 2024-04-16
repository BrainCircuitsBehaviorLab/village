import logging
import struct

import numpy as np
import serial

logger = logging.getLogger(__name__)


class DataType(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __str__(self):
        return self.name


class ArduinoTypes(object):
    BYTE = DataType("byte", 1)
    CHAR = DataType("char", 1)
    UINT8 = DataType("uint8", 1)
    INT16 = DataType("int16", 2)
    UINT16 = DataType("uint16", 2)
    UINT32 = DataType("uint32", 4)
    UINT64 = DataType("uint64", 8)
    FLOAT32 = DataType("float32", 4)
    FLOAT64 = DataType("float64", 8)

    @staticmethod
    def get_array(array, dtype):
        if dtype == ArduinoTypes.CHAR or dtype == ArduinoTypes.UINT8:
            return ArduinoTypes.get_uint8_array(array)
        elif dtype == ArduinoTypes.UINT16:
            return ArduinoTypes.get_uint16_array(array)
        elif dtype == ArduinoTypes.UINT32 or dtype == ArduinoTypes.FLOAT:
            return ArduinoTypes.get_uint32_array(array)
        else:
            return None

    @staticmethod
    def get_uint8_array(array):
        print("my_array ", array, str(ArduinoTypes.UINT8))
        return np.array(array, dtype=str(ArduinoTypes.UINT8)).tobytes()

    @staticmethod
    def get_int16_array(array):
        return np.array(array, dtype=str(ArduinoTypes.INT16)).tobytes()

    @staticmethod
    def get_uint16_array(array):
        return np.array(array, dtype=str(ArduinoTypes.UINT16)).tobytes()

    @staticmethod
    def get_uint32_array(array):
        return np.array(array, dtype=str(ArduinoTypes.UINT32)).tobytes()

    @staticmethod
    def get_float(value):
        return struct.pack("<f", value)

    @staticmethod
    def cvt_float32(message_bytes):
        return struct.unpack("<f", message_bytes)[0]

    @staticmethod
    def cvt_float64(message_bytes):
        return struct.unpack("<d", message_bytes)[0]

    @staticmethod
    def cvt_int64(message_bytes):
        return int.from_bytes(message_bytes, byteorder="little")

    @staticmethod
    def cvt_uint32(message_bytes):
        return struct.unpack("<L", message_bytes)[0]

    @staticmethod
    def cvt_uint64(message_bytes):
        return struct.unpack("<Q", message_bytes)[0]


class ArCOM(object):
    """
    ArCOM is an interface to simplify data transactions between Arduino and Python.
    """

    def open(self, serial_port, baudrate=115200, timeout=1):
        """
        Open serial connection
        :param serialPortName:
        :param baudRate:
        :return:
        """
        baudrate = 4000000
        print("en open", baudrate, timeout)
        self.serial_object = serial.Serial(
            serial_port, baudrate=baudrate, timeout=timeout
        )

        return self

    def close(self):
        """
        Close serial connection
        :return:
        """
        self.serial_object.close()

    def bytes_available(self):
        """

        :return:
        """
        try:
            return self.serial_object.inWaiting()
        except:  # noqa: E722
            print("Bpod connection ERROR. Check USB cable.")
            # return self.serial_object.inWaiting()

    ##############################################################
    ## WRITE #####################################################
    ##############################################################

    def write_char(self, value):
        self.serial_object.write(str.encode(value))

    def write_array(self, array):
        self.serial_object.write(array)

    ##############################################################
    ## READ BYTE #################################################
    ##############################################################

    def read_byte(self):
        message_bytes = self.serial_object.read(ArduinoTypes.BYTE.size)
        return message_bytes

    def read_char(self):
        message_bytes = self.serial_object.read(ArduinoTypes.CHAR.size)

        return message_bytes.decode("utf-8")

    def read_uint8(self):
        message_bytes = self.serial_object.read(ArduinoTypes.UINT8.size)
        # logger.debug("Read %s bytes: %s", len(message_bytes), message_bytes)
        message = int.from_bytes(message_bytes, byteorder="little")
        return message

    def read_uint16(self):
        message_bytes = self.serial_object.read(ArduinoTypes.UINT16.size)
        # logger.debug("Read %s bytes: %s", ArduinoTypes.UINT16.size, message_bytes)
        message = int.from_bytes(message_bytes, byteorder="little")
        return message

    def read_uint32(self):
        message_bytes = self.serial_object.read(ArduinoTypes.UINT32.size)
        # logger.debug("Read %s bytes: %s", ArduinoTypes.UINT32.size, message_bytes)
        message = int.from_bytes(message_bytes, byteorder="little")
        return message

    def read_uint64(self):
        message_bytes = self.serial_object.read(ArduinoTypes.UINT64.size)
        # logger.debug("Read %s bytes: %s", ArduinoTypes.UINT32.size, message_bytes)
        message = int.from_bytes(message_bytes, byteorder="little")
        return message

    def read_float32(self):
        message_bytes = self.serial_object.read(ArduinoTypes.FLOAT32.size)
        # logger.debug("Read %s bytes: %s", ArduinoTypes.UINT32.size, message_bytes)
        message = struct.unpack("<f", message_bytes)
        return message[0]

    ##############################################################
    ## READ ARRAY ################################################
    ##############################################################

    def read_bytes_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_byte()
            message_array.append(message_bytes)
        return message_array

    def read_char_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_char()
            message_array.append(message_bytes)

        return message_array

    def read_uint8_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_uint8()
            message_array.append(message_bytes)

        return message_array

    def read_uint16_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_uint16()
            message_array.append(message_bytes)

        return message_array

    def read_uint32_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_uint32()
            message_array.append(message_bytes)

        return message_array

    def read_float32_array(self, array_len=1):
        message_array = []
        for pos in range(0, array_len):
            message_bytes = self.read_float32()
            message_array.append(message_bytes)

        return message_array
