import importlib
import inspect
import os
import subprocess
import sys
import traceback
from pathlib import Path

import sounddevice as sd
from pandas import DataFrame
from PyQt5.QtWidgets import QLayout

from village.classes.collection import Collection
from village.classes.enums import Actions, Active, Cycle, DataTable, Info, State
from village.classes.subject import Subject
from village.classes.task import Task
from village.log import log
from village.settings import settings
from village.time_utils import time_utils


class Data:
    def __init__(self) -> None:
        self.subject = Subject()
        self.task = Task()
        self.state: State = State.WAIT
        self.table: DataTable = DataTable.EVENTS
        self.tag_reader: Active = settings.get("TAG_READER")
        self.cycle: Cycle = settings.get("CYCLE")
        self.cycle_text: str = ""
        self.text: str = ""
        self.old_text: str = ""
        self.day: bool = True
        self.changing_settings: bool = False
        self.info: Info = settings.get("INFO")
        self.actions: Actions = settings.get("ACTIONS")
        self.tasks: list[Task] = []
        self.filename: str = ""
        self.df_all: DataFrame | None = None
        self.errors: str = ""

        self.update_cycle()
        self.create_directories()
        self.create_collections()
        log.event_protocol = self.events
        self.download_github_repository(settings.get("GITHUB_REPOSITORY_EXAMPLE"))

    @staticmethod
    def change_directory_settings(new_path: str) -> None:
        settings.set("PROJECT_DIRECTORY", new_path)
        settings.set("DATA_DIRECTORY", str(Path(new_path) / "data"))
        settings.set("SESSIONS_DIRECTORY", str(Path(new_path) / "data" / "sessions"))
        settings.set("VIDEOS_DIRECTORY", str(Path(new_path) / "data" / "videos"))
        settings.set("CODE_DIRECTORY", str(Path(new_path) / "code"))

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
    def create_directories_from_path(path: str) -> bool:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            data = os.path.join(path, "data")
            Path(data).mkdir(parents=True, exist_ok=True)
            sessions = os.path.join(data, "sessions")
            Path(sessions).mkdir(parents=True, exist_ok=True)
            videos = os.path.join(data, "videos")
            Path(videos).mkdir(parents=True, exist_ok=True)
            code = os.path.join(path, "code")
            Path(code).mkdir(parents=True, exist_ok=True)
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
                "next_task",
                "next_settings",
            ],
            [str, str, float, str, str, str, str],
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
        tasks: list[Task] = []

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
                        new_task = cls()
                        new_task.name = name
                        if not any(item.name == name for item in tasks):
                            tasks.append(new_task)
            except Exception:
                log.error(
                    "Couldn't import " + module_name, exception=traceback.format_exc()
                )
                continue

        self.tasks = tasks
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
        state_name = data.state.name
        state_description = data.state.description
        subject_name = data.subject.name
        task_name = data.task.name
        tag_reader_name = data.tag_reader.name
        cycle_text = data.cycle_text

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

    def launch_task(self) -> bool:
        task_name = self.subject.next_task
        task = next((item for item in self.tasks if item.name == task_name), None)
        if task is None:
            log.error("Task: " + task_name + " not found", subject=self.subject.name)
            return False
        else:
            self.task = task
            self.task.subject = self.subject.name
            start_time = time_utils.now_string_for_filename()
            self.task.df = None
            self.task.new_df = None

            filename = str(self.subject.name) + "_" + str(self.subject.next_task)
            filename += "_" + start_time
            self.filename = filename
            self.df_all = None

            try:
                data.task.test_run(subject=self.subject.name)
                return True
            except Exception:
                log.alarm(
                    "Error launching task " + task_name,
                    subject=self.subject.name,
                    exception=traceback.format_exc(),
                )
                return False


data = Data()
