from typing import Any, Callable

from PyQt5.QtWidgets import QWidget

from village.classes.enums import Active
from village.pybpodapi.session import Session
from village.scripts import time_utils
from village.settings import settings


class PyBpodBase:
    error: str = "Error connecting to the bpod "
    session: Session | Any = None
    connected: bool = False

    def connect(self, functions: list[Callable]) -> None:
        return

    def add_state(
        self,
        state_name: Any,
        state_timer: float = 0,
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
        self, counter_number: Any, target_event: Any, threshold: Any
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

    def manual_override_input(self, message: str) -> None:
        return

    def manual_override_output(self, message: str | tuple) -> None:
        return

    def register_value(self, name: str, value: Any) -> None:
        return

    def receive_softcode(self, idx: int) -> None:
        return

    def led(self, i: int, close: bool) -> None:
        return

    def water(self, i: int, close: bool) -> None:
        return

    def poke(self, i: int, close: bool) -> None:
        return


class TelegramBotBase:
    error: str = "Error connecting to the telegram_bot "

    def alarm(self, message: str) -> None:
        return


class ScaleBase:
    error: str = "Error connecting to the scale "

    def tare(self) -> None:
        return

    def calibrate(self, weight: float) -> None:
        return

    def get_weight(self) -> float:
        return 0.0


class TempSensorBase:
    error: str = "Error connecting to the temp_sensor "

    def start(self) -> None:
        return

    def get_temperature(self) -> tuple[float, float, str]:
        return 0.0, 0.0, ""


class SoundDeviceBase:
    samplerate: int = 44100
    error: str = (
        ""
        if settings.get("USE_SOUNDCARD") == Active.OFF
        else "Error connecting to the sound_device "
    )

    def load(self, left: Any, right: Any) -> None:
        return

    def play(self) -> None:
        return

    def stop(self) -> None:
        return


class EventBase:
    def log(self, date: str, type: str, subject: str, description: str) -> None:
        return

    def log_temp(self, date: str, temperature: float, humidity: float) -> None:
        return


class CameraBase:
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


class BehaviorWindowBase(QWidget):
    def set_active(self, value: bool) -> None:
        return

    def set_draw_function(self, draw_fn: Callable) -> None:
        return
