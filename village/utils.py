import datetime
import time
from typing import Any

import sounddevice as sd
from PyQt5.QtWidgets import QLayout

from village.classes.protocols import CameraProtocol, LogProtocol


class Utils:
    def __init__(self) -> None:
        self.log_protocol = LogProtocol()
        self.cam_protocol = CameraProtocol()

    @staticmethod
    def now() -> datetime.datetime:
        return datetime.datetime.now()

    @staticmethod
    def time_since_start(start: datetime.datetime) -> datetime.timedelta:
        return datetime.datetime.now() - start

    @staticmethod
    def ms_since_start(start: datetime.datetime) -> int:
        timing = datetime.datetime.now() - start
        return int(timing / datetime.timedelta(milliseconds=1))

    @staticmethod
    def now_string() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def now_string_for_filename() -> str:
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def date_from_string(string: str) -> datetime.datetime:
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def date_from_filename_string(string: str) -> datetime.datetime:
        return datetime.datetime.strptime(string, "%Y%m%d_%H%M%S")

    @staticmethod
    def date_from_setting_string(string: str) -> datetime.datetime:
        return datetime.datetime.strptime(string, "%H:%M")

    def log(
        self,
        description: str,
        type: str = "INFO",
        subject: str = "system",
        exception: Exception | None = None,
    ) -> None:
        date = self.now_string()
        if exception is not None:
            type = "ERROR"
            description += " " + str(exception)
        text = date + "  " + type + "  " + subject + "  " + description
        self.log_protocol.log(date, type, subject, description)
        self.cam_protocol.log(text)
        print(text)

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

    def get_sound_devices(self) -> list[str]:
        devices = sd.query_devices()
        devices_str = [d["name"] for d in devices]
        return devices_str

    @staticmethod
    def measure_time(func) -> Any:
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            print(f"{func.__name__} execution time: {execution_time:.2f} ms")
            return result

        return wrapper

    class Chrono:
        def __init__(self) -> None:
            self.init_time = datetime.datetime.now()

        def reset(self) -> None:
            self.init_time = datetime.datetime.now()

        def get_time(self) -> datetime.timedelta:
            return datetime.datetime.now() - self.init_time

        def get_seconds(self) -> int:
            return int(self.get_time() / datetime.timedelta(seconds=1))

        def get_milliseconds(self) -> int:
            return int(self.get_time() / datetime.timedelta(milliseconds=1))


utils = Utils()
