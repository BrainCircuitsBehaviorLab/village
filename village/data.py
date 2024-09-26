import importlib
import inspect
import os
import subprocess
import sys
import traceback
from pathlib import Path

from village.classes.collection import Collection
from village.classes.enums import Actions, Active, Cycle, Info, State, Table
from village.classes.subject import Subject
from village.classes.task import Task
from village.settings import settings
from village.utils import utils


class Data:
    def __init__(self) -> None:
        self.subject = Subject()
        self.task = Task()
        self.state: State = State.WAIT
        self.table: Table = Table.EVENTS
        self.tag_reader: Active = settings.get("TAG_READER")
        self.cycle: Cycle = settings.get("CYCLE")
        self.cycle_text: str = ""
        self.text: str = ""
        self.old_text: str = ""
        self.day: bool = True
        self.info: Info = settings.get("INFO")
        self.actions: Actions = settings.get("ACTIONS")
        self.tasks: list[Task] = []

        self.update_cycle()
        self.create_directories()
        self.create_collections()
        self.download_github_repository(settings.get("GITHUB_REPOSITORY_EXAMPLE"))
        utils.log_protocol = self.events
        utils.log("VILLAGE Started")

    def change_directory_settings(self, new_path: str) -> None:
        settings.set("PROJECT_DIRECTORY", new_path)
        settings.set("DATA_DIRECTORY", str(Path(new_path) / "data"))
        settings.set("SESSIONS_DIRECTORY", str(Path(new_path) / "data" / "sessions"))
        settings.set("VIDEOS_DIRECTORY", str(Path(new_path) / "data" / "videos"))
        settings.set("CODE_DIRECTORY", str(Path(new_path) / "code"))

    def create_directories(self) -> None:
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

    def create_directories_from_path(self, path: str) -> bool:
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

    def create_collections(self) -> None:
        self.events = Collection("events", ["date", "type", "subject", "description"])
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
                "conditions",
            ],
        )
        self.subjects = Collection(
            "subjects",
            [
                "date",
                "name",
                "tag",
                "basal_weight",
                "active",
                "last_session_ended",
                "waiting_period",
                "next_session_time",
                "conditions",
            ],
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
        )
        self.sound_calibration = Collection(
            "sound_calibration",
            ["date", "speaker", "target(dB)", "first_volume(dB)", "volume(dB)", "amp"],
        )

    def download_github_repository(self, repository: str) -> None:
        directory = Path(settings.get("CODE_DIRECTORY"))
        if not directory.exists() and directory == settings.get(
            "DEFAULT_CODE_DIRECTORY"
        ):
            directory.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(["git", "clone", repository, directory])
                utils.log("Repository " + repository + " downloaded")
            except Exception:
                utils.log(
                    "Error downloading repository " + repository,
                    exception=traceback.format_exc(),
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
                utils.log(
                    "Error importing " + module_name, exception=traceback.format_exc()
                )
                continue

        self.tasks = tasks
        number_of_tasks = len(tasks)
        if number_of_tasks == 1:
            utils.log("1 task successfully imported")
        else:
            utils.log(str(number_of_tasks) + " tasks successfully imported")

    def get_subject_from_tag(self, tag: str) -> bool:
        subject_series = self.subjects.get_last_entry(column="tag", value=tag)

        if subject_series is None:
            utils.log("subject with tag: " + tag + " not found", type="ERROR")
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
                day = utils.date_from_setting_string(settings.get("DAYTIME")).time()
                night = utils.date_from_setting_string(settings.get("NIGHTTIME")).time()
                now = utils.now().time()

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


data = Data()
