import json
import traceback
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable, Tuple

import pandas as pd

from village.classes.calibrations import Calibrations
from village.classes.enums import Active, ControllerEnum, Save
from village.classes.null_classes import NullCamera
from village.controllers.arduino_controller import arduino
from village.controllers.bpod_controller import bpod
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
    """Exception raised for errors in the TaskBase class."""

    def __init__(self, message) -> None:
        super().__init__(message)


class BpodEvent(EventName):
    """Enumeration of Bpod event names."""

    pass


class BpodOutput(OutputChannel):
    """Enumeration of Bpod output channels."""

    pass


class TaskBase:
    """Base class for defining behavioral tasks.

    Subclass ``TaskBase`` to implement your own task. You must override four methods
    and may optionally call helper methods and read certain attributes during
    execution.

    The task starts by calling ``start()``, then enters a loop where it calls
    ``create_trial()`` followed by ``after_trial()``. The loop continues until the
    maximum number of trials is reached, the maximum duration is exceeded,
    or ``force_stop`` is set to True. Finally, ``close()`` is called to
    clean up resources.


    ──────────────────────────────────────────────────────────
    METHODS YOU MUST OVERRIDE
    ──────────────────────────────────────────────────────────

    start(self)
        Called once before the trial loop begins.
        Use it to configure hardware, pre-compute stimuli, open files, etc.

    create_trial(self)
        Called at the beginning of every trial.
        If using Bpod: each call starts with an empty state machine. Add states
        with ``bpod.add_state`` and, when the method returns, the state machine
        is sent and run automatically. ``after_trial`` is called once it
        finishes.
        If not using Bpod: you are responsible for creating and running the
        trial logic yourself.

    after_trial(self)
        Called immediately after each trial finishes.
        Use it to score the animal's performance, update adaptive parameters,
        and call ``register_value`` to save whatever values you need for
        the trial.
        You must always register a ``water`` value with the amount of water
        consumed during the trial; the system sums it across the session to
        get the total water consumption. If that total falls below a
        configurable threshold, an alarm is triggered. The threshold can be
        adjusted in the Settings tab of the GUI.

    close(self)
        Called once after the trial loop ends (session finished, forced stop,
        or error).
        Use it to close files, stop hardware, release resources.

    ──────────────────────────────────────────────────────────
    METHODS YOU CAN CALL (do not override)
    ──────────────────────────────────────────────────────────

    register_start_trial(self, raspberry_timestamp: float, controller_timestamp: float)
        No need to call this if you are using a Bpod controller, it is called
        automatically.
        For other controllers, call this at the beginning of each trial to register
        the start of the trial.
        We use 2 timestamps because we use the start of the trial to synchronize the
        clocks between the raspberry and the controller.
        If you are not using a controller, (i.e. the controller is the same raspberry),
        the controller_timestamp is exactly the same as the raspberry timestamp.
        To get the raspberry timestamp you can use time_utils.now_timestamp().

    register_end_trial(self, controller_timestamp: float = 0.0)
        No need to call this if you are using a Bpod controller, it is called
        automatically.
        For other controllers, call this at the end of each trial to register the
        end of the trial.

    register_enter_state(self, state_name: str, controller_timestamp: float)
        No need to call this if you are using a Bpod controller, it is called
        automatically.
        For other controllers, call this when entering a state to register the
        entry into that state.

    register_controller_event(self, name: str, controller_timestamp: float)
        No need to call this if you are using a Bpod controller, it is called
        automatically.
        For other controllers, call this to register an event from the controller.

    register_raspberry_event(self, name: str, raspberry_timestamp: float)
        Call this to register an event from the raspberry, for example when executing
        direct functions or when using a camera to detect or trigger actions.

    register_value(self, name: str, value: Any)
        Saves a custom value to the current trial row in the CSV.
        Call this inside ``after_trial``.

        Example::

            self.register_value("correct", 1)
            self.register_value("response_time", 0.432)

    execute_function(self, i: int)
        Executes a registered function.

        Args:
            i (int): The function index (1-99).

        Example::
            self.execute_function(1)  # executes the function registered at index 1

    ──────────────────────────────────────────────────────────
    ATTRIBUTES YOU CAN READ INSIDE YOUR TASK
    ──────────────────────────────────────────────────────────

    self.name: str
        Name of the task.

    self.subject : str
        Name of the subject running the session.

    self.system_name : str
        Name of the system as defined in the settings tab of the GUI.

    self.bpod : BpodController
        Bpod interface (state machine construction, sending, etc.).
        Primarily used inside ``create_trial``.

    self.arduino : ArduinoController
        Arduino interface for tasks that use an Arduino instead of Bpod.

    self.settings : Settings
        Object that holds all the session parameters defined in the training
        protocol. Read and write its attributes to implement adaptive training.

    self.calibrations : Calibrations
        Object that holds the task's calibrations. Call its methods to convert
        between hardware values and real-world units.

        Example::

            gain = self.calibrations.sound_calibration.get_sound_gain(
                speaker=1, dB=70.0, sound_name="white_noise"
            )

    self.cam_box : Camera | NullCamera
        Camera attached to the operant box (NullCamera if not configured).

    self.current_trial : int
        The current trial number starting from 1

    self.trial_data : dict
        Dictionary populated automatically at the end of each trial.
        Available inside ``after_trial``.

        **Keys always present:**

        - ``"date"`` (str): date string of the session.
        - ``"trial"`` (int): current trial number.
        - ``"subject"`` (str): subject name.
        - ``"task"`` (str): task name.
        - ``"system_name"`` (str): system name from settings.
        - ``"TRIAL_START"`` (float): absolute timestamp (seconds, UNIX epoch)
          when the trial started.
        - ``"TRIAL_END"`` (float): absolute timestamp when the trial ended.
        - ``"ordered_list_of_events"`` (list[str]): event names in the order
          they occurred during the trial (e.g.
          ``["Port1In", "Port1Out", "Port1In"]``).

        **Keys added per state visited (Bpod or manual):**

        - ``"STATE_<name>_START"`` (list[float]): timestamps of every entry
          into that state. It is a list because the same state can be visited
          more than once in a single trial.
        - ``"STATE_<name>_END"`` (list[float]): timestamps of every exit from
          that state, paired with the corresponding START list.

        **Keys added per event type:**

        - ``"<EventName>"`` (list[float]): timestamps of every occurrence of
          that event (e.g. ``"Port1In"``, ``"Port1Out"``).

        When using Bpod all state and event keys are filled automatically.
        When not using Bpod, call ``register_enter_state`` and
        ``register_controller_event`` / ``register_raspberry_event`` yourself
        to populate them.

        **Keys added by you:**

        - Any name passed to ``register_value`` inside ``after_trial``.

        Example::

            def after_trial(self):
                if self.trial_data.get("correct") == 1:
                    self.settings.difficulty += 1
                t_start = self.trial_data["STATE_stimulus_START"][0]
                t_end = self.trial_data["STATE_stimulus_END"][0]
                response_time = t_end - t_start

    self.force_stop: bool
        Set this to True from inside your own task logic (e.g. in after_trial,
        once some in-task condition is met) to make the task stop.

    self.stop_button_pressed: bool
        True once something external (e.g. the STOP TASK button) has asked the
        task to stop. Unlike force_stop, you should not set this yourself --
        just read it if you want to react to it.

    self.should_stop: bool (read-only)
        True once ANY stopping condition is met: the trial/time limit (in
        Manual mode), force_stop, or stop_button_pressed. If your task does not use
        Bpod and create_trial contains its own waiting loop, check this
        property on every iteration so the loop actually exits when the task
        is asked to stop, instead of running forever:

        Example::

            def create_trial(self):
                while not self.should_stop:
                    ...  # wait for your own condition

    self.chrono: Chrono
        Using self.chrono.get_seconds() you can get the time in seconds since the
        task started.
    """

    def __init__(self) -> None:
        self.controller_type = ControllerEnum.RASPBERRY
        self.bpod = bpod
        self.arduino = arduino
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
        self.stop_button_pressed: bool = False
        self.run_mode: str = "Manual"
        self.maximum_number_of_trials: int = 100000000
        self.chrono = time_utils.Chrono()

        self.calibrations: Calibrations = Calibrations()

        self.current_x = 0.0
        self.current_y = 0.0

    # ----------------------------------------------------------------------------------
    # Top-level methods — OVERRIDE these in your task is required
    # ----------------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------------
    # Helper methods - you can call them from your task to register events and values
    # ----------------------------------------------------------------------------------

    # if you are using bpod the following methods are automatically called with
    # the correct timestamps, so you never need to call them yourself:
    # register_start_trial
    # register_end_trial
    # register_enter_state
    # register_controller_event

    def register_start_trial(
        self, raspberry_timestamp: float, controller_timestamp: float
    ) -> None:
        """Registers the start of a trial. We use 2 timestamps because we use the start
        of the trial to synchronize the clocks between the raspberry and the controller.
        If you are not using a controller, (i.e. the controller is the same raspberry),
        the controller_timestamp is exactly the same as the raspberry timestamp. To get
        the raspberry timestamp you can use time_utils.now_timestamp().

        Args:
            raspberry_timestamp (float): Raspberry time.
            controller_timestamp (float): Controller clock timestamp.
        """
        self.recorder.start_trial(raspberry_timestamp, controller_timestamp)

    def register_end_trial(self, controller_timestamp: float = 0.0) -> None:
        """Registers the end of a trial. If you are not using a controller, (i.e. the
        controller is the same raspberry), the controller_timestamp is exactly
        the same as the raspberry timestamp.
        Args:
            controller_timestamp (float): Controller clock timestamp.
        """
        self.recorder.end_trial(controller_timestamp)

    def register_enter_state(
        self, state_name: str, controller_timestamp: float
    ) -> None:
        """Registers the entry into a Bpod state.

        Args:
            state_name (str): The name of the state entered.
            controller_timestamp (float): Controller clock timestamp.
        """
        self.recorder.add_controller_event(f"enter_{state_name}", controller_timestamp)

    def register_controller_event(self, name: str, controller_timestamp: float) -> None:
        """Registers a custom event using a controller clock timestamp.

        Args:
            name (str): The name of the event (column header).
            controller_timestamp (float): Controller clock timestamp.
        """
        self.recorder.add_controller_event(name, controller_timestamp)

    # for bpod controller, arduino controller or raspberry pi controller, you can use
    # the following methods to register events and values
    def register_raspberry_event(self, name: str, raspberry_timestamp: float) -> None:
        """Registers a custom event using a raspberry timestamp.
        If you are using bpod, you may want to call this for events that are generated
        asynchronously from the bpod state machine, for example when executing direct
        functions or when using a camera to detect or trigger events.

        Args:
            name (str): The name of the event (column header).
            raspberry_timestamp (float): Raspberry time.
        """
        self.recorder.add_raspberry_event(name, raspberry_timestamp)

    def register_value(self, name: str, value: Any) -> None:
        """Registers a custom value to be saved with the trial data.

        Args:
            name (str): The name of the value (column header).
            value (Any): The value to store.
        """
        self.recorder.add_value(name, value)
        self.trial_data[name] = value

    def execute_function(self, i: int) -> None:
        """Executes a registered function.

        Args:
            i (int): The function index (1-99).
        """
        if 1 <= i <= 99:
            self.functions[i]()

    # ----------------------------------------------------------------------------------
    # Helper or private methods - you don't need to call or override them
    # ----------------------------------------------------------------------------------
    @property
    def should_stop(self) -> bool:
        """True once any stopping condition is met.

        Trial/time limits and force_stop are only checked BETWEEN trials, by
        run()'s own while loop -- they cannot interrupt a create_trial() that
        is currently blocked in its own waiting loop. Tasks that do not use
        Bpod and wait on their own condition inside create_trial should poll
        this property instead, so they actually exit when asked to.

        The trial limit only applies in Manual mode: Auto mode runs until the
        subject leaves the corridor, not for a fixed number of trials.
        """
        trial_limit_reached = (
            self.run_mode == "Manual"
            and self.current_trial > self.maximum_number_of_trials
        )
        return (
            trial_limit_reached
            or self.chrono.get_seconds() >= self.settings.maximum_duration
            or self.force_stop
            or self.stop_button_pressed
        )

    def run_in_thread(self, daemon: bool = True) -> None:
        """Runs the task in a separate background thread.

        Args:
            daemon (bool, optional): Whether to run as a daemon thread.
                Defaults to True.
        """

        def test_run():
            self.create_paths()
            self.start()
            while not self.should_stop:
                self.do_trial()
            self.disconnect_and_save("Manual")

        self.process = Thread(target=test_run, daemon=daemon)
        self.process.start()
        return

    def run(self) -> None:
        """Runs the task in the main thread until completion or forced stop."""
        self.chrono.reset()
        self.start()
        while not self.should_stop:
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
        try:
            self.close()
        except Exception:
            log.alarm(
                "Error closing the task: " + self.name,
                subject=self.subject,
                exception=traceback.format_exc(),
            )
        sound_device.stop()
        self.recorder.close()
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
        if name == "TaskBase":
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
