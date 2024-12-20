from village.classes.protocols import CameraProtocol, EventProtocol, TelegramBotProtocol
from village.time_utils import time_utils


class Log:
    def __init__(self) -> None:
        self.event_protocol = EventProtocol()
        self.cam_protocol = CameraProtocol()
        self.telegram_protocol = TelegramBotProtocol()

    def info(self, description: str, subject: str = "system") -> None:
        type = "INFO"
        date = time_utils.now_string()
        text = date + "  " + type + "  " + subject + "  " + description
        self.event_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
        print(text)

    def start(self, task: str, subject: str = "system") -> None:
        type = "START"
        date = time_utils.now_string()
        description = task + " started"
        text = date + "  " + type + " " + subject + "  " + description
        self.event_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
        print(text)

    def end(self, task: str, subject: str = "system") -> None:
        type = "END"
        date = time_utils.now_string()
        description = task + " ended"
        text = date + "  " + type + " " + subject + "  " + description
        self.event_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
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
        self.event_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
        print(text)

    def alarm(
        self,
        description: str,
        subject: str = "system",
        exception: str | None = None,
    ) -> None:
        type = "ALARM"
        date = time_utils.now_string()
        message = description if subject == "system" else description + " " + subject
        self.telegram_protocol.alarm(message)
        description = self.clean_text(exception, description)
        text = date + "  " + type + "  " + subject + "  " + description
        self.event_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
        print(text)

    def clean_text(self, exception: str | None, description: str) -> str:
        if exception is not None:
            exception = exception.replace(";", " ")
            exception = " || ".join(exception.splitlines())
            description += " " + exception
        return description


log = Log()
