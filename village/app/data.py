import importlib
import inspect
import pkgutil
from pathlib import Path

from village.app.settings import settings
from village.app.utils import utils
from village.classes.collection import Collection
from village.classes.task import Task


class Data:
    def __init__(self) -> None:
        # directories
        self.create_directories()

        # collections
        self.events = Collection("events", ["date", "type", "subject", "value"])
        self.sessions = Collection(
            "sessions",
            ["date", "name", "subject", "tag", "weight", "task", "duration", "water"],
        )
        self.water_calibration = Collection(
            "water_calibration", ["date", "port_number", "volume(ul)", "time(ms)"]
        )

        self.tasks = self.import_all_tasks("user")

    def create_directories(self) -> None:
        directory = Path(settings.get("PROJECT_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("DATA_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("SESSIONS_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)
        directory = Path(settings.get("VIDEOS_DIRECTORY"))
        directory.mkdir(parents=True, exist_ok=True)

    def import_all_tasks(self, package_name: str) -> list[Task]:
        tasks = []

        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.walk_packages(
                package.__path__, package_name + "."
            ):
                try:
                    module = importlib.import_module(name)

                    clsmembers = inspect.getmembers(module, inspect.isclass)

                    for _, cls in clsmembers:
                        if issubclass(cls, Task) and cls != Task:
                            name = cls.__name__
                            new_task = cls()
                            new_task.name = name
                            tasks.append(new_task)
                except Exception as e:
                    utils.log(
                        "Error importing " + name,
                        exception=e,
                        destinations=[self.events],
                    )
                    continue
        except ModuleNotFoundError:
            pass

        return tasks


data = Data()
