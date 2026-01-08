import socket
import sys
import threading
import time
import traceback
from typing import Any, Callable

from village.classes.abstract_classes import PyBpodBase
from village.pybpodapi.protocol import Bpod, StateMachine
from village.scripts.log import log
from village.scripts.parse_bpod_messages import (
    parse_input_to_tuple_override,
    parse_output_to_tuple_override,
)
from village.settings import settings


class SoftCode:
    """Handles UDP SoftCode communication.

    Attributes:
        client_socket (socket.socket): The UDP socket.
        address (tuple): The (ip, port) address for UDP communication.
    """

    def __init__(self) -> None:
        """Initializes the SoftCode connection."""
        address = int(settings.get("BPOD_NET_PORT"))
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(1.0)
        self.address = ("127.0.0.1", address)

    def send(self, idx: int) -> None:
        """Sends a SoftCode to the configured address.

        Args:
            idx (int): The softcode index to send.
        """
        str_message = "SoftCode" + str(idx)
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def kill(self) -> None:
        """Sends a kill signal to stop the current session."""
        str_message = "kill"
        message = str_message.encode("utf-8")
        self.client_socket.sendto(message, self.address)
        stop_message = b"s"
        self.client_socket.sendto(stop_message, self.address)

    def close(self) -> None:
        """Closes the UDP socket."""
        self.client_socket.close()


class PyBpod(PyBpodBase):
    """Interface for controlling Bpod devices.

    Attributes:
        bpod (Bpod): The Bpod device instance.
        sma (StateMachine): The state machine instance.
        softcode (SoftCode): The SoftCode handler.
        session: The current Bpod session.
        connected (bool): Connection status.
        error (str): Error message if any.
        functions (list[Callable]): List of callback functions for softcodes.
    """

    def __init__(self) -> None:
        """Initializes the PyBpod interface."""
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
        """Adds a state to the state machine.

        Args:
            state_name (Any): The name of the state.
            state_timer (float): Duration of the state in seconds.
            state_change_conditions (Any): Dictionary of events that trigger state transitions.
            output_actions (Any): Actions to perform when entering the state.
        """
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
        """Sets a global timer.

        Args:
            timer_id (Any): The ID of the timer.
            timer_duration (Any): The duration of the timer.
            on_set_delay (int): Delay before setting the timer.
            channel (Any | None): The channel associated with the timer.
            on_message (int): Message to send when timer starts.
            off_message (int): Message to send when timer ends.
            loop_mode (int): Loop mode configuration.
            loop_intervals (int): Number of loop intervals.
            send_events (int): Whether to send events.
            oneset_triggers (Any | None): Triggers to set once.
        """
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
        """Sets a condition for the state machine.

        Args:
            condition_number (Any): The identifier for the condition.
            condition_channel (Any): The channel to check.
            channel_value (Any): The value to check against.
        """
        self.sma.set_condition(
            condition_number=condition_number,
            condition_channel=condition_channel,
            channel_value=channel_value,
        )

    def set_global_counter(
        self, counter_number: Any, target_event: Any, threshold: Any
    ) -> None:
        """Sets a global counter.

        Args:
            counter_number (Any): The ID of the counter.
            target_event (Any): The event to count.
            threshold (Any): The count threshold.
        """
        self.sma.set_global_counter(
            counter_number=counter_number,
            target_event=target_event,
            threshold=threshold,
        )

    def create_state_machine(self) -> None:
        """Creates a new state machine instance."""
        self.sma = StateMachine(self.bpod)

    def send_and_run_state_machine(self) -> None:
        """Sends and runs the current state machine on the Bpod."""
        self.bpod.send_state_machine(self.sma)
        self.bpod.run_state_machine(self.sma)

    def register_value(self, name: str, value: Any) -> None:
        """Registers a value with the Bpod session.

        Args:
            name (str): The name of the value.
            value (Any): The value to register.
        """
        self.bpod.register_value(name, value)

    def receive_softcode(self, idx: int) -> None:
        """Handles receiving a softcode and forwarding it via SoftCode sender.

        Args:
            idx (int): The softcode index.
        """
        self.softcode.send(idx)

    def manual_override_input(self, message: str) -> None:
        """Manually overrides an input channel.

        Args:
            message (str): The override message string.
        """
        channel_name, channel_number, value = parse_input_to_tuple_override(message)

        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.INPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def manual_override_output(self, message: str | tuple) -> None:
        """Manually overrides an output channel.

        Args:
            message (str | tuple): The override message string or tuple.
        """
        channel_name, channel_number, value = parse_output_to_tuple_override(message)

        self.bpod.manual_override(
            channel_type=Bpod.ChannelTypes.OUTPUT,
            channel_name=channel_name,
            channel_number=channel_number,
            value=value,
        )

    def softcode_handler_function(self, data: int) -> None:
        """Handles regular softcode callbacks.

        Args:
            data (int): The softcode data value (1-99).
        """
        if 1 <= data <= 99:
            self.functions[data]()

    def connect(self, functions: list[Callable]) -> None:
        """Connects to the Bpod and initializes session.

        Args:
            functions (list[Callable]): List of callback functions for softcodes.
        """
        try:
            self.bpod = Bpod()
        except Exception:
            time.sleep(0.1)
            self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)
        self.softcode = SoftCode()
        self.session = self.bpod.session
        self.connected = True
        self.functions = functions
        self.bpod.softcode_handler_function = self.softcode_handler_function  # type: ignore

    def led(self, i: int, close: bool) -> None:
        """Triggers an LED in a separate thread.

        Args:
            i (int): LED index.
            close (bool): Whether to close connection after triggered.
        """
        thread = threading.Thread(
            target=self.led_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def led_thread(self, i: int, close: bool) -> None:
        """Thread function to blink an LED.

        Args:
            i (int): LED index.
            close (bool): Whether to close connection after.
        """
        port = "PWM" + str(i)
        self.manual_override_output((port, 255))
        time.sleep(1)
        self.manual_override_output((port, 0))
        if close:
            self.close()

    def water(self, i: int, close: bool) -> None:
        """Triggers a water valve in a separate thread.

        Args:
            i (int): Valve index.
            close (bool): Whether to close connection.
        """
        thread = threading.Thread(
            target=self.water_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def water_thread(self, i: int, close: bool) -> None:
        """Thread function to open and close a water valve.

        Args:
            i (int): Valve index.
            close (bool): Whether to close connection.
        """
        self.manual_override_output("Valve" + str(i))
        time.sleep(1)
        self.manual_override_output("Valve" + str(i) + "Off")
        if close:
            self.close()

    def poke(self, i: int, close: bool) -> None:
        """Simulates a poke event in a separate thread.

        Args:
            i (int): Poke port index.
            close (bool): Whether to close connection.
        """
        thread = threading.Thread(
            target=self.poke_thread,
            args=(
                i,
                close,
            ),
        )
        thread.start()

    def poke_thread(self, i: int, close: bool) -> None:
        """Thread function to simulate poke entry and exit.

        Args:
            i (int): Poke port index.
            close (bool): Whether to close connection.
        """
        self.manual_override_input("Port" + str(i) + "In")
        time.sleep(0.1)
        self.manual_override_input("Port" + str(i) + "Out")
        if close:
            self.close()

    def clean(self) -> None:
        """Runs a cleanup state machine that exits immediately."""
        self.add_state(
            state_name="End",
            state_timer=0,
            state_change_conditions={"Tup": "exit"},
            output_actions=[],
        )
        self.send_and_run_state_machine()

    def stop(self) -> None:
        """Stops the current session and closes connections."""
        self.softcode.kill()
        time.sleep(1)
        self.close()

    def close(self) -> None:
        """Closes the Bpod connection."""
        self.connected = False
        try:
            self.bpod.close()
        except AttributeError:
            pass


def get_bpod() -> PyBpodBase:
    """Initializes and returns a PyBpod instance.

    Returns:
        PyBpodBase: An instance of PyBpod or a dummy base class on failure/Sphinx.
    """
    if "sphinx" in sys.modules:
        return PyBpodBase()
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
            return PyBpodBase()


bpod = get_bpod()

