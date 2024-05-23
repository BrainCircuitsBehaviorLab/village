import datetime

from village.classes.protocols import LogProtocol


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


utils = Utils()
