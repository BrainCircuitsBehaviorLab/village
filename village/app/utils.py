import datetime
from pathlib import Path

from PyQt5.QtWidgets import QLayout

from village.classes.protocols import LogProtocol
from village.classes.settings_class import Setting


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def now_string() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def now_string_for_filename() -> str:
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(
        self,
        description: str,
        subject: str = "",
        exception: Exception | None = None,
        destinations: list[LogProtocol] = [],
    ) -> None:
        date = self.now_string()
        if exception is None:
            print(date + "  " + subject + "  " + description)
        else:
            print(date + "  " + subject + "  " + description + " " + str(exception))

        for d in destinations:
            d.log(description, subject, date)

    def generate_directory_paths(self, project_directory) -> list[Setting]:
        directory_settings = [
            Setting(
                "PROJECT_DIRECTORY",
                project_directory,
                str,
                "The directory of the project",
            ),
            Setting(
                "DATA_DIRECTORY",
                project_directory + "/data",
                str,
                "The directory of the data",
            ),
            Setting(
                "SESSIONS_DIRECTORY",
                project_directory + "/sessions",
                str,
                "The directory of the sessions",
            ),
            Setting(
                "VIDEOS_DIRECTORY",
                project_directory + "/videos",
                str,
                "The directory of the sessions",
            ),
            Setting(
                "APP_DIRECTORY",
                str(Path(__file__).parent.parent.parent),
                str,
                "The directory of the application",
            ),
        ]

        return directory_settings

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


utils = Utils()
