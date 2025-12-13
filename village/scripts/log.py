import re
from typing import TYPE_CHECKING

from village.classes.null_classes import (
    NullCamera,
    NullCollection,
    NullTelegramBot,
)
from village.scripts.time_utils import time_utils

if TYPE_CHECKING:
    from village.classes.collection import Collection
    from village.devices.camera import Camera
    from village.devices.telegram_bot import TelegramBot


class Log:
    def __init__(self) -> None:
        self.event: Collection | NullCollection = NullCollection()
        self.temp: Collection | NullCollection = NullCollection()
        self.cam: Camera | NullCamera = NullCamera()
        self.telegram_bot: TelegramBot | NullTelegramBot = NullTelegramBot()

    def info(self, description: str, subject: str = "system") -> None:
        type = "INFO"
        date = time_utils.now_string()
        text = date + "  " + type + "  " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text)

    def temperature(self, temperature: float, humidity: float) -> None:
        date = time_utils.now_string()
        self.temp.log_temp(date, temperature, humidity)

    def start(self, task: str, subject: str = "system") -> None:
        type = "START"
        date = time_utils.now_string()
        description = task + " started"
        text = date + "  " + type + " " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text)

    def end(self, task: str, subject: str = "system") -> None:
        type = "END"
        date = time_utils.now_string()
        description = task + " ended"
        text = date + "  " + type + " " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text)

    def error(
        self,
        description: str,
        subject: str = "system",
        exception: str | None = None,
    ) -> None:
        type = "ERROR"
        date = time_utils.now_string()
        description = self.clean_text(exception, description)
        text = date + "  " + type + "  " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text.replace("  |  ", "\n"))

    def alarm(
        self,
        description: str,
        subject: str = "system",
        exception: str | None = None,
        report: bool = False,
    ) -> None:
        type = "ALARM"
        date = time_utils.now_string()
        message = description if subject == "system" else description + " " + subject
        self.telegram_bot.alarm(message)
        print("")
        print(exception)
        print("")
        description = self.clean_text(exception, description)
        text = date + "  " + type + "  " + subject + "  " + description
        if not report:
            self.event.log(date, type, subject, description)
            self.cam.write_text(text)
        print(text.replace("  |  ", "\n"))

    def clean_text(self, exception: str | None, description: str) -> str:
        if exception is not None:
            lines = exception.split("\n")
            processed_lines = [description]

            for line in lines:
                if re.search(r"\^{2,}", line):
                    continue
                if line.startswith("Traceback"):
                    continue
                if line.startswith("  File"):
                    line = "  |  " + line
                if not line.startswith(" "):
                    line = "  |  " + "  " + line
                processed_lines.append(line)

            description = "  |  ".join(processed_lines)
            description = description.replace(";", "")

        return description


log = Log()
