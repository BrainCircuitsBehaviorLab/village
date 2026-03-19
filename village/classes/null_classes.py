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
        """Adds a state to the state machine.

        Args:
            state_name (Any): Name of the state.
            state_timer (float): Duration of the state in seconds.
            state_change_conditions (Any): Conditions to transition to other states.
            output_actions (Any): Actions to perform in this state.
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
        """Configures a global timer.

        Args:
            timer_id (Any): ID of the timer.
            timer_duration (Any): Duration of the timer.
            on_set_delay (int): Delay before the timer starts.
            channel (Any | None): Output channel to link.
            on_message (int): Message when timer starts.
            off_message (int): Message when timer ends.
            loop_mode (int): Loop mode.
            loop_intervals (int): Interval between loops.
            send_events (int): Whether to send events.
            oneset_triggers (Any | None): Triggers to set.
        """
        pass

    def set_condition(
        self, condition_number: Any, condition_channel: Any, channel_value: Any
    ) -> None:
        """Sets a condition for the state machine.

        Args:
            condition_number (Any): The condition ID.
            condition_channel (Any): The channel to check.
            channel_value (Any): The value to match.
        """
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
        """Sends an alarm message.

        Args:
            message (str): The alarm message.
        """
        return


class NullScale:
    error: str = "Error connecting to the scale "

    def tare(self) -> None:
        """Tares the scale."""
        return

    def calibrate(self, weight: float) -> None:
        """Calibrates the scale using a known weight.

        Args:
            weight (float): The known weight.
        """
        return

    def get_weight(self) -> float:
        """Gets the current weight.

        Returns:
            float: The weight reading (default 0.0).
        """
        return 0.0


class NullTempSensor:
    error: str = "Error connecting to the temp_sensor "

    def start(self) -> None:
        """Starts the sensor."""
        return

    def get_temperature(self) -> tuple[float, float, str]:
        """Gets temperature and humidity.

        Returns:
            tuple[float, float, str]: Temperature, humidity, and formatted string.
        """
        return 0.0, 0.0, ""


class NullMotor:
    error: str = "Error connecting to the motor "
    open_angle: int = 0
    close_angle: int = 0

    def open(self) -> None:
        """Opens the motor/device."""
        return

    def close(self) -> None:
        """Closes the motor/device."""
        return


class NullSoundDevice:
    samplerate: int = 44100
    error: str = (
        ""
        if settings.get("USE_SOUNDCARD") == Active.OFF
        else "Error connecting to the sound_device "
    )

    def load(self, load: Any, right: Any) -> None:
        """Loads sound data.

        Args:
            load (Any): Left channel data or similar.
            right (Any): Right channel data.
        """
        return

    def play(self) -> None:
        """Plays the loaded sound."""
        return

    def stop(self) -> None:
        """Stops sound playback."""
        return

    def load_wav(self, file: str) -> None:
        """Loads a WAV file.

        Args:
            file (str): Path or name of the WAV file.
        """
        return


class NullCollection:
    def log(self, date: str, type: str, subject: str, description: str) -> None:
        """Logs a generic event.

        Args:
            date (str): Date/time string.
            type (str): Event type.
            subject (str): Subject name.
            description (str): Description.
        """
        return

    def log_temp(self, date: str, temperature: float, humidity: float) -> None:
        """Logs temperature and humidity data.

        Args:
            date (str): Date/time string.
            temperature (float): Temperature value.
            humidity (float): Humidity value.
        """
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
        """Starts the camera."""
        return

    def stop_camera(self) -> None:
        """Stops the camera."""
        return

    def start_preview_window(self) -> QWidget:
        """Starts the preview window.

        Returns:
            QWidget: A QWidget for the preview.
        """
        return QWidget()

    def stop_preview_window(self) -> None:
        """Stops the preview window."""
        return

    def start_recording(self, path_video: str = "", path_csv: str = "") -> None:
        """Starts recording.

        Args:
            path_video (str): Path for video file.
            path_csv (str): Path for CSV data.
        """
        return

    def stop_recording(self) -> None:
        """Stops recording."""
        return

    def print_info_about_config(self) -> None:
        """Prints camera configuration info."""
        return

    def pre_process(self, request) -> None:
        """Preprocessing callback for frames.

        Args:
            request: The request object.
        """
        return

    def write_text(self, text: str) -> None:
        """Writes text annotation to the frame.

        Args:
            text (str): The text to write.
        """
        return

    def areas_corridor_ok(self) -> bool:
        """Checks corridor areas status.

        Returns:
            bool: True if OK.
        """
        return True

    def area_1_empty(self) -> bool:
        """Checks if area 1 is empty.

        Returns:
            bool: True if empty.
        """
        return True

    def area_2_empty(self) -> bool:
        """Checks if area 2 is empty.

        Returns:
            bool: True if empty.
        """
        return True

    def area_3_empty(self) -> bool:
        """Checks if area 3 is empty.

        Returns:
            bool: True if empty.
        """
        return True

    def area_4_empty(self) -> bool:
        """Checks if area 4 is empty.

        Returns:
            bool: True if empty.
        """
        return True

    def take_picture(self) -> None:
        """Takes a picture."""
        return


class NullBehaviorWindow(QWidget):
    background_color = None

    def start_drawing(self) -> None:
        """Starts the drawing mode."""
        return

    def stop_drawing(self) -> None:
        """Stops the drawing mode."""
        return

    def load_draw_function(
        self,
        draw_fn: Optional[Callable],
        image: str | None = None,
        video: str | None = None,
    ) -> None:
        """Loads a drawing function and media.

        Args:
            draw_fn (Optional[Callable]): The drawing function.
            image (str | None): Image path.
            video (str | None): Video path.
        """
        return

    def load_image(self, file: str) -> None:
        """Loads an image.

        Args:
            file (str): The file path.
        """
        return

    def load_video(self, file: str) -> None:
        """Loads a video.

        Args:
            file (str): The file path.
        """
        return

    def get_video_frame(self) -> Optional[QImage]:
        """Gets the current video frame.

        Returns:
            Optional[QImage]: The current frame as a QImage.
        """
        return None
