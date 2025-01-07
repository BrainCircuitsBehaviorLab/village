import importlib
import importlib.util
import inspect
import os
import subprocess
import sys
import traceback
from pathlib import Path
from threading import Thread
from typing import Callable

import numpy as np
import pandas as pd
import sounddevice as sd
from PyQt5.QtWidgets import QLayout

from village.classes.collection import Collection
from village.classes.enums import Actions, Active, Cycle, DataTable, Info, State
from village.classes.plot import SessionPlot, SubjectPlot
from village.classes.protocols import CameraProtocol
from village.classes.subject import Subject
from village.classes.task import Task
from village.classes.training import Training
from village.log import log
from village.settings import settings
from village.time_utils import time_utils


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
        self.training: Training = Training()
        self.subject_plot: SubjectPlot = SubjectPlot()
        self.session_plot: SessionPlot = SessionPlot()
        self.state: State = State.WAIT
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
        self.session_df = pd.DataFrame()
        self.old_session_df = pd.DataFrame()
        self.old_session_raw_df = pd.DataFrame()
        self.rt_session_path = str(
            Path(settings.get("SESSIONS_DIRECTORY"), "session.csv")
        )

        self.update_cycle()
        self.create_directories()
        self.create_collections()
        log.event_protocol = self.events
        self.download_github_repository(settings.get("GITHUB_REPOSITORY_EXAMPLE"))

    @staticmethod
    def change_directory_settings(new_path: str) -> None:
        settings.set("PROJECT_DIRECTORY", new_path)
        settings.set("DATA_DIRECTORY", str(Path(new_path, "data")))
        settings.set("SESSIONS_DIRECTORY", str(Path(new_path, "data", "sessions")))
        settings.set("VIDEOS_DIRECTORY", str(Path(new_path, "data", "videos")))
        settings.set("CODE_DIRECTORY", str(Path(new_path, "code")))

    @staticmethod
    def create_directories() -> None:
        directory = Path(settings.get("PROJECT_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("DATA_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("SESSIONS_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("VIDEOS_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("CODE_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_directories_from_path(p: str) -> bool:
        try:
            path = Path(p)
            path.mkdir(parents=True, exist_ok=True)
            data = Path(path, "data")
            data.mkdir(parents=True, exist_ok=True)
            sessions = Path(data, "sessions")
            sessions.mkdir(parents=True, exist_ok=True)
            videos = Path(data, "videos")
            videos.mkdir(parents=True, exist_ok=True)
            code = Path(path, "code")
            code.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def download_github_repository(repository: str) -> None:
        directory = Path(settings.get("CODE_DIRECTORY"))
        default_directory = Path(settings.get("DEFAULT_CODE_DIRECTORY"))
        if len(os.listdir(directory)) == 0 and directory == default_directory:
            directory.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(["git", "clone", repository, directory])
                log.info("Repository " + repository + " downloaded")
            except Exception:
                log.error(
                    "Error downloading repository " + repository,
                    exception=traceback.format_exc(),
                )

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
                "target(ul)",
                "first_volume(ul)",
                "volume(ul)",
                "time(ms)",
            ],
            [str, int, float, float, float, float],
        )
        self.sound_calibration = Collection(
            "sound_calibration",
            ["date", "speaker", "target(dB)", "first_volume(dB)", "volume(dB)", "amp"],
            [str, str, float, float, float, float],
        )
        self.temperatures = Collection(
            "temperatures",
            ["date", "temperature", "humidity"],
            [str, float, float],
        )

    def import_all_tasks(self) -> None:
        directory = settings.get("CODE_DIRECTORY")
        sys.path.append(directory)

        python_files: list[str] = []
        tasks = dict()
        training_found = 0
        session_plot_found = 0
        subject_plot_found = 0
        functions_path = ""

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file == "functions.py":
                    functions_path = os.path.join(root, file)
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
                        "Couldn't import user functions",
                        exception=traceback.format_exc(),
                    )

        for python_file in python_files:
            relative_path = os.path.relpath(python_file, directory)
            module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]
            try:
                module = importlib.import_module(module_name)
                clsmembers = inspect.getmembers(module, inspect.isclass)
                for _, cls in clsmembers:
                    if issubclass(cls, Task) and cls != Task:
                        name = cls.__name__
                        _ = cls()
                        if name not in tasks:
                            tasks[name] = cls
                    elif issubclass(cls, Training) and cls != Training:
                        training_found += 1
                        if training_found == 1:
                            t = cls()
                            t.copy_settings()
                            self.training = t
                    elif issubclass(cls, SessionPlot) and cls != SessionPlot:
                        session_plot_found += 1
                        if session_plot_found == 1:
                            p = cls()
                            self.session_plot = p
                    elif issubclass(cls, SubjectPlot) and cls != SubjectPlot:
                        subject_plot_found += 1
                        if subject_plot_found == 1:
                            s = cls()
                            self.subject_plot = s
            except Exception:
                log.error(
                    "Couldn't import " + module_name, exception=traceback.format_exc()
                )
                continue
        if training_found == 0:
            log.error("Training protocol not found")
        elif training_found == 1:
            log.info("Training protocol successfully imported")
        else:
            log.error("Multiple training protocols found")
        if session_plot_found == 0:
            log.error("Custom Session plot not found, using default")
        elif session_plot_found == 1:
            log.info("Custom Session plot successfully imported")
        else:
            log.error("Multiple session plots found")
        if subject_plot_found == 0:
            log.error("Custom Subject plot not found, using default")
        elif subject_plot_found == 1:
            log.info("Custom Subject plot successfully imported")
        else:
            log.error("Multiple subject plots found")
        self.tasks = dict(sorted(tasks.items()))
        number_of_tasks = len(tasks)
        if number_of_tasks == 1:
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
                day = time_utils.date_from_setting_string(
                    settings.get("DAYTIME")
                ).time()
                night = time_utils.date_from_setting_string(
                    settings.get("NIGHTTIME")
                ).time()
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
            "SYSTEM STATE: "
            + state_name
            + " ("
            + state_description
            + ")     //////     "
            + "SUBJECT: "
            + subject_name
            + "     //////     "
            + "TASK: "
            + task_name
            + "     //////     "
            + "RFID_READER: "
            + rfid_reader_name
            + "     //////     "
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

    def delete_all_elements(self, layout: QLayout) -> None:
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem is not None:
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.deleteLater()
                else:
                    if layoutItem.layout() is not None:
                        self.delete_all_elements(layoutItem.layout())

    @staticmethod
    def get_sound_devices() -> list[str]:
        devices = sd.query_devices()
        devices_str = [d["name"] for d in devices]
        return devices_str

    def launch_task_manual(self, cam: CameraProtocol) -> bool:
        self.task.create_paths()
        self.task.cam_box = cam
        if self.subject.name != "None":
            self.task.cam_box.start_record(
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
                "Error launching task " + self.task.name,
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            return False

    def launch_task_auto(self, cam: CameraProtocol) -> bool:
        self.task.create_paths()
        if self.subject != "None":
            self.task.cam_box = cam
            self.task.cam_box.start_record(
                self.task.video_path, self.task.video_data_path
            )
        try:
            self.weight = np.nan
            self.training.load_settings_from_jsonstring(self.subject.next_settings)
            task_name = self.training.settings.next_task
            cls = self.tasks.get(task_name)
            if cls is None:
                log.alarm(
                    "Error launching task: "
                    + task_name
                    + " not found. Disconnecting RFID Reader.",
                    subject=self.subject.name,
                )
                return False
            elif issubclass(cls, Task):
                self.task = cls()
                self.task.subject = self.subject.name
                self.task.settings = self.training.settings
                self.task.training = self.training
                log.start(task=task_name, subject=self.subject.name)
                self.run_task_in_thread()
                return True
            else:
                log.alarm(
                    "Error launching task: "
                    + task_name
                    + " is not a subclass of Task. Disconnecting RFID Reader.",
                    subject=self.subject.name,
                )
                return False
        except Exception:
            log.alarm(
                "Error launching task: " + task_name + " Disconnecting RFID Reader.",
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            return False

    def run_task_in_thread(self) -> None:
        self.process = Thread(target=self.run_task, daemon=True)
        self.process.start()

    def run_task(self) -> None:
        try:
            self.task.bpod.reconnect(self.functions)
            self.task.run()
        except Exception:
            if self.state in [State.LAUNCH_MANUAL, State.RUN_MANUAL]:
                log.error(
                    "Error running task " + self.task.name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
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
                    + " Disconnecting RFID Reader.",
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                self.state = State.OPEN_DOOR2_STOP
        finally:
            self.task.close()

    def reset_subject_task_training(self) -> None:
        self.task = Task()
        self.subject = Subject()
        self.training.restore()
        self.max_time_counter = 1

    def update_session_df(self) -> pd.DataFrame:
        try:
            self.session_df = pd.read_csv(self.rt_session_path, sep=";")
        except Exception:
            self.session_df = pd.DataFrame()
        return self.session_df

    def get_both_sessions_dfs(self) -> list[pd.DataFrame]:
        df = self.update_session_df()
        df2 = self.task.transform(df)
        return [df, df2]

    def disconnect_and_save(self, run_mode: str) -> None:
        save, duration, trials, water, settings_str = self.task.disconnect_and_save(
            run_mode
        )
        if save:
            self.save_to_sessions_summary(duration, trials, water, settings_str)
        log.end(task=self.task.name, subject=self.subject.name)

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


manager = Manager()
