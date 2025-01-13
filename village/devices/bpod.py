import re
import socket
import time
import traceback
from typing import Any, Callable

from village.classes.protocols import PyBpodProtocol
from village.log import log
from village.pybpodapi.protocol import Bpod, StateMachine
from village.settings import settings


class Softcode:

    def __init__(self) -> None:
        """Open the connection"""
        address = int(settings.get("BPOD_NET_PORT"))
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(1.0)
        self.address = ("127.0.0.1", address)

    def send(self, idx: int) -> None:
        """Send the softcode to the port idx"""
        str_message = "SoftCode" + str(idx)
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def kill(self) -> None:
        """Send a code to kill the current session"""
        str_message = "kill"
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def close(self) -> None:
        """Close the connection"""
        self.client_socket.close()


class PyBpod(PyBpodProtocol):
    def __init__(self) -> None:
        self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)
        self.softcode = Softcode()
        self.session = self.bpod.session
        self.connected = True
        self.error = ""
        self.functions: list[Callable] = []

    def add_state(
        self,
        state_name: Any,
        state_timer: int = 0,
        state_change_conditions: Any = {},
        output_actions: Any = (),
    ) -> None:
        self.sma.add_state(
            state_name=state_name,
            state_timer=state_timer,
            state_change_conditions=state_change_conditions,
            output_actions=output_actions,
        )

    def set_global_timer(
        self,
        timer_id: Any,
        timer_duration: Any,
        on_set_delay: int = 0,
        channel: Any | None = None,
        on_message: int = 1,
        off_message: int = 0,
        loop_mode: int = 0,
        loop_intervals: int = 0,
        send_events: int = 1,
        oneset_triggers: Any | None = None,
    ) -> None:
        self.sma.set_global_timer(
            timer_id=timer_id,
            timer_duration=timer_duration,
            on_set_delay=on_set_delay,
            channel=channel,
            on_message=on_message,
            off_message=off_message,
            loop_mode=loop_mode,
            loop_intervals=loop_intervals,
            send_events=send_events,
            oneset_triggers=oneset_triggers,
        )

    def set_condition(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        self.sma.set_condition(
            condition_number=condition_number,
            condition_channel=condition_channel,
            channel_value=channel_value,
        )

    def set_global_counter(
        self, counter_number: Any, target_event: Any, threshold: Any
    ) -> None:
        self.sma.set_global_counter(
            counter_number=counter_number,
            target_event=target_event,
            threshold=threshold,
        )

    def create_state_machine(self) -> None:
        self.sma = StateMachine(self.bpod)

    def send_and_run_state_machine(self) -> None:
        self.bpod.send_state_machine(self.sma)
        self.bpod.run_state_machine(self.sma)

    def register_value(self, name: str, value: Any) -> None:
        self.bpod.register_value(name, value)

    def send_softcode(self, idx: int) -> None:
        # TODO: Move outside bpod as this is to receive softcodes in bpod
        self.softcode.send(idx)

    @staticmethod
    def parse_message_input(message: str | tuple[str, int]) -> tuple[str, int, int]:
        # Convert the message to string if it's a tuple
        msg = str(message)

        # Pattern for "Port#In" and "Port#Out" (where # is 1-9)
        port_pattern = re.compile(r"Port([0-9])(In|Out)")

        # Pattern for "PA1_Port#In" and "PA1_Port#Out" (where # is 1-9)
        pa1_port_pattern = re.compile(r"PA1_Port([0-9])(In|Out)")

        # Pattern for "BNC#High" and "BNC#Low" (where # is 1-9)
        bnc_pattern = re.compile(r"BNC([0-9])(High|Low)")

        # Pattern for "Wire#High" and "Wire#Low" (where # is 1-9)
        wire_pattern = re.compile(r"Wire([0-9])(High|Low)")

        # Pattern for "SerialX_Y" messages (where X is 1-9 and Y is 1-99)
        serial_pattern = re.compile(r"Serial([0-9])_([0-9][0-9]?)")

        # Pattern for "SoftCodeX" messages (where X is 1-99)
        softcode_pattern = re.compile(r"SoftCode([0-9][0-9]?)")

        # Pattern for GlobalTimer#_End
        global_timer_end_pattern = re.compile(r"_GlobalTimer([0-9])_(End)")

        # Pattern for GlobalTimer#_Start
        global_timer_start_pattern = re.compile(r"_GlobalTimer([0-9])_(Start)")

        # Pattern for GlobalCounter# with _End and _Reset suffixes
        global_counter_pattern = re.compile(r"_GlobalCounter([0-9])_(End)")

        # Pattern for "Condition#"
        condition_pattern = re.compile(r"_Condition([0-9])")

        if msg == "_Tup":
            return ("_Tup", 1, 1)

        elif port_match := port_pattern.match(msg):
            channel, state = port_match.groups()
            value = 1 if state == "In" else 0
            return ("Port", int(channel), value)

        elif pa1_port_match := pa1_port_pattern.match(msg):
            channel, state = pa1_port_match.groups()
            value = 1 if state == "In" else 0
            return ("PA1_Port", int(channel), value)

        elif bnc_match := bnc_pattern.match(msg):
            channel, state = bnc_match.groups()
            value = 3 if state == "High" else 0
            return ("BNC", int(channel), value)

        elif wire_match := wire_pattern.match(msg):
            channel, state = wire_match.groups()
            value = 3 if state == "High" else 0
            return ("Wire", int(channel), value)

        elif serial_match := serial_pattern.match(msg):
            channel, val = serial_match.groups()
            return ("Serial", int(channel), int(val))

        elif softcode_match := softcode_pattern.match(msg):
            channel = softcode_match.group(1)
            return ("USB", int(channel), 1)  # The value is always 1

        elif global_timer_start_match := global_timer_start_pattern.match(msg):
            channel, _ = global_timer_start_match.groups()
            return ("_GlobalTimer", int(channel), 1)

        elif global_timer_end_match := global_timer_end_pattern.match(msg):
            channel, _ = global_timer_end_match.groups()
            return ("_GlobalTimer_End", int(channel), 1)

        elif global_counter_end_match := global_counter_pattern.match(msg):
            channel, _ = global_counter_end_match.groups()
            return ("_GlobalCounter_End", int(channel), 1)

        elif condition_match := condition_pattern.match(msg):
            channel = condition_match.group(1)
            return ("_Condition", int(channel), 1)

        else:
            raise ValueError(f"Unrecognized message format: {msg}")

    @staticmethod
    def parse_message_output(message: str | tuple[str, int]) -> tuple[str, Any, int]:
        # Convert the message to string if it's a tuple
        msg = str(message)

        # Pattern for ("PWMX", Y) messages (where X is 1-9 and Y is 0-255)
        pwm_pattern = re.compile(r"\('PWM([0-9])',\s*([0-9]|[0-9][0-9]{1,2})\)")

        # Pattern for ("Valve", X) messages (where X is 1-8)
        valve_pattern = re.compile(r"\('Valve',\s*([0-9])")

        # Pattern for ("BNCX", Y) messages (where X is 1-2 and Y is 0-3)
        bnc_pattern = re.compile(r"\('BNC([0-9])',\s*([0-9])")

        # Pattern for ("WireX", Y) messages (where X is 1-4 and Y is 0-3)
        wire_pattern = re.compile(r"\('Wire([0-9])',\s*([0-9])")

        # Pattern for ("SerialX", Y) messages (where X is 1-9 and Y is 0-99)
        serial_pattern = re.compile(r"\('Serial([0-9])',\s*([0-9][0-9]?)")

        # Pattern for ("SoftCode", Y) messages (where Y is 1-99)
        softcode_pattern = re.compile(r"\('SoftCode',\s*([0-9][0-9]?)")

        # Pattern for ("_GlobalTimerTrig", Y) messages (where Y is 1-9)
        global_timer_trig_pattern = re.compile(r"\('_GlobalTimerTrig',\s*([0-9])")

        # Pattern for ("_GlobalTimerCancel", Y) messages (where Y is 1-9)
        global_timer_cancel_pattern = re.compile(r"\('_GlobalTimerCancel',\s*([0-9])")

        # Pattern for ("_GlobalCounterReset", Y) messages (where Y is 1-9)
        global_counter_reset_pattern = re.compile(r"\('_GlobalCounterReset',\s*([0-9])")

        if pwm_match := pwm_pattern.match(msg):
            channel, val = pwm_match.groups()
            return ("PWM", int(channel), int(val))

        elif valve_match := valve_pattern.match(msg):
            channel = valve_match.group(1)
            return ("Valve", int(channel), 1)  # The value is always 1

        elif bnc_match := bnc_pattern.match(msg):
            channel, val = bnc_match.groups()
            return ("BNC", int(channel), int(val))

        elif wire_match := wire_pattern.match(msg):
            channel, val = wire_match.groups()
            return ("Wire", int(channel), int(val))

        elif serial_match := serial_pattern.match(msg):
            channel, val = serial_match.groups()
            return ("Serial", int(channel), int(val))

        elif softcode_match := softcode_pattern.match(msg):
            val = softcode_match.group(1)
            return ("SoftCode", "", int(val))  # The value is always 1

        elif global_timer_trig_match := global_timer_trig_pattern.match(msg):
            val = global_timer_trig_match.group(1)
            return ("_GlobalTimerTrig", "", int(val))

        elif global_timer_cancel_match := global_timer_cancel_pattern.match(msg):
            val = global_timer_cancel_match.group(1)
            return ("_GlobalTimerCancel", "", int(val))

        elif global_counter_reset_match := global_counter_reset_pattern.match(msg):
            val = global_counter_reset_match.group(1)
            return ("_GlobalCounterReset", "", int(val))

        else:
            raise ValueError(f"Unrecognized message format: {msg}")

    def manual_override_input(self, message: str | tuple) -> None:
        channel_name, channel_number, value = self.parse_message_input(message)
        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.INPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def manual_override_output(self, message: str | tuple) -> None:
        channel_name, channel_number, value = self.parse_message_output(message)
        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.OUTPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def softcode_handler_function(self, data: int) -> None:
        if 1 <= data <= 99:
            self.functions[data]()

    def reconnect(self, functions: list[Callable]) -> None:
        if not self.connected:
            self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)
        self.softcode = Softcode()
        self.session = self.bpod.session
        self.connected = True
        self.functions = functions
        self.bpod.softcode_handler_function = self.softcode_handler_function  # type: ignore

    def clean(self) -> None:
        self.add_state(
            state_name="End",
            state_timer=0,
            state_change_conditions={"_Tup": "exit"},
            output_actions=[],
        )
        self.send_and_run_state_machine()

    def stop(self) -> None:
        self.softcode.kill()
        time.sleep(1)
        self.close()

    def close(self) -> None:
        self.connected = False
        try:
            self.bpod.close()
        except AttributeError:
            pass


def get_bpod() -> PyBpodProtocol:
    try:
        bpod = PyBpod()
        log.info("Bpod successfully initialized")
        return bpod
    except Exception:
        log.error("Could not initialize bpod", exception=traceback.format_exc())
        return PyBpodProtocol()


bpod = get_bpod()
