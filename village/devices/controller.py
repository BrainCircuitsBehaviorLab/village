import threading
import time
import traceback
from typing import Any, Callable

from village.classes.enums import ControllerEnum
from village.classes.null_classes import (
    NullBpod,
    NullSession,
    NullSoftCodeToBpod,
    NullStateMachine,
)
from village.pybpodapi.com.softcode_to_bpod import SoftCodeToBpod
from village.pybpodapi.protocol import Bpod, StateMachine
from village.pybpodapi.session import Session
from village.scripts.log import log
from village.scripts.parse_bpod_messages import (
    parse_input_to_tuple_override,
    parse_output_to_tuple_override,
)
from village.settings import settings


class BehaviorController:
    def __init__(self) -> None:
        self.type = settings.get("BEHAVIOR_CONTROLLER")
        if self.type == ControllerEnum.BPOD:
            self.bpod: Bpod | NullBpod = NullBpod()
            self.sma: StateMachine | NullStateMachine = NullStateMachine()
            self.softcode_to_bpod: SoftCodeToBpod | NullSoftCodeToBpod = (
                NullSoftCodeToBpod()
            )
            self.session: Session | NullSession = NullSession()
            self.connected = False
            self.functions: list[Callable] = []
            self.error = "Error connecting to the bpod "
            try:
                self.bpod = Bpod()
                self.sma = StateMachine(self.bpod)
                self.softcode_to_bpod = SoftCodeToBpod()
                self.session = self.bpod.session
                self.error = ""
                log.info("Bpod successfully initialized")
                self.bpod.close()
            except Exception:
                time.sleep(0.1)
                try:
                    self.bpod = Bpod()
                    self.sma = StateMachine(self.bpod)
                    self.softcode_to_bpod = SoftCodeToBpod()
                    self.session = self.bpod.session
                    self.error = ""
                    log.info("Bpod successfully initialized")
                    self.bpod.close()
                except Exception:
                    self.error = "Error connecting to Bpod"
                    log.error(
                        "Could not initialize bpod", exception=traceback.format_exc()
                    )
        elif self.type == ControllerEnum.ARDUINO:
            self.error = "Arduino not implemented yet"
        elif self.type == ControllerEnum.RASPBERRY:
            self.error = "Raspberry Pi not implemented yet"

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

    def send_softcode_to_bpod(self, idx: int) -> None:
        self.softcode_to_bpod.send(idx)

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
            self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)
        self.softcode_to_bpod = SoftCodeToBpod()
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
        self.softcode_to_bpod.kill()
        time.sleep(1)
        self.close()

    def close(self) -> None:
        self.connected = False
        try:
            self.bpod.close()
        except AttributeError:
            pass


def get_controller() -> BehaviorController:
    return BehaviorController()


controller = get_controller()
