import json
import traceback
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable, Tuple

import pandas as pd

from village.classes.collection import Collection
from village.classes.enums import Active, ControllerEnum, Save
from village.classes.null_classes import NullCamera
from village.controllers.arduino_controller import ArduinoController
from village.controllers.bpod_controller import BpodController
from village.controllers.trial_recorder import TrialRecorder
from village.custom_classes.training_protocol_base import Settings, TrainingProtocolBase
from village.devices.sound_device import sound_device
from village.pybpodapi.hardware.events import EventName
from village.pybpodapi.hardware.output_channels import OutputChannel
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import settings

if TYPE_CHECKING:
    from village.devices.camera import Camera


class TaskError(Exception):
    """Exception raised for errors in the Task class."""

    def __init__(self, message) -> None:
        super().__init__(message)


class BpodEvent(EventName):
    """Enumeration of Bpod event names."""

    pass


class BpodOutput(OutputChannel):
    """Enumeration of Bpod output channels."""

    pass


class Task:
    """Base class for defining behavioral tasks.

    Subclass ``Task`` to implement your own task. You must override four methods
    and may optionally call helper methods and read certain attributes during
    execution.

    ──────────────────────────────────────────────────────────
    METHODS YOU MUST OVERRIDE
    ──────────────────────────────────────────────────────────

    start(self) -> None
        Called once before the trial loop begins.
        Use it to configure hardware, pre-compute stimuli, open files, etc.

    create_trial(self) -> None
        Called at the beginning of every trial.
        Build and send the Bpod state machine here (or set up stimuli for
        non-Bpod controllers). The state machine runs to completion before
        ``after_trial`` is called.

    after_trial(self) -> None
        Called immediately after each trial finishes.
        Use it to score the animal's performance, update adaptive parameters,
        and call ``register_value`` to save custom columns to the data file.
        ``self.trial_data`` is already populated at this point.

    close(self) -> None
        Called once after the trial loop ends (session finished, forced stop,
        or error).
        Use it to close files, stop hardware, release resources.

    ──────────────────────────────────────────────────────────
    METHODS YOU CAN CALL (do not override)
    ──────────────────────────────────────────────────────────

    register_value(name: str, value: Any) -> None
        Saves a custom value to the current trial row in the CSV.
        Call this inside ``after_trial``.

        Example::

            self.register_value("correct", 1)
            self.register_value("response_time", 0.432)

    ──────────────────────────────────────────────────────────
    ATTRIBUTES YOU CAN READ INSIDE YOUR TASK
    ──────────────────────────────────────────────────────────

    self.trial_data : dict
        Dictionary populated automatically after each trial with Bpod event
        timestamps and any values previously registered via ``register_value``.
        Available inside ``after_trial`` to drive adaptive logic.

        Typical keys: ``"trial"``, ``"subject"``, ``"task"``, ``"date"``,
        ``"system_name"``, plus every key you have registered with
        ``register_value``.

        Example::

            def after_trial(self):
                if self.trial_data.get("correct") == 1:
                    self.settings.difficulty += 1

    self.current_trial : int
        1-based index of the trial that just ran (available in both
        ``create_trial`` and ``after_trial``).

    self.subject : str
        Name of the subject running the session.

    self.settings : Settings
        Object that holds all the session parameters defined in the training
        protocol. Read and write its attributes to implement adaptive training.

    self.sound_calibration.get_sound_gain(speaker, dB, sound_name)
        to convert a target dB level into a hardware gain value.

        Example::

            gain = self.sound_calibration.get_sound_gain(
                speaker=1, dB=65.0, sound_name="white_noise"
            )

    self.water_calibration.get_valve_time(port, volume)
        to convert a target volume (µl) into the valve open time (seconds).

        Example::

            valve_time = self.water_calibration.get_valve_time(
                port=1, volume=5.0  # 5 µl
            )

    self.bpod : BpodController
        Low-level Bpod interface (state machine construction, sending, etc.).
        Primarily used inside ``create_trial``.

    self.arduino : ArduinoController
        Arduino interface for tasks that use an Arduino instead of Bpod.

    self.cam_box : Camera | NullCamera
        Camera attached to the behaviour box (NullCamera if not configured).
    """

    def __init__(self) -> None:
        self.controller_type = ControllerEnum.RASPBERRY
        self.bpod = BpodController()
        self.arduino = ArduinoController()
        self.recorder: TrialRecorder = TrialRecorder()
        self.functions: list[Callable] = []

        self.name: str = self.get_name()
        self.subject: str = "None"
        self.current_trial: int = 1
        self.touch_response: list = []
        self.system_name: str = settings.get("SYSTEM_NAME")
        self.date: str = time_utils.now_string()

        self.cam_box: Camera | NullCamera = NullCamera()

        self.info: str = ""

        self.filename: str = ""
        self.sessions_directory: str = ""
        self.raw_session_path: str = ""
        self.session_path: str = ""
        self.session_settings_path: str = ""
        self.video_directory: str = ""
        self.video_path: str = ""
        self.video_data_path: str = ""
        self.subject_path: str = ""
        self.rt_session_path: str = ""
        self.settings: Settings = Settings()
        self.training: TrainingProtocolBase = TrainingProtocolBase()
        self.trial_data: dict = {}

        self.process = Thread()
        self.raw_df: pd.DataFrame = pd.DataFrame()
        self.session_df: pd.DataFrame = pd.DataFrame()
        self.subject_df: pd.DataFrame = pd.DataFrame()
        self.force_stop: bool = False
        self.maximum_number_of_trials: int = 100000000
        self.chrono = time_utils.Chrono()

        self.sound_calibration: Collection = Collection("", [], [])
        self.water_calibration: Collection = Collection("", [], [])

    # OVERWRITE THESE METHODS IN YOUR TASKS
    def start(self) -> None:
        """Starts the task. Must be overridden by subclasses."""
        raise TaskError("The method start(self) is required")

    def create_trial(self) -> None:
        """Creates the state machine for the current trial. Must be overridden."""
        raise TaskError("The method create_trial(self) is required")

    def after_trial(self) -> None:
        """Executed after each trial completes. Must be overridden."""
        raise TaskError("The method after_trial(self) is required")

    def close(self) -> None:
        """Closes the task and releases resources. Must be overridden."""
        raise TaskError("The method close(self) is required")

    # METHODS TO USE IN YOUR TASKS, BUT NOT OVERWRITE
    def register_value(self, name: str, value: Any) -> None:
        """Registers a custom value to be saved with the trial data.

        Args:
            name (str): The name of the value (column header).
            value (Any): The value to store.
        """
        self.recorder.add_value(name, value)
        self.trial_data[name] = value

    # DO NOT OVERWRITE THESE METHODS
    def execute_function(self, i: int) -> None:
        """Executes a registered function.

        Args:
            i (int): The function index (1-99).
        """
        if 1 <= i <= 99:
            self.functions[i]()

    def run_in_thread(self, daemon: bool = True) -> None:
        """Runs the task in a separate background thread.

        Args:
            daemon (bool, optional): Whether to run as a daemon thread.
            Defaults to True.
        """

        def test_run():
            self.create_paths()
            self.start()
            while self.current_trial <= self.maximum_number_of_trials:
                self.do_trial()
            self.disconnect_and_save("Manual")

        self.process = Thread(target=test_run, daemon=daemon)
        self.process.start()
        return

    def run(self) -> None:
        """Runs the task in the main thread until completion or forced stop."""
        self.chrono.reset()
        self.start()
        while (
            self.current_trial <= self.maximum_number_of_trials
            and self.chrono.get_seconds() < self.settings.maximum_duration
            and not self.force_stop
        ):
            self.do_trial()

    def do_trial(self) -> None:
        """Executes a single trial.

        Initializes the state machine, runs it, collects data, and performs
        post-trial updates.
        """
        if self.controller_type == ControllerEnum.BPOD:
            self.bpod.create_state_machine()
            self.cam_box.trial = self.current_trial
            self.create_trial()
            self.bpod.send_and_run_state_machine()
        else:
            self.cam_box.trial = self.current_trial
            self.create_trial()
        self.trial_data = self.recorder.get_trial_data(
            self.date, self.current_trial, self.subject, self.name, self.system_name
        )
        self.after_trial()
        self.concatenate_trial_data()
        self.current_trial += 1
        return

    def concatenate_trial_data(self) -> None:
        """Appends the current trial's data to the session DataFrame."""
        self.row_df = pd.DataFrame([self.trial_data])
        self.session_df = pd.concat([self.session_df, self.row_df], ignore_index=True)
        self.trial_data = {}

    def disconnect_and_save(self, run_mode: str) -> Tuple[Save, float, int, int, str]:
        """Stops the task, disconnects devices, and saves session data.

        Args:
            run_mode (str): The mode in which the task was run (e.g., "Manual").

        Returns:
            Tuple[Save, float, int, int, str]: A tuple containing the save status,
            session duration, number of trials, water consumed, and settings string.
        """
        save: Save = Save.NO
        duration: float = 0.0
        trials: int = 0
        water: int = 0
        settings_str: str = ""
        self.close()
        sound_device.stop()
        if self.controller_type == ControllerEnum.BPOD:
            self.bpod.stop()
        self.cam_box.stop_recording()
        if self.subject != "None":
            try:
                duration, trials, water, ok = self.save_csv(run_mode=run_mode)
                if ok:
                    settings_str = self.save_json(run_mode)
                    save = Save.YES
                else:
                    save = Save.ZERO
            except Exception:
                log.alarm(
                    "Error saving the task: " + self.name,
                    subject=self.subject,
                    exception=traceback.format_exc(),
                )
                save = Save.ERROR
            if save == Save.YES:
                try:
                    self.training.df = self.subject_df
                    self.training.subject = self.subject
                    self.training.last_task = self.name
                    self.training.settings = self.settings
                    self.training.update_training_settings()
                except Exception:
                    save = Save.ERROR
                    log.alarm(
                        "Error updating the training settings for task: " + self.name,
                        subject=self.subject,
                        exception=traceback.format_exc(),
                    )
        if self.controller_type == ControllerEnum.BPOD:
            self.bpod.close()
        elif self.controller_type == ControllerEnum.ARDUINO:
            self.arduino.close()
        return save, duration, trials, water, settings_str

    def save_json(self, run_mode: str) -> str:
        """Saves the session settings to a JSON file.

        Args:
            run_mode (str): The execution mode string.

        Returns:
            str: The JSON string containing the settings.
        """

        dictionary: dict[str, Any] = {}

        default_properties_to_save = ["minimum_duration", "maximum_duration"]
        default_properties_to_not_save = [
            "next_task",
            "refractory_period",
            "observations",
        ]
        default_properties = default_properties_to_save + default_properties_to_not_save
        extra_properties = [
            prop for prop in vars(self.settings) if prop not in default_properties
        ]
        properties = default_properties_to_save + extra_properties

        for name in properties:
            if hasattr(self.settings, name):
                value = getattr(self.settings, name)
                dictionary[name] = value

        dictionary["run_mode"] = run_mode
        dictionary["observations"] = self.settings.observations
        json_string = json.dumps(dictionary)

        with open(self.session_settings_path, "w") as f:
            f.write(json_string)

        return json_string

    def save_csv(self, run_mode: str) -> Tuple[float, int, int, bool]:
        """Saves the session data to CSV files.

        Processes raw data, saves raw and clean session files, and updates the
        subject's cumulative data file.

        Args:
            run_mode (str): The execution mode string.

        Returns:
            Tuple[float, int, int, bool]: Duration, trial count, water consumed,
            and success status.
        """

        duration: float = 0.0
        trials: int = 0
        water: int = 0

        self.raw_df = pd.read_csv(self.rt_session_path, sep=";")

        if self.raw_df.shape[0] > 100000:
            log.alarm(
                "The session file is very large, probably due to"
                + " overdetections in some of the ports",
                subject=self.subject,
            )

        trials = int(self.raw_df["TRIAL"].iloc[-1])

        if trials > 1:
            non_nan_values = self.raw_df["START"].dropna()
            # sort it
            non_nan_values = non_nan_values.sort_values(ascending=True)

            if not non_nan_values.empty:
                duration = float(non_nan_values.iloc[-1] - non_nan_values.iloc[0])
                duration = round(duration, 4)

            self.raw_df.to_csv(self.raw_session_path, index=False, header=True, sep=";")

            trials = self.session_df.shape[0]

            try:
                water = int(self.session_df["water"].sum())
            except Exception:
                water = 0

            if water == 0 and settings.get("NO_WATER_DRUNK") == Active.ON:
                log.alarm(
                    "No water was drunk in task: " + self.name, subject=self.subject
                )

            self.session_df["run_mode"] = [run_mode] * self.session_df.shape[0]
            self.session_df.to_csv(self.session_path, header=True, index=False, sep=";")

            try:
                self.subject_df = pd.read_csv(
                    self.subject_path, sep=";", low_memory=False
                )

                self.session_df["session"] = [
                    int(self.subject_df["session"].iloc[-1]) + 1
                ] * self.session_df.shape[0]
                self.subject_df = pd.concat(
                    [self.subject_df, self.session_df], sort=True
                )
            except FileNotFoundError:
                self.session_df["session"] = [1] * self.session_df.shape[0]
                self.subject_df = self.session_df

            priority_columns = [
                "session",
                "date",
                "trial",
                "subject",
                "task",
                "system_name",
                "run_mode",
            ]
            reordered_columns = priority_columns + [
                col for col in self.subject_df.columns if col not in priority_columns
            ]
            self.subject_df = self.subject_df[reordered_columns]

            self.subject_df.to_csv(self.subject_path, header=True, index=False, sep=";")

            def safe_to_numeric(series) -> Any:
                try:
                    return pd.to_numeric(series)
                except Exception:
                    return series

            self.subject_df = self.subject_df.apply(safe_to_numeric)

            return duration, trials, water, True
        else:
            if settings.get("NO_TRIALS_PERFORMED") == Active.ON:
                log.alarm(
                    "No trials were recorded in task: " + self.name,
                    subject=self.subject,
                )
            return 0.0, 0, 0, False

    @classmethod
    def get_name(cls) -> str:
        """Returns the name of the task class."""
        name = cls.__name__
        if name == "Task":
            return "None"
        else:
            return name

    def create_paths(self) -> None:
        """Sets up file and directory paths for the session."""
        start_time = time_utils.now()
        self.date = time_utils.string_from_date(start_time)
        start_time_str = time_utils.filename_string_from_date(start_time)

        self.filename = str(self.subject) + "_" + str(self.name) + "_" + start_time_str
        self.rt_session_path = str(
            Path(settings.get("SESSIONS_DIRECTORY"), "session.csv")
        )

        directory = Path(settings.get("SESSIONS_DIRECTORY"), self.subject)
        if self.subject != "None":
            directory.mkdir(parents=True, exist_ok=True)
        self.sessions_directory = str(directory)

        directory = Path(settings.get("VIDEOS_DIRECTORY"), self.subject)
        if self.subject != "None":
            directory.mkdir(parents=True, exist_ok=True)
        self.video_directory = str(directory)

        self.raw_session_path = str(
            Path(self.sessions_directory, self.filename + "_RAW.csv")
        )
        self.session_path = str(Path(self.sessions_directory, self.filename + ".csv"))
        self.session_settings_path = str(
            Path(self.sessions_directory, self.filename + ".json")
        )

        self.video_path = str(Path(self.video_directory, self.filename + ".mp4"))
        self.video_data_path = str(Path(self.video_directory, self.filename + ".csv"))
        self.subject_path = str(Path(self.sessions_directory, self.subject + ".csv"))
