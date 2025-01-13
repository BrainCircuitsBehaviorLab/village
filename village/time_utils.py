import os
import time
from datetime import datetime, timedelta
from typing import Any


class TimeUtils:
    @staticmethod
    def now() -> datetime:
        return datetime.now()

    @staticmethod
    def hours_ago(hours: int) -> datetime:
        return datetime.now() - timedelta(hours=hours)

    @staticmethod
    def time_since_start(start: datetime) -> timedelta:
        return datetime.now() - start

    @staticmethod
    def ms_since_start(start: datetime) -> int:
        timing = datetime.now() - start
        return int(timing / timedelta(milliseconds=1))

    @staticmethod
    def now_string() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def now_string_for_filename() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def string_from_date(date: datetime) -> str:
        return date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def filename_string_from_date(date: datetime) -> str:
        return date.strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def date_from_string(string: str) -> datetime:
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def date_from_filename_string(string: str) -> datetime:
        return datetime.strptime(string, "%Y%m%d_%H%M%S")

    @staticmethod
    def date_from_setting_string(string: str) -> datetime:
        return datetime.strptime(string, "%H:%M")

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

    @staticmethod
    def find_closest_file(directory: str, prefix: str, date: datetime) -> str:
        closest_file = None
        closest_time = None
        path = ""

        for filename in os.listdir(directory):
            if filename.startswith(prefix) and filename.endswith(".mp4"):
                try:
                    date_str = filename[len(prefix) + 1 : -4]
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")

                    if file_date < date:
                        if closest_time is None or file_date > closest_time:
                            closest_time = file_date
                            closest_file = filename
                except ValueError:
                    continue

        if closest_file is not None:
            path = os.path.join(directory, closest_file)

        return path

    class Chrono:
        def __init__(self) -> None:
            self.init_time = datetime.now()

        def reset(self) -> None:
            self.init_time = datetime.now()

        def get_time(self) -> timedelta:
            return datetime.now() - self.init_time

        def get_seconds(self) -> int:
            return int(self.get_time() / timedelta(seconds=1))

        def get_milliseconds(self) -> int:
            return int(self.get_time() / timedelta(milliseconds=1))

    class Timer:
        def __init__(self, seconds: int) -> None:
            self.seconds = seconds
            self.init_time = datetime.now() - timedelta(seconds=seconds)

        # the first time has_elapsed is true
        def has_elapsed(self) -> bool:
            value = datetime.now() - self.init_time >= timedelta(seconds=self.seconds)
            if value:
                self.reset()
            return value

        def reset(self) -> None:
            self.init_time = datetime.now()

    class HourChangeDetector:
        def __init__(self) -> None:
            self.last_hour = datetime.now().hour

        def has_hour_changed(self) -> bool:
            current_hour = datetime.now().hour

            if current_hour != self.last_hour:
                self.last_hour = current_hour
                return True
            return False

    class CycleChangeDetector:
        def __init__(self, day_time: str, night_time: str) -> None:
            self.day_time = TimeUtils.date_from_setting_string(day_time)
            self.night_time = TimeUtils.date_from_setting_string(night_time)
            self.last_state = self._get_current_cycle()

        def _get_current_cycle(self) -> str:
            now = time_utils.now()

            if self.day_time < self.night_time:
                if self.day_time <= now < self.night_time:
                    return "day"
                else:
                    return "night"
            else:
                if now >= self.day_time or now < self.night_time:
                    return "day"
                else:
                    return "night"

        def has_cycle_changed(self) -> bool:
            current_state = self._get_current_cycle()
            if current_state != self.last_state:
                self.last_state = current_state
                return True
            return False

    class TimestampTracker:
        def __init__(self, hours: int) -> None:
            self.timestamps = [datetime.now()]
            self.hours = hours

        def add_timestamp(self) -> None:
            self.timestamps.append(datetime.now())

        def clean_and_count(self) -> int:
            hours_ago = datetime.now() - timedelta(hours=self.hours)
            self.timestamps = [ts for ts in self.timestamps if ts > hours_ago]
            return len(self.timestamps)


time_utils = TimeUtils()
