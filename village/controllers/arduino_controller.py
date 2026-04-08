from typing import Any, Callable

from village.classes.enums import ControllerEnum
from village.controllers.controller import Controller


class ArduinoController(Controller):
    def __init__(self) -> None:
        super().__init__()

        self.type = ControllerEnum.ARDUINO
        self.check_connection()

    def check_connection(self):
        self.error = ""

    def connect(self, functions: list[Callable]) -> None:
        """Connects to the Arduino and initializes session.

        Args:
            functions (list[Callable]): List of callback functions for softcodes.
        """
        self.functions = functions
        self.connected = True

    def get_trial_data(self) -> dict:
        return self.recorder.get_trial_data()

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
            state_change_conditions (Any): Dictionary of events that trigger
            state transitions.
            output_actions (Any): Actions to perform when entering the state.
        """
        pass

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
        pass

    def set_condition(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        """Sets a condition for the state machine.

        Args:
            condition_number (Any): The identifier for the condition.
            condition_channel (Any): The channel to check.
            channel_value (Any): The value to check against.
        """
        pass

    def set_global_counter(
        self, counter_number: Any, target_event: Any, threshold: Any
    ) -> None:
        """Sets a global counter.

        Args:
            counter_number (Any): The ID of the counter.
            target_event (Any): The event to count.
            threshold (Any): The count threshold.
        """
        pass

    def create_state_machine(self) -> None:
        """Creates a new state machine instance."""
        pass

    def send_and_run_state_machine(self) -> None:
        """Sends and runs the current state machine on the Bpod."""
        pass

    def register_value(self, name: str, value: Any) -> None:
        """Registers a value with the session recorder.

        Args:
            name (str): The name of the value.
            value (Any): The value to register.
        """
        self.recorder.add_value(name, value)

    def send_softcode_to_bpod(self, idx: int) -> None:
        """Handles sending a softcode to the bpod.

        Args:
            idx (int): The softcode index.
        """
        pass

    def manual_override_input(self, message: str) -> None:
        """Manually overrides an input channel.

        Args:
            message (str): The override message string.
        """
        pass

    def manual_override_output(self, message: str | tuple) -> None:
        """Manually overrides an output channel.

        Args:
            message (str | tuple): The override message string or tuple.
        """
        pass

    def softcode_handler_function(self, data: int) -> None:
        """Handles regular softcode callbacks.

        Args:
            data (int): The softcode data value (1-99).
        """
        if 1 <= data <= 99:
            self.functions[data]()

    def led(self, i: int, close: bool) -> None:
        """Triggers an LED in a separate thread.

        Args:
            i (int): LED index.
            close (bool): Whether to close connection after triggered.
        """
        pass

    def water(self, i: int, close: bool) -> None:
        """Triggers a water valve in a separate thread.

        Args:
            i (int): Valve index.
            close (bool): Whether to close connection.
        """
        pass

    def poke(self, i: int, close: bool) -> None:
        """Simulates a poke event in a separate thread.

        Args:
            i (int): Poke port index.
            close (bool): Whether to close connection.
        """
        pass

    def clean(self) -> None:
        """Runs a cleanup state machine that exits immediately."""
        pass

    def stop(self) -> None:
        """Stops the current session and closes connections."""
        self.close()

    def close(self) -> None:
        """Closes the Bpod connection."""
        pass
