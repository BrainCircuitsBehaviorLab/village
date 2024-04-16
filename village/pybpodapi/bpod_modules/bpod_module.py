from pybpodapi.com.arcom import ArduinoTypes
from pybpodapi.exceptions.bpod_error import BpodErrorException


class BpodModule(object):
    def __init__(
        self,
        connected=False,
        module_name="",
        firmware_version=0,
        events_names=[],
        n_serial_events=0,
        serial_port=None,
    ):
        self.name = module_name
        self.serial_port = serial_port
        self.connected = connected
        self.firmware_version = firmware_version
        self.event_names = events_names
        self.n_serial_events = n_serial_events

        self.relay_active = False

        self.bpod_modules = None

    def __str__(self):
        return "{0} (connected: {1})(firmware: {2})".format(
            self.name, self.connected, self.firmware_version
        )

    def load_message(self, msg, msg_id=None):
        """
        Load a message through bpod to the module and associate an ID to it.

        :param list(int) msg: Message to send
        :param int msg_id: Id of the message to use
        """
        if msg_id is None:
            for i in range(255):
                if not self.bpod_modules.bpod.msg_id_list[i]:
                    msg_id = i + 1
                    break

        self.bpod_modules.bpod.load_serial_message(self.serial_port, msg_id, msg)
        return msg_id

    def start_module_relay(self):
        if not self.bpod_modules.relay_is_active:
            self.bpod_modules.activate_module_relay(self)
            self.relay_active = True
        else:
            raise BpodErrorException(
                """Error: You must disable the active module relay before 
                starting another one."""
            )

    def stop_module_relay(self):
        self.bpod_modules.deactivate_module_relay(self)
        self.relay_active = False

    def __read(self, size=None, dtype=None):
        if not self.relay_active:
            raise BpodErrorException(
                """Error: you must start the module relay with start_moule_relay() 
                before you can read bytes from a module"""
            )

        if size is None:
            size = self.bpod_modules.bpod.data_available()
        return self.bpod_modules.module_read(self, size, dtype)

    def write_char_array(self, message):
        self.bpod_modules.module_write(self, message, ArduinoTypes.CHAR)

    def write_uint8_array(self, message):
        self.bpod_modules.module_write(self, message, ArduinoTypes.UINT8)

    def write_uint16_array(self, message):
        self.bpod_modules.module_write(self, message, ArduinoTypes.UINT16)

    def write_uint32_array(self, message):
        self.bpod_modules.module_write(self, message, ArduinoTypes.UINT32)

    def write_float_array(self, message):
        self.bpod_modules.module_write(self, message, ArduinoTypes.FLOAT)

    def read_char_array(self, size=None):
        self.__read(size, ArduinoTypes.CHAR)

    def read_uint8_array(self, size=None):
        self.__read(size, ArduinoTypes.UINT8)

    def read_uint16_array(self, size=None):
        self.__read(size, ArduinoTypes.UINT16)

    def read_uint32_array(self, size=None):
        self.__read(size, ArduinoTypes.UINT32)

    def read_float_array(self, size=None):
        self.__read(size, ArduinoTypes.FLOAT)
