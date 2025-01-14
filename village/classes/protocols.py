from typing import TYPE_CHECKING, Any, Callable

from PyQt5.QtWidgets import QWidget

from village.pybpodapi.session import Session
from village.scripts import time_utils

if TYPE_CHECKING:
    from village.pybpodapi.session import Session


class PyBpodProtocol:
    error: str = "Error connecting to the bpod "
    session: Session | Any
    connected: bool = False

    def reconnect(self, functions: list[Callable]) -> None:
        return

    def add_state(
        self,
        state_name: Any,
        state_timer: int = 0,
        state_change_conditions: Any = {},
        output_actions: Any = (),
    ) -> None:
        return

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
        return

    def set_condition(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        return

    def set_global_counter(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        return

    def create_state_machine(self) -> None:
        return

    def send_and_run_state_machine(self) -> None:
        return

    def close(self) -> None:
        return

    def stop(self) -> None:
        return

    def manual_override_input(self, message: str | tuple) -> None:
        return

    def manual_override_output(self, message: str | tuple) -> None:
        return

    def register_value(self, name: str, value: Any) -> None:
        return

    def send_softcode(self, idx: int) -> None:
        return


class TelegramBotProtocol:
    error: str = "Error connecting to the telegram bot "

    def alarm(self, message: str) -> None:
        return


class ScaleProtocol:
    error: str = "Error connecting to the scale "

    def tare(self) -> None:
        return

    def calibrate(self, weight: float) -> None:
        return

    def get_weight(self) -> float:
        return 0.0

    def get_weight_subject(self) -> float:
        return 0.0

    def get_weight_string(self) -> str:
        return ""


class TempSensorProtocol:
    error: str = "Error connecting to the temp sensor "

    def start(self) -> None:
        return

    def get_temperature(self) -> tuple[float, float, str]:
        return 0.0, 0.0, ""


class EventProtocol:
    def log(self, date: str, type: str, subject: str, description: str) -> None:
        return


class CameraProtocol:
    area1: list[int] = []
    area2: list[int] = []
    area3: list[int] = []
    area4: list[int] = []
    areas: list[list[int]] = []
    change: bool = False
    state: str = ""
    path_picture: str = ""
    error: str = "Error connecting to the camera "
    trial: int = -1
    is_recording: bool = False
    show_time_info: bool = False
    chrono = time_utils.Chrono()

    def start_camera(self) -> None:
        return

    def start_preview_window(self) -> QWidget:
        return QWidget()

    def stop_preview_window(self) -> None:
        return

    def start_record(self, path_video: str = "", path_csv: str = "") -> None:
        return

    def stop_record(self) -> None:
        return

    def stop(self) -> None:
        return

    def change_focus(self, lensposition) -> None:
        return

    def change_framerate(self, framerate) -> None:
        return

    def print_info_about_config(self) -> None:
        return

    def pre_process(self, request) -> None:
        return

    def log(self, text: str) -> None:
        return

    def areas_corridor_ok(self) -> bool:
        return True

    def area_1_empty(self) -> bool:
        return True

    def area_2_empty(self) -> bool:
        return True

    def area_3_empty(self) -> bool:
        return True

    def area_4_empty(self) -> bool:
        return True

    def take_picture(self) -> None:
        return
