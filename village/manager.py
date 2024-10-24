import importlib
import inspect
import os
import subprocess
import sys
import traceback
from pathlib import Path
from threading import Thread

import sounddevice as sd
from PyQt5.QtWidgets import QLayout

from village.classes.collection import Collection
from village.classes.enums import Actions, Active, Cycle, DataTable, Info, State
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
        tag_reader (Active): Tag reader settings.
        cycle (Cycle): Current cycle settings.
        info (Info): Information settings.
        actions (Actions): Actions settings.
        cycle_text (str): Text representation of the current cycle.
        text (str): Current system text.
        old_text (str): Previous system text.
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
        self.state: State = State.WAIT
        self.table: DataTable = DataTable.EVENTS
        self.tag_reader: Active = settings.get("TAG_READER")
        self.cycle: Cycle = settings.get("CYCLE")
        self.info: Info = settings.get("INFO")
        self.actions: Actions = settings.get("ACTIONS")
        self.cycle_text: str = ""
        self.text: str = ""
        self.old_text: str = ""
        self.day: bool = True
        self.changing_settings: bool = False
        self.tasks: dict[str, type] = dict()
        self.errors: str = ""

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

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

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
                        if training_found == 0:
                            training_found += 1
                            t = cls()
                            t.copy_settings()
                            self.training = t
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
        # self.tasks = tasks
        self.tasks = dict(sorted(tasks.items()))
        number_of_tasks = len(tasks)
        if number_of_tasks == 1:
            log.info("1 task successfully imported")
        else:
            log.info(str(number_of_tasks) + " tasks successfully imported")

    def get_subject_from_tag(self, tag: str) -> bool:
        subject_series = self.subjects.get_last_entry(column="tag", value=tag)

        if subject_series is None:
            log.error("subject with tag: " + tag + " not found")
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

    def update_text(self) -> bool:
        state_name = self.state.name
        state_description = self.state.description
        subject_name = self.subject.name
        task_name = self.task.name
        tag_reader_name = self.tag_reader.name
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
            + "TAG_READER: "
            + tag_reader_name
            + "     //////     "
            + "CYCLE: "
            + cycle_text
        )

        value = self.text != self.old_text
        self.old_text = self.text
        return value

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

    def launch_task_manual(self) -> bool:
        try:
            self.run_task_in_thread()
            return True
        except Exception:
            log.alarm(
                "Error launching task " + self.task.name,
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            return False

    def launch_task_auto(self) -> bool:
        try:
            manager.training.load_settings_from_jsonstring(self.subject.next_settings)
            task_name = manager.training.settings.next_task
            cls = self.tasks.get(task_name)
            if cls is None:
                log.error(
                    "Task: " + task_name + " not found", subject=self.subject.name
                )
                return False
            elif issubclass(cls, Task):
                self.task = cls()
                self.task.subject = self.subject.name
                self.task.settings = manager.training.settings
                self.run_task_in_thread()
                return True
            else:
                log.alarm(
                    "Task: " + task_name + " is not a subclass of Task",
                    subject=self.subject.name,
                )
                return False
        except Exception:
            log.alarm(
                "Error launching task " + task_name,
                subject=self.subject.name,
                exception=traceback.format_exc(),
            )
            return False

    def run_task_in_thread(self) -> None:
        self.process = Thread(target=self.run_task, daemon=True)
        self.process.start()

    def run_task(self) -> None:
        try:
            self.task.run()
        except Exception:
            if self.state in [State.LAUNCH_MANUAL, State.RUN_MANUAL]:
                log.alarm(
                    "Error running task " + self.task.name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                manager.state = State.SAVE_MANUAL
            elif manager.state in [
                State.LAUNCH_AUTO,
                State.RUN_ACTION,
                State.RUN_OPENED,
                State.RUN_CLOSED,
                State.OPEN_DOOR2,
                State.CLOSE_DOOR2,
            ]:
                log.alarm(
                    "Error running task " + self.task.name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                manager.state = State.OPEN_DOOR2_STOP
            elif manager.state in [
                State.OPEN_DOOR1,
                State.CLOSE_DOOR1,
                State.RUN_TRAPPED,
            ]:
                log.alarm(
                    "Error running task " + self.task.name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                manager.state = State.SAVE_TRAPPED

        finally:
            self.task.close()

    def reset_subject_task_training(self) -> None:
        self.task = Task()
        self.subject = Subject()
        self.training.restore()


manager = Manager()
