from typing import Any, Callable, Optional

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QWidget

from village.classes.enums import Active
from village.scripts.time_utils import time_utils
from village.settings import settings


class NullBpod:
    def close(self) -> None:
        pass

    def send_state_machine(self, sma: Any) -> None:
        pass

    def run_state_machine(self, sma: Any) -> None:
        pass

    def register_value(self, name: str, value: Any) -> None:
        pass

    def manual_override(
        self,
        channel_type: Any,
        channel_name: Any,
        channel_number: Any,
        value: Any,
    ) -> None:
        pass


class NullStateMachine:
    def add_state(
        self,
        state_name: Any,
        state_timer: float = 0,
        state_change_conditions: Any = {},
        output_actions: Any = (),
    ) -> None:
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
        pass

    def set_condition(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        pass

    def set_global_counter(
        self, counter_number: Any, target_event: Any, threshold: Any
    ) -> None:
        pass


class NullSoftCodeToBpod:
    def send(self, idx: int) -> None:
        pass

    def kill(self) -> None:
        pass


class NullSession:
    def current_trial(self) -> None:
        pass


class NullTelegramBot:
    error: str = "Error connecting to the telegram_bot "

    def alarm(self, message: str) -> None:
        return


class NullScale:
    error: str = "Error connecting to the scale "

    def tare(self) -> None:
        return

    def calibrate(self, weight: float) -> None:
        return

    def get_weight(self) -> float:
        return 0.0


class NullTempSensor:
    error: str = "Error connecting to the temp_sensor "

    def start(self) -> None:
        return

    def get_temperature(self) -> tuple[float, float, str]:
        return 0.0, 0.0, ""


class NullMotor:
    error: str = "Error connecting to the motor "
    open_angle: int = 0
    close_angle: int = 0

    def open(self) -> None:
        return

    def close(self) -> None:
        return


class NullSoundDevice:
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

    def load_wav(self, file: str) -> None:
        return


class NullCollection:
    def log(self, date: str, type: str, subject: str, description: str) -> None:
        return

    def log_temp(self, date: str, temperature: float, humidity: float) -> None:
        return


class NullCamera:
    area1: list[int] = []
    area2: list[int] = []
    area3: list[int] = []
    area4: list[int] = []
    areas: list[list[int]] = []
    area1_is_triggered: bool = False
    area2_is_triggered: bool = False
    area3_is_triggered: bool = False
    area4_is_triggered: bool = False
    change: bool = False
    annotation: str = ""
    path_picture: str = ""
    error: str = "Error connecting to the camera "
    trial: int = -1
    is_recording: bool = False
    show_time_info: bool = False
    x_position: int = -1
    y_position: int = -1
    chrono = time_utils.Chrono()

    def start_camera(self) -> None:
        return

    def stop_camera(self) -> None:
        return

    def start_preview_window(self) -> QWidget:
        return QWidget()

    def stop_preview_window(self) -> None:
        return

    def start_recording(self, path_video: str = "", path_csv: str = "") -> None:
        return

    def stop_recording(self) -> None:
        return

    def print_info_about_config(self) -> None:
        return

    def pre_process(self, request) -> None:
        return

    def write_text(self, text: str) -> None:
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


class NullBehaviorWindow(QWidget):
    background_color = None

    def start_drawing(self) -> None:
        return

    def stop_drawing(self) -> None:
        return

    def load_draw_function(
        self,
        draw_fn: Optional[Callable],
        image: str | None = None,
        video: str | None = None,
    ) -> None:
        return

    def load_image(self, file: str) -> None:
        return

    def load_video(self, file: str) -> None:
        return

    def get_video_frame(self) -> Optional[QImage]:
        return None
