import logging
import time

import numpy as np
from pybpodapi.bpod.bpod_com_protocol import BpodCOMProtocol
from pybpodapi.bpod_modules.bpod_modules import BpodModules
from pybpodapi.com.arcom import ArduinoTypes
from pybpodapi.com.protocol.recv_msg_headers import ReceiveMessageHeader
from pybpodapi.com.protocol.send_msg_headers import SendMessageHeader
from pybpodapi.exceptions.bpod_error import BpodErrorException

logger = logging.getLogger(__name__)


class BpodCOMProtocolModules(BpodCOMProtocol):
    """
    Define command actions that can be requested to Bpod device.

    **Private attributes**

        _arcom
            :class:`pybpodapi.com.arcom.ArCOM`

            ArCOM object that performs serial communication.

    **Methods**

    """

    def _bpodcom_get_modules_info(self, hardware):

        bpod_modules = BpodModules(self)  # type: BpodModules

        input_modules = [inp for inp in hardware.inputs if inp == "U"]
        n_modules = len(input_modules)
        n_serial_events = int(hardware.max_serial_events / (n_modules + 1))

        self._arcom.write_char(SendMessageHeader.GET_MODULES)
        time.sleep(0.3)

        modules_requested_events = np.array([0] * n_modules)

        names = {}

        if self._arcom.bytes_available() > 1:
            for i in range(n_modules):
                connected = self._arcom.read_uint8() == 1
                firmware_version = None
                module_name = None
                events_names = []

                if connected:
                    firmware_version = self._arcom.read_uint32()
                    name_length = self._arcom.read_uint8()
                    name_string = self._arcom.read_char_array(name_length)
                    name_string = "".join(name_string)

                    if name_string not in names:
                        names[name_string] = 0
                    names[name_string] += 1

                    module_name = name_string + str(names[name_string])

                    flag = self._arcom.read_uint8()
                    while flag == 1:  # has more info to be read
                        param_type = self._arcom.read_uint8()

                        if param_type == ReceiveMessageHeader.MODULE_REQUESTED_EVENT:
                            modules_requested_events[i] = self._arcom.read_uint8()

                        elif param_type == ReceiveMessageHeader.MODULE_EVENT_NAMES:

                            n_event_names = self._arcom.read_uint8()
                            for _ in range(n_event_names):
                                n_chars = self._arcom.read_uint8()
                                event_name = self._arcom.read_char_array(n_chars)
                                events_names.append("".join(event_name))

                        flag = self._arcom.read_uint8()

                bpod_modules += BpodModules.create_module(
                    connected,
                    module_name,
                    firmware_version,
                    events_names,
                    n_serial_events,
                    serial_port=i + 1,
                )

        if (
            modules_requested_events.sum() + n_serial_events
        ) > hardware.max_serial_events:
            raise BpodErrorException(
                "Error: Connected modules requested too many events."
            )

        for i, module in enumerate(bpod_modules):
            if module.connected:

                if modules_requested_events[i] > module.n_serial_events:
                    n_to_reassign = modules_requested_events[i] - module.n_serial_events
                    module.n_serial_events = modules_requested_events[i]
                else:
                    n_to_reassign = 0

                index = n_modules - 1
                while n_to_reassign > 0:
                    if bpod_modules[index].n_serial_events >= n_to_reassign:
                        bpod_modules[index].n_serial_events = (
                            bpod_modules[index].n_serial_events - n_to_reassign
                        )
                        n_to_reassign = 0
                    else:
                        n_to_reassign = (
                            n_to_reassign - bpod_modules[index].n_serial_events
                        )
                        bpod_modules[index].n_serial_events = 0
                    index -= 1

        n_serial_events_array = [m.n_serial_events for m in bpod_modules]
        n_soft_codes = hardware.max_serial_events - sum(n_serial_events_array)

        bytes2send = ArduinoTypes.get_uint8_array(
            [ord("%")] + n_serial_events_array + [n_soft_codes]
        )

        self._arcom.write_array(bytes2send)
        res = self._arcom.read_uint8()

        if not res:
            raise BpodErrorException(
                "Error: Failed to configure module event assignment."
            )

        return bpod_modules

    def _bpodcom_activate_module_relay(self, module_index):
        self._arcom.write_array(
            [ord(SendMessageHeader.SET_MODULE_RELAY), module_index, 1]
        )

    def _bpodcom_deactivate_module_relay(self, module_index):
        self._arcom.write_array(
            [ord(SendMessageHeader.SET_MODULE_RELAY), module_index, 0]
        )

    def _bpodcom_clean_any_data_in_the_buffer(self):
        n_bytes_available = self.bytes_available()
        if n_bytes_available > 0:
            self._arcom.read_uint8_array(n_bytes_available)

    def _bpodcom_module_write(self, module_index, message, dtype=None):
        if dtype is None:
            dtype = ArduinoTypes.UINT8

        if isinstance(message, str):
            message = [ord(c) for c in message]
        elif not isinstance(message, (list, np.ndarray)):
            message = [message]
        else:
            message = message

        msg = ArduinoTypes.get_array(message, dtype)

        if len(msg) > 64:
            raise BpodErrorException(
                "Error: module messages must be under 64 bytes per transmission"
            )

        to_send = [
            ord(SendMessageHeader.WRITE_TO_MODULE),
            module_index + 1,
            len(msg),
        ]
        to_send = ArduinoTypes.get_uint8_array(to_send)

        self._arcom.write_array(to_send + msg)

    def _bpodcom_module_read(self, module_index, size, dtype=None):
        if dtype is None:
            dtype = ArduinoTypes.UINT8

        if dtype == ArduinoTypes.CHAR:
            return self._arcom.read_char_array(size)
        elif dtype == ArduinoTypes.UINT8:
            return self._arcom.read_uint8_array(size)
        elif dtype == ArduinoTypes.UINT16:
            return self._arcom.read_uint16_array(size)
        elif dtype == ArduinoTypes.UINT32:
            return self._arcom.read_uint32_array(size)
        elif dtype == ArduinoTypes.FLOAT32:
            return self._arcom.read_float32_array(size)
        else:
            return None
