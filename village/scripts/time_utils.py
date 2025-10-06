from __future__ import annotations

import datetime
import os
import time
from typing import Any, Callable, Tuple


class TimeUtils:
    def __init__(self) -> None:
        self._base_wall: datetime.datetime = datetime.datetime.now()
        self._base_mono_ns: int = time.monotonic_ns()

    def sync(self) -> None:
        self._base_wall = datetime.datetime.now()
        self._base_mono_ns = time.monotonic_ns()

    def now(self) -> datetime.datetime:
        elapsed_ns = time.monotonic_ns() - self._base_mono_ns
        return self._base_wall + datetime.timedelta(seconds=elapsed_ns / 1e9)

    def get_time_monotonic(self) -> float:
        return time.monotonic()

    def now_timestamp(self) -> float:
        return self.now().timestamp()

    def monotonic_ns_to_timestamps(self, mono_ns: int) -> float:
        elapsed_ns = mono_ns - self._base_mono_ns
        value = self._base_wall + datetime.timedelta(seconds=elapsed_ns / 1e9)
        return value.timestamp()

    def time_in_future_seconds(self, seconds: int) -> datetime.datetime:
        return self.now() + datetime.timedelta(seconds=seconds)

    def hours_ago(self, hours: int) -> datetime.datetime:
        return self.now() - datetime.timedelta(hours=hours)

    def date_from_previous_weekday(self, weekday: int) -> datetime.datetime:
        today = self.now()
        days = (today.weekday() - weekday) % 7
        return today - datetime.timedelta(days=days)

    def time_since_day_started(self) -> datetime.timedelta:
        t = self.now()
        start = datetime.datetime(t.year, t.month, t.day)
        return t - start

    def seconds_since_start(self, start: datetime.datetime) -> int:
        return int((self.now() - start).total_seconds())

    def now_string(self) -> str:
        return self.now().strftime("%Y-%m-%d %H:%M:%S")

    def now_string_for_filename(self) -> str:
        return self.now().strftime("%Y%m%d_%H%M%S")

    def string_from_date(self, date: datetime.datetime) -> str:
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def string_from_timestamp(self, timestamp: float) -> str:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def filename_string_from_date(self, date: datetime.datetime) -> str:
        return date.strftime("%Y%m%d_%H%M%S")

    def date_from_string(self, string: str) -> datetime.datetime:
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    def time_from_setting_string(self, string: str) -> datetime.time:
        return datetime.datetime.strptime(string, "%H:%M").time()

    def date_from_path(self, path: str) -> datetime.datetime:
        filename = path.split("/")[-1][:-4]
        date_str = "_".join(filename.split("_")[-2:])
        return datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")

    def days_ago_init_times(
        self,
        first: datetime.time,
        second: datetime.time,
        days: int,
        time_to_end: datetime.datetime | None = None,
    ) -> Tuple[datetime.datetime, datetime.datetime]:

        end = time_to_end or self.now()

        if first < end.time():
            day = end - datetime.timedelta(days=days - 1)
        else:
            day = end - datetime.timedelta(days=days)

        v1 = day.replace(
            hour=first.hour,
            minute=first.minute,
            second=first.second,
            microsecond=first.microsecond,
        )
        v2 = day.replace(
            hour=second.hour,
            minute=second.minute,
            second=second.second,
            microsecond=second.microsecond,
        )
        return v1, v2

    def tomorrow_init_time(self, first: datetime.time) -> datetime.datetime:
        base = self.now()
        day = base + datetime.timedelta(days=1) if first < base.time() else base
        return day.replace(
            hour=first.hour,
            minute=first.minute,
            second=first.second,
            microsecond=first.microsecond,
        )

    def range_24_hours(
        self, day_date: datetime.datetime, first_init_time: datetime.time
    ) -> Tuple[datetime.datetime, datetime.datetime]:
        start_time = datetime.datetime.combine(day_date.date(), first_init_time)
        end_time = start_time + datetime.timedelta(hours=24)
        return start_time, end_time

    def measure_time(self, func) -> Callable[..., Any]:
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"{func.__name__} execution time: {(end - start)*1000:.2f} ms")
            return result

        return wrapper

    def find_closest_file_and_seconds(
        self, directory: str, prefix: str, date: datetime.datetime
    ) -> Tuple[str, int]:
        closest_file = None
        closest_time = None
        path = ""
        time_seconds = 0

        for filename in os.listdir(directory):
            if filename.startswith(prefix) and filename.endswith(".mp4"):
                try:
                    date_str = filename[len(prefix) + 1 : -4]
                    file_date = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    if file_date < date and (
                        closest_time is None or file_date > closest_time
                    ):
                        closest_time = file_date
                        closest_file = filename
                except ValueError:
                    continue

        if closest_file and closest_time:
            path = os.path.join(directory, closest_file)
            delta = date - closest_time
            time_seconds = int(delta.total_seconds() - 10)

        return path, time_seconds

    def format_duration(self, milliseconds: int) -> str:
        hours = milliseconds // 3_600_000
        minutes = (milliseconds % 3_600_000) // 60_000
        seconds = (milliseconds % 60_000) // 1_000
        millis = milliseconds % 1_000
        return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

    class Chrono:
        def __init__(self) -> None:
            self.init_time = time.monotonic()

        def reset(self) -> None:
            self.init_time = time.monotonic()

        def get_time(self) -> float:
            return time.monotonic() - self.init_time

        def get_seconds(self) -> int:
            return int(self.get_time())

        def get_milliseconds(self) -> int:
            return int(self.get_time() * 1000)

    class Timer:
        def __init__(self, seconds: int) -> None:
            self.seconds = seconds
            now = time.monotonic()
            self.init_time = now - self.seconds
            self.ten_seconds_time = now - 10.0

        def has_elapsed(self) -> bool:
            now = time.monotonic()
            if now - self.init_time >= self.seconds:
                self.init_time = now
                self.ten_seconds_time = now
                return True
            return False

        def ten_seconds_elapsed(self) -> bool:
            now = time.monotonic()
            if now - self.ten_seconds_time >= 10:
                self.ten_seconds_time = now
                return True
            return False

        def reset(self) -> None:
            now = time.monotonic()
            self.init_time = now
            self.ten_seconds_time = now

    class HourChangeDetector:
        def __init__(self) -> None:
            self.last_hour = datetime.datetime.now().hour

        def has_hour_changed(self) -> bool:
            current_hour = datetime.datetime.now().hour
            if current_hour != self.last_hour:
                self.last_hour = current_hour
                return True
            return False

    class CycleChangeDetector:
        def __init__(self, day_time: str, night_time: str) -> None:
            self.day_time = datetime.datetime.strptime(day_time, "%H:%M").time()
            self.night_time = datetime.datetime.strptime(night_time, "%H:%M").time()
            self.last_state = self._get_current_cycle()

        def _get_current_cycle(self) -> str:
            t = datetime.datetime.now().time()
            if self.day_time < self.night_time:
                return "day" if self.day_time <= t < self.night_time else "night"
            else:
                return "day" if (t >= self.day_time or t < self.night_time) else "night"

        def has_cycle_changed(self) -> bool:
            current = self._get_current_cycle()
            if current != self.last_state:
                self.last_state = current
                return True
            return False

    class TimestampTracker:
        def __init__(self, hours: int) -> None:
            self.timestamps = [time.time()]
            self.hours = hours
            self.empty = False

        def add_timestamp(self) -> None:
            self.timestamps.append(time.time())

        def trigger_empty(self) -> bool:
            cutoff = time.time() - self.hours * 3600
            self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
            count = len(self.timestamps)
            if count > 0:
                self.empty = False
                return False
            elif self.empty:
                return False
            else:
                self.empty = True
                return True


time_utils = TimeUtils()
