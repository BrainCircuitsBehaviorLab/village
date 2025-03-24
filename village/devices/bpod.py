import socket
import threading
import time
import traceback
from typing import Any, Callable

from village.classes.protocols import PyBpodProtocol
from village.log import log
from village.pybpodapi.protocol import Bpod, StateMachine
from village.scripts import time_utils
from village.scripts.parse_bpod_messages import (
    parse_input_to_tuple_override,
    parse_output_to_tuple_override,
)
from village.settings import settings


class SoftCode:

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
        self.softcode = SoftCode()
        self.session = self.bpod.session
        self.connected = False
        self.error = ""
        self.functions: list[Callable] = []

    def add_state(
        self,
        state_name: Any,
        state_timer: float = 0,
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

    def receive_softcode(self, idx: int) -> None:
        self.softcode.send(idx)

    def manual_override_input(self, message: str) -> None:
        channel_name, channel_number, value = parse_input_to_tuple_override(message)

        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.INPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def manual_override_output(self, message: str | tuple) -> None:
        channel_name, channel_number, value = parse_output_to_tuple_override(message)

        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.OUTPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def softcode_handler_function(self, data: int) -> None:
        if 1 <= data <= 99:
            self.functions[data]()

    def connect(self, functions: list[Callable]) -> None:
        try:
            self.bpod = Bpod()
        except Exception:
            time.sleep(0.1)

            # TESTING remove >>
            file_name = "/home/pi/bpod_crashes.txt"
            date = time_utils.now_string()
            exception_str = traceback.format_exc()
            with open(file_name, "a") as f:
                f.write(f"{date},{exception_str}\n")
            # >> remove

            self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)
        self.softcode = SoftCode()
        self.session = self.bpod.session
        self.connected = True
        self.functions = functions
        self.bpod.softcode_handler_function = self.softcode_handler_function  # type: ignore

    def led(self, i: int, close: bool) -> None:
        thread = threading.Thread(
            target=self.led_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def led_thread(self, i: int, close: bool) -> None:
        port = "PWM" + str(i)
        self.manual_override_output((port, 255))
        time.sleep(1)
        self.manual_override_output((port, 0))
        if close:
            self.close()

    def water(self, i: int, close: bool) -> None:
        thread = threading.Thread(
            target=self.water_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def water_thread(self, i: int, close: bool) -> None:
        self.manual_override_output("Valve" + str(i))
        time.sleep(1)
        self.manual_override_output("Valve" + str(i) + "Off")
        if close:
            self.close()

    def poke(self, i: int, close: bool) -> None:
        thread = threading.Thread(
            target=self.poke_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def poke_thread(self, i: int, close: bool) -> None:
        self.manual_override_input("Port" + str(i) + "In")
        time.sleep(0.1)
        self.manual_override_input("Port" + str(i) + "Out")
        if close:
            self.close()

    def clean(self) -> None:
        self.add_state(
            state_name="End",
            state_timer=0,
            state_change_conditions={"Tup": "exit"},
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
        bpod.close()
        return bpod
    except Exception:
        time.sleep(0.1)
        try:
            bpod = PyBpod()
            log.info("Bpod successfully initialized")
            bpod.close()
            return bpod
        except Exception:
            log.error("Could not initialize bpod", exception=traceback.format_exc())
            return PyBpodProtocol()


bpod = get_bpod()
