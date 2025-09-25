import importlib
import importlib.util
import inspect
import os
import sys
import traceback
from pathlib import Path
from threading import Thread
from typing import Callable

import numpy as np
import pandas as pd
import requests  # type: ignore

from village.classes.abstract_classes import BehaviorWindowBase, CameraBase
from village.classes.after_session import AfterSessionBase
from village.classes.change_cycle import ChangeCycleBase
from village.classes.collection import Collection
from village.classes.enums import (
    Actions,
    Active,
    Cycle,
    DataTable,
    Info,
    Save,
    State,
    SyncType,
)
from village.classes.plot import (
    OnlinePlotBase,
    SessionPlotBase,
    SubjectPlotBase,
)
from village.classes.subject import Subject
from village.classes.task import Task
from village.classes.training import TrainingProtocolBase
from village.devices.temp_sensor import temp_sensor
from village.log import log
from village.scripts import time_utils, utils
from village.settings import settings


class Manager:
    """
    Data class manages the state and operations related to the village data.

    Attributes:
        subject (Subject): Instance of Subject class.
        task (Task): Instance of Task class.
        training (Training): Instance of Training class.
        state (State): Current state of the system.
        table (DataTable): Data table type.
        rfid_reader (Active): RFID reader settings.
        cycle (Cycle): Current cycle settings.
        info (Info): Information settings.
        actions (Actions): Actions settings.
        cycle_text (str): Text representation of the current cycle.
        text (str): Current system text.
        day (bool): Indicates if it's day.
        changing_settings (bool): Indicates if settings are being changed.
        tasks (dict[str, type]): Dictionary of tasks.
        errors (str): Error messages.
        events (Collection): Collection of events.
        sessions_summary (Collection): Collection of session summaries.
        subjects (Collection): Collection of subjects.
        water_calibration (Collection): Collection of water calibration data.
        sound_calibration (Collection): Collection of sound calibration data.
        temperatures (Collection): Collection of temperature data.
        process (Thread): Thread for running tasks.
    """

    def __init__(self) -> None:
        self.subject = Subject()
        self.task = Task()
        self.training: TrainingProtocolBase = TrainingProtocolBase()
        self.subject_plot: SubjectPlotBase = SubjectPlotBase()
        self.session_plot: SessionPlotBase = SessionPlotBase()
        self.online_plot: OnlinePlotBase = OnlinePlotBase()
        self.after_session: AfterSessionBase = AfterSessionBase()
        self.change_cycle: ChangeCycleBase = ChangeCycleBase()
        self.state: State = State.WAIT
        self.previous_state_wait: bool = True
        self.error_stop: bool = False
        self.calibrating: bool = False
        self.table: DataTable = DataTable.EVENTS
        self.rfid_reader: Active = settings.get("RFID_READER")
        self.cycle: Cycle = settings.get("CYCLE")
        self.info: Info = settings.get("INFO")
        self.actions: Actions = settings.get("ACTIONS")
        self.cycle_text: str = ""
        self.text: str = ""
        self.day: bool = True
        self.weight: float = np.nan
        self.changing_settings: bool = False
        self.tasks: dict[str, type] = dict()
        self.errors: str = ""
        self.max_time_counter: int = 1
        self.functions: list[Callable] = [lambda: None for _ in range(99)]
        self.sound_calibration_functions: list[Callable] = []
        self.sound_calibration_error: bool = False
        self.raw_session_df = pd.DataFrame()
        self.old_session_df = pd.DataFrame()
        self.old_session_raw_df = pd.DataFrame()
        self.rt_session_path = str(
            Path(settings.get("SESSIONS_DIRECTORY"), "session.csv")
        )

        self.update_cycle()
        utils.create_directories()
        self.create_collections()
        log.event = self.events
        log.temp = self.temperatures
        utils.download_github_repository(settings.get("GITHUB_REPOSITORY_EXAMPLE"))
        self.detections = time_utils.TimestampTracker(
            hours=int(settings.get("NO_DETECTION_HOURS"))
        )
        self.sessions = time_utils.TimestampTracker(
            hours=int(settings.get("NO_SESSION_HOURS"))
        )
        self.hour_change_detector = time_utils.HourChangeDetector()
        self.cycle_change_detector = time_utils.CycleChangeDetector(
            settings.get("DAYTIME"), settings.get("NIGHTTIME")
        )
        self.detection_change = True
        self.error_in_manual_task = False
        self.rfid_changed = False
        self.change_cycle_flag = False
        self.after_session_flag = False
        self.getting_weights = False
        self.measuring_weight_list: list[float] = []
        self.log_weight = False
        self.taring_scale = False

        self.healthchecks_url = settings.get("HEALTHCHECKS_URL")

        self.behavior_window = BehaviorWindowBase()

    def create_collections(self) -> None:
        self.events = Collection(
            "events", ["date", "type", "subject", "description"], [str, str, str, str]
        )
        self.sessions_summary = Collection(
            "sessions_summary",
            [
                "date",
                "subject",
                "tag",
                "weight",
                "task",
                "duration",
                "trials",
                "water",
                "settings",
            ],
            [str, str, str, float, str, float, int, float, str],
        )
        self.subjects = Collection(
            "subjects",
            [
                "name",
                "tag",
                "basal_weight",
                "active",
                "next_session_time",
                "next_settings",
            ],
            [str, str, float, str, str, str],
        )
        self.water_calibration = Collection(
            "water_calibration",
            [
                "date",
                "port_number",
                "time(s)",
                "water_delivered(ul)",
                "calibration_number",
                "water_expected(ul)",
                "error(%)",
            ],
            [str, int, float, float, int, float, float],
        )
        self.sound_calibration = Collection(
            "sound_calibration",
            [
                "date",
                "speaker",
                "sound_name",
                "gain",
                "dB_obtained",
                "calibration_number",
                "dB_expected",
                "error(%)",
            ],
            [str, int, str, float, float, int, float, float],
        )
        self.temperatures = Collection(
            "temperatures",
            ["date", "temperature", "humidity"],
            [str, float, float],
        )
        self.deleted_sessions = Collection(
            "deleted_sessions",
            [
                "filename",
            ],
            [str],
        )

    def import_all_tasks(self) -> None:
        directory = settings.get("CODE_DIRECTORY")
        sys.path.append(directory)

        python_files: list[str] = []
        tasks = dict()
        training_found = 0
        session_plot_found = 0
        subject_plot_found = 0
        online_plot_found = 0
        after_session_found = 0
        change_cycle_found = 0
        training_correct = False
        session_plot_correct = False
        subject_plot_correct = False
        online_plot_correct = False
        after_session_correct = False
        change_cycle_correct = False
        functions_path = ""
        sound_path = ""

        for root, _, files in os.walk(directory):
            for file in files:
                if file == "softcode_functions.py":
                    functions_path = os.path.join(root, file)
                if file == "sound_functions.py":
                    sound_path = os.path.join(root, file)
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        if os.path.exists(functions_path):
            module_name = "custom_module"
            spec = importlib.util.spec_from_file_location(module_name, functions_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    for i in range(1, 100):
                        func_name = f"function{i}"
                        if hasattr(module, func_name):
                            self.functions[i] = getattr(module, func_name)
                except Exception:
                    log.error(
                        "Couldn't import softcode functions",
                        exception=traceback.format_exc(),
                    )

        if os.path.exists(sound_path):
            module_name = "custom_module2"
            spec = importlib.util.spec_from_file_location(module_name, sound_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    if hasattr(module, "sound_calibration_functions"):
                        self.sound_calibration_functions = getattr(
                            module, "sound_calibration_functions"
                        )
                except Exception:
                    log.error(
                        "Couldn't import sound calibration functions",
                        exception=traceback.format_exc(),
                    )

        for python_file in python_files:
            relative_path = os.path.relpath(python_file, directory)
            module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]
            try:
                module = importlib.import_module(module_name)
                clsmembers = inspect.getmembers(module, inspect.isclass)
                for _, cls in clsmembers:
                    if cls.__module__ != module_name:
                        continue

                    if issubclass(cls, Task) and cls != Task:
                        name = cls.__name__
                        _ = cls()
                        if name not in tasks:
                            tasks[name] = cls
                    elif (
                        issubclass(cls, TrainingProtocolBase)
                        and cls != TrainingProtocolBase
                    ):
                        training_found += 1
                        if training_found == 1:
                            t = cls()
                            t.copy_settings()
                            self.training = t
                            training_correct = True
                    elif issubclass(cls, SessionPlotBase) and cls != SessionPlotBase:
                        session_plot_found += 1
                        if session_plot_found == 1:
                            p = cls()
                            self.session_plot = p
                            session_plot_correct = True
                    elif issubclass(cls, SubjectPlotBase) and cls != SubjectPlotBase:
                        subject_plot_found += 1
                        if subject_plot_found == 1:
                            s = cls()
                            self.subject_plot = s
                            subject_plot_correct = True
                    elif issubclass(cls, OnlinePlotBase) and cls != OnlinePlotBase:
                        online_plot_found += 1
                        if online_plot_found == 1:
                            o = cls()
                            self.online_plot = o
                            online_plot_correct = True
                    elif issubclass(cls, AfterSessionBase) and cls != AfterSessionBase:
                        after_session_found += 1
                        if after_session_found == 1:
                            a = cls()
                            self.after_session = a
                            after_session_correct = True
                    elif issubclass(cls, ChangeCycleBase) and cls != ChangeCycleBase:
                        change_cycle_found += 1
                        if change_cycle_found == 1:
                            y = cls()
                            self.change_cycle = y
                            change_cycle_correct = True

            except Exception:
                log.error(
                    "Couldn't import " + module_name, exception=traceback.format_exc()
                )
                continue
        if training_found == 0:
            log.error("Training protocol not found")
        elif training_found == 1 and training_correct:
            log.info("Training protocol successfully imported")
        elif training_found > 1:
            log.error("Multiple training protocols found")
        if session_plot_found == 0:
            log.info("Custom Session plot not found, using default")
        elif session_plot_found == 1 and session_plot_correct:
            log.info("Custom Session plot successfully imported")
        elif session_plot_found > 1:
            log.error("Multiple session plots found")
        if subject_plot_found == 0:
            log.info("Custom Subject plot not found, using default")
        elif subject_plot_found == 1 and subject_plot_correct:
            log.info("Custom Subject plot successfully imported")
        elif subject_plot_found > 1:
            log.error("Multiple subject plots found")
        if online_plot_found == 0:
            log.info("Custom Online plot not found, using default")
        elif online_plot_found == 1 and online_plot_correct:
            log.info("Custom Online plot successfully imported")
        elif online_plot_found > 1:
            log.error("Multiple online plots found")
        if after_session_found == 0:
            log.info("Custom After Session Run not found, using default")
        elif after_session_found == 1 and after_session_correct:
            log.info("Custom After Session Run successfully imported")
        elif after_session_found > 1:
            log.error("Multiple After Session Run found")
        if change_cycle_found == 0:
            log.info("Custom Change Cycle Run not found, using default")
        elif change_cycle_found == 1 and change_cycle_correct:
            log.info("Custom Change Cycle Run successfully imported")
        elif change_cycle_found > 1:
            log.error("Multiple Change Cycle Run found")
        self.tasks = dict(sorted(tasks.items()))
        number_of_tasks = len(tasks)
        if number_of_tasks == 0:
            log.error("No tasks could be imported")
        elif number_of_tasks == 1:
            log.info("1 task successfully imported")
        else:
            log.info(str(number_of_tasks) + " tasks successfully imported")

    def get_subject_from_tag(self, tag: str) -> bool:
        subject_series = self.subjects.get_last_entry(column="tag", value=tag)

        if subject_series is None:
            log.error("Subject with tag: " + tag + " not found")
            return False
        else:
            self.subject.subject_series = subject_series
            return True

    def update_cycle(self) -> None:
        match self.cycle:
            case self.cycle.DAY:
                self.cycle_text = "DAY"
                self.day = True
            case self.cycle.NIGHT:
                self.cycle_text = "NIGHT"
                self.day = False
            case self.cycle.AUTO:
                day = time_utils.time_from_setting_string(settings.get("DAYTIME"))
                night = time_utils.time_from_setting_string(settings.get("NIGHTTIME"))
                now = time_utils.now().time()

                if day < night:
                    if day < now < night:
                        self.cycle_text = "AUTO (DAY)"
                        self.day = True
                    else:
                        self.cycle_text = "AUTO (NIGHT)"
                        self.day = False
                else:
                    if day < now or now < night:
                        self.cycle_text = "AUTO (DAY)"
                        self.day = True
                    else:
                        self.cycle_text = "AUTO (NIGHT)"
                        self.day = False

    def update_text(self) -> None:
        state_name = self.state.name
        state_description = self.state.description
        subject_name = self.subject.name
        task_name = self.task.name
        rfid_reader_name = self.rfid_reader.name
        cycle_text = self.cycle_text

        self.text = (
            "     SYSTEM STATE: "
            + state_name
            + " ("
            + state_description
            + ")                    "
            + "SUBJECT: "
            + subject_name
            + "                    "
            + "TASK: "
            + task_name
            + "                    "
            + "RFID_READER: "
            + rfid_reader_name
            + "                    "
            + "CYCLE: "
            + cycle_text
        )

    def multiple_detections(self, multiple: bool) -> bool:
        if multiple:
            log.info(
                "Multiple tags detected in the last seconds",
                subject=self.subject.name,
            )
            return True
        return False

    def launch_task_manual(self, cam: CameraBase) -> bool:
        self.task.create_paths()
        self.task.cam_box = cam
        self.task.water_calibration = self.water_calibration
        self.task.sound_calibration = self.sound_calibration
        if self.subject.name != "None":
            self.task.cam_box.start_recording(
                self.task.video_path, self.task.video_data_path
            )
        else:
            self.task.cam_box.show_time_info = True
        try:
            self.weight = np.nan
            log.start(task=self.task.name, subject=self.subject.name)
            self.run_task_in_thread()
            return True
        except Exception:
            log.error(
                "Error running task " + self.task.name,
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            self.error_in_manual_task = True
            return False

    def launch_task_auto(self, cam: CameraBase) -> bool:
        try:
            self.weight = np.nan
            self.training.load_settings_from_jsonstring(self.subject.next_settings)
            task_name = self.training.settings.next_task
            cls = self.tasks.get(task_name)
            if cls is None:
                log.alarm(
                    "Error running task: "
                    + task_name
                    + " not found. Opening door2 and disconnecting RFID reader.",
                    subject=self.subject.name,
                )
                return False
            elif issubclass(cls, Task):
                self.task = cls()
                self.task.subject = self.subject.name
                self.task.settings = self.training.settings
                self.task.training = self.training
                self.task.create_paths()
                self.task.cam_box = cam
                self.task.cam_box.start_recording(
                    self.task.video_path, self.task.video_data_path
                )
                self.task.maximum_number_of_trials = 100000000
                self.task.water_calibration = self.water_calibration
                self.task.sound_calibration = self.sound_calibration
                log.start(task=task_name, subject=self.subject.name)
                self.run_task_in_thread()
                return True
            else:
                log.alarm(
                    "Error running task: "
                    + task_name
                    + " is not a subclass of Task."
                    + " Opening door2 and disconnecting RFID reader.",
                    subject=self.subject.name,
                )
                return False
        except Exception:
            log.alarm(
                "Error running task: "
                + task_name
                + " Opening door2 and disconnecting RFID reader.",
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            return False

    def run_task_in_thread(self) -> None:
        self.process = Thread(target=self.run_task, daemon=True)
        self.process.start()

    def run_task(self) -> None:
        try:
            self.task.bpod.connect(self.functions)
            self.task.run()
        except Exception:
            if self.state in [State.LAUNCH_MANUAL, State.RUN_MANUAL]:
                log.error(
                    "Error running task " + self.task.name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                self.error_in_manual_task = True
                self.state = State.SAVE_MANUAL
            elif self.state in [
                State.LAUNCH_AUTO,
                State.RUN_FIRST,
                State.RUN_OPENED,
                State.RUN_CLOSED,
                State.OPEN_DOOR2,
                State.CLOSE_DOOR2,
            ]:
                log.alarm(
                    "Error running task "
                    + self.task.name
                    + " Opening door2 and disconnecting RFID reader.",
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                self.state = State.OPEN_DOOR2_STOP
                log.info("Going to OPEN_DOOR2_STOP State")

    def reset_subject_task_training(self) -> None:
        self.task = Task()
        self.subject = Subject()
        self.training.restore()
        self.max_time_counter = 1
        self.last_line_raw_df = 0
        self.raw_session_df = pd.DataFrame()
        self.calibrating = False
        self.previous_state_wait = True
        self.error_stop = False

    def update_raw_session_df(self) -> pd.DataFrame:
        try:
            self.raw_session_df = pd.read_csv(
                self.rt_session_path,
                sep=";",
            )
        except Exception:
            self.raw_session_df = pd.DataFrame()
        return self.raw_session_df

    def get_both_sessions_dfs(self) -> list[pd.DataFrame]:
        raw_df = self.update_raw_session_df()
        return [raw_df, self.task.session_df]

    def disconnect_and_save(self, run_mode: str) -> None:
        # TODO kill the touchscreen reading
        self.behavior_window.load_draw_function(None)
        self.behavior_window.stop_drawing()
        save, duration, trials, water, settings_str = self.task.disconnect_and_save(
            run_mode
        )
        if save != Save.NO:
            self.save_to_sessions_summary(duration, trials, water, settings_str)
            if save == Save.YES:
                try:
                    self.save_to_subjects()
                    log.info("Session and video data saved.", subject=self.subject.name)
                except Exception:
                    log.alarm(
                        "Error updating the training settings for task: "
                        + self.task.name,
                        subject=self.subject.name,
                        exception=traceback.format_exc(),
                    )
            else:
                try:
                    self.save_refractory_to_subjects()
                except Exception:
                    log.alarm(
                        "Error updating the training settings for task: "
                        + self.task.name,
                        subject=self.subject.name,
                        exception=traceback.format_exc(),
                    )

        log.end(task=self.task.name, subject=self.subject.name)
        self.sessions.add_timestamp()
        self.after_session_flag = True

    def save_to_subjects(self) -> None:
        df = self.subjects.df.copy()
        self.training.settings = self.task.settings
        next_settings = self.training.get_jsonstring(exclude=["observations"])
        df.loc[df["name"] == self.subject.name, "next_settings"] = next_settings

        time_val = time_utils.time_in_future_seconds(
            int(self.training.settings.refractory_period)
        )
        time_str = time_utils.string_from_date(time_val)
        df.loc[df["name"] == self.subject.name, "next_session_time"] = time_str
        self.subjects.df = df
        self.subjects.save_from_df(self.training)

    def save_refractory_to_subjects(self) -> None:
        df = self.subjects.df.copy()
        time_val = time_utils.time_in_future_seconds(
            int(self.training.settings.refractory_period)
        )
        time_str = time_utils.string_from_date(time_val)
        df.loc[df["name"] == self.subject.name, "next_session_time"] = time_str
        self.subjects.df = df
        self.subjects.save_from_df(self.training)

    def save_to_sessions_summary(
        self, duration: float, trials: int, water: int, settings_used_str: str
    ) -> None:

        self.sessions_summary.add_entry(
            [
                self.task.date,
                self.subject.name,
                self.subject.tag,
                self.weight,
                self.task.name,
                duration,
                trials,
                water,
                settings_used_str,
            ]
        )

    def cycle_checks(self) -> None:
        text, non_det_subs, non_ses_subs, low_water_subs, sync = self.create_report(24)
        log.alarm(text, report=True)
        if (
            len(non_det_subs) > 0
            and settings.get("NO_DETECTION_SUBJECT_24H") == Active.ON
        ):
            log.alarm("No detections in the last 24 hours: " + ", ".join(non_det_subs))
        if (
            len(non_ses_subs) > 0
            and settings.get("NO_SESSION_SUBJECT_24H") == Active.ON
        ):
            log.alarm("No sessions in the last 24 hours: " + ", ".join(non_ses_subs))
        if len(low_water_subs) > 0:
            log.alarm(
                "Low water consumption in the last 24 hours: "
                + ", ".join(low_water_subs)
            )
        if not sync and settings.get("SYNC_TYPE") != SyncType.OFF:
            log.alarm("No sync in the last 24 hours.")
        self.change_cycle_flag = True

    def create_report(
        self, hours: int
    ) -> tuple[str, list[str], list[str], list[str], bool]:
        minimum_water = float(settings.get("MINIMUM_WATER_SUBJECT_24H"))
        events = self.events.df.copy()
        subjects = self.subjects.df.copy()
        sessions_summary = self.sessions_summary.df.copy()

        events["date"] = pd.to_datetime(events["date"])
        sessions_summary["date"] = pd.to_datetime(sessions_summary["date"])

        time_hours_ago = time_utils.hours_ago(hours)

        detections = events[
            (events["description"] == "Subject detected")
            & (events["date"] >= time_hours_ago)
        ]
        sessions = events[
            (events["type"] == "START") & (events["date"] >= time_hours_ago)
        ]
        syncs = events[
            (events["description"] == "Sync completed successfully")
            & (events["date"] >= time_hours_ago)
        ]
        sync = True
        if len(syncs) == 0 and len(sessions) > 0:
            sync = False

        sessions_summary = sessions_summary[sessions_summary["date"] >= time_hours_ago]

        subject_detections = detections.groupby("subject").size().to_dict()
        subject_sessions = sessions.groupby("subject").size().to_dict()
        subject_water = sessions_summary.groupby("subject")["water"].sum().to_dict()
        subject_weight = sessions_summary.groupby("subject")["weight"].mean().to_dict()

        active_subjects = subjects.loc[
            subjects["active"].apply(utils.is_active), "name"
        ].tolist()
        active_hours = utils.calculate_active_hours(subjects)

        report_text = "REPORT last " + str(hours) + "h\n\n"
        report_text += "state: " + self.state.name + ", subject: " + self.subject.name
        report_text += "\n\n"
        report_text += "subject, detections, sessions, water, weight\n"

        non_detected_subjects = []
        non_session_subjects = []
        low_water_subjects = []

        for sub in active_subjects:
            try:
                detections_str = str(subject_detections[sub])
            except KeyError:
                detections_str = "0"
                if active_hours[sub] >= 23:
                    non_detected_subjects.append(sub)
            try:
                sessions_str = str(subject_sessions[sub])
            except KeyError:
                sessions_str = "0"
                if active_hours[sub] >= 23:
                    non_session_subjects.append(sub)
            try:
                water = subject_water[sub]
                water_str = str(int(water))
            except KeyError:
                water = 0
                water_str = "0"
            if active_hours[sub] >= 23 and water < minimum_water:
                low_water_subjects.append(sub)
            try:
                weight_str = str(round(subject_weight[sub], 2))
            except KeyError:
                weight_str = "0"
            report_text += (
                sub
                + ", "
                + detections_str
                + ", "
                + sessions_str
                + ", "
                + water_str
                + ", "
                + weight_str
                + "\n"
            )
        return (
            report_text,
            non_detected_subjects,
            non_session_subjects,
            low_water_subjects,
            sync,
        )

    def send_heartbeat(self) -> None:
        if self.healthchecks_url == "":
            return
        try:
            requests.get(self.healthchecks_url, timeout=10)
        except Exception:
            pass

    def hourly_checks(self) -> None:
        temp, _, temp_string = temp_sensor.get_temperature()
        if temp > float(settings.get("MAXIMUM_TEMPERATURE")):
            log.alarm("Temperature above maximum: " + temp_string)
        elif temp < float(settings.get("MINIMUM_TEMPERATURE")):
            log.alarm("Temperature below minimum: " + temp_string)

        if self.detections.trigger_empty():
            value = str(self.detections.hours)
            log.alarm("No subjects detected in the last " + value + " hours")

        if self.sessions.trigger_empty():
            value = str(self.sessions.hours)
            log.alarm("No sessions performed in the last " + value + " hours")

        if utils.has_low_disk_space():
            log.alarm("Low disk space (less than 10GB)")

        self.send_heartbeat()


manager = Manager()
