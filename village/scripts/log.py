import re

from village.classes.abstract_classes import (
    CameraBase,
    EventBase,
    TelegramBotBase,
)
from village.scripts.time_utils import time_utils


class Log:
    """Handles logging of events, errors, alarms, and other system info.

    Attributes:
        event (EventBase): Handler for generic events.
        temp (EventBase): Handler for temperature events.
        cam (CameraBase): Handler for camera overlay text.
        telegram_bot (TelegramBotBase): Handler for Telegram notifications.
    """

    def __init__(self) -> None:
        """Initializes the Log system with default handlers."""
        self.event = EventBase()
        self.temp = EventBase()
        self.cam = CameraBase()
        self.telegram_bot = TelegramBotBase()

    def info(self, description: str, subject: str = "system") -> None:
        """Logs an informational message.

        Args:
            description (str): The message content.
            subject (str): The subject related to the info.
        """
        type = "INFO"
        date = time_utils.now_string()
        text = date + "  " + type + "  " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text)

    def temperature(self, temperature: float, humidity: float) -> None:
        """Logs temperature and humidity data.

        Args:
            temperature (float): The temperature value.
            humidity (float): The humidity value.
        """
        date = time_utils.now_string()
        self.temp.log_temp(date, temperature, humidity)

    def start(self, task: str, subject: str = "system") -> None:
        """Logs the start of a task.

        Args:
            task (str): The task name.
            subject (str): The subject involved.
        """
        type = "START"
        date = time_utils.now_string()
        description = task + " started"
        text = date + "  " + type + " " + subject + "  " + description
        self.event.log(date, type, subject, description)
        self.cam.write_text(text)
        print(text)

    def end(self, task: str, subject: str = "system") -> None:
        """Logs the end of a task.

        Args:
            task (str): The task name.
            subject (str): The subject involved.
        """
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
        """Logs an error message.

        Args:
            description (str): The error description.
            subject (str): The subject involved.
            exception (str | None): Optional exception traceback string.
        """
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
        """Logs an alarm and sends a Telegram notification.

        Args:
            description (str): The alarm description.
            subject (str): The subject involved.
            exception (str | None): Optional exception traceback string.
            report (bool): If True, skips logging to event log (used for reports).
        """
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
        """Formats an exception traceback into a single line string.

        Args:
            exception (str | None): The exception traceback.
            description (str): The initial description.

        Returns:
            str: The cleaned and formatted string.
        """
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

