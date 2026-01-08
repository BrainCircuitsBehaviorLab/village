from __future__ import annotations

import datetime
import os
import time
from typing import Any, Callable, Tuple


class TimeUtils:
    """Utility class for time-related operations using monotonic and wall-clock time."""

    def __init__(self) -> None:
        """Initializes the TimeUtils instance with current time values."""
        self._base_wall: datetime.datetime = datetime.datetime.now()
        self._base_mono_ns: int = time.monotonic_ns()

    def sync(self) -> None:
        """Synchronizes base time references."""
        self._base_wall = datetime.datetime.now()
        self._base_mono_ns = time.monotonic_ns()

    def now(self) -> datetime.datetime:
        """Returns the current datetime calculated from monotonic time.

        Returns:
            datetime.datetime: Current time.
        """
        elapsed_ns = time.monotonic_ns() - self._base_mono_ns
        return self._base_wall + datetime.timedelta(seconds=elapsed_ns / 1e9)

    def get_time_monotonic(self) -> float:
        """Returns the current monotonic time in seconds.

        Returns:
            float: Monotonic time.
        """
        return time.monotonic()

    def now_timestamp(self) -> float:
        """Returns the current timestamp.

        Returns:
            float: Current timestamp.
        """
        return self.now().timestamp()

    def monotonic_ns_to_timestamps(self, mono_ns: int) -> float:
        """Converts monotonic nanoseconds to a timestamp.

        Args:
            mono_ns (int): Monotonic time in nanoseconds.

        Returns:
            float: Corresponding timestamp.
        """
        elapsed_ns = mono_ns - self._base_mono_ns
        value = self._base_wall + datetime.timedelta(seconds=elapsed_ns / 1e9)
        return value.timestamp()

    def time_in_future_seconds(self, seconds: int) -> datetime.datetime:
        """Returns a datetime a specific number of seconds in the future.

        Args:
            seconds (int): seconds to add.

        Returns:
            datetime.datetime: Future time.
        """
        return self.now() + datetime.timedelta(seconds=seconds)

    def hours_ago(self, hours: int) -> datetime.datetime:
        """Returns a datetime a specific number of hours in the past.

        Args:
            hours (int): hours to subtract.

        Returns:
            datetime.datetime: Past time.
        """
        return self.now() - datetime.timedelta(hours=hours)

    def date_from_previous_weekday(self, weekday: int) -> datetime.datetime:
        """Returns the date of the most recent occurrence of a specific weekday.

        Args:
            weekday (int): The day of the week (0=Monday, 6=Sunday).

        Returns:
            datetime.datetime: The resulting date.
        """
        today = self.now()
        days = (today.weekday() - weekday) % 7
        return today - datetime.timedelta(days=days)

    def time_since_day_started(self) -> datetime.timedelta:
        """Returns the time elapsed since the start of the current day.

        Returns:
            datetime.timedelta: Time elapsed.
        """
        t = self.now()
        start = datetime.datetime(t.year, t.month, t.day)
        return t - start

    def seconds_since_start(self, start: datetime.datetime) -> int:
        """Returns the number of seconds elapsed since a given start time.

        Args:
            start (datetime.datetime): Start time.

        Returns:
            int: Seconds elapsed.
        """
        return int((self.now() - start).total_seconds())

    def now_string(self) -> str:
        """Returns the current time as a formatted string.

        Returns:
            str: Formatted time string ("%Y-%m-%d %H:%M:%S").
        """
        return self.now().strftime("%Y-%m-%d %H:%M:%S")

    def now_string_for_filename(self) -> str:
        """Returns the current time formatted for filenames.

        Returns:
            str: Formatted time string ("%Y%m%d_%H%M%S").
        """
        return self.now().strftime("%Y%m%d_%H%M%S")

    def string_from_date(self, date: datetime.datetime) -> str:
        """Formats a date object as a string.

        Args:
            date (datetime.datetime): Date object.

        Returns:
            str: Formatted string ("%Y-%m-%d %H:%M:%S").
        """
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def string_from_timestamp(self, timestamp: float) -> str:
        """Formats a timestamp as a string.

        Args:
            timestamp (float): Timestamp to format.

        Returns:
            str: Formatted string ("%Y-%m-%d %H:%M:%S").
        """
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def filename_string_from_date(self, date: datetime.datetime) -> str:
        """Formats a date object for filenames.

        Args:
            date (datetime.datetime): Date object.

        Returns:
            str: Formatted string ("%Y%m%d_%H%M%S").
        """
        return date.strftime("%Y%m%d_%H%M%S")

    def date_from_string(self, string: str) -> datetime.datetime:
        """Parses a date string into a datetime object.

        Args:
            string (str): Date string ("%Y-%m-%d %H:%M:%S").

        Returns:
            datetime.datetime: Parsed datetime object.
        """
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    def time_from_setting_string(self, string: str) -> datetime.time:
        """Parses a time string from settings.

        Args:
            string (str): Time string ("%H:%M").

        Returns:
            datetime.time: Parsed time object, defaults to 08:00 on error.
        """
        try:
            return datetime.datetime.strptime(string, "%H:%M").time()
        except (ValueError, TypeError):
            return datetime.time(8, 0)

    def date_from_path(self, path: str) -> datetime.datetime:
        """Extracts date from a file path based on filename convention.

        Args:
            path (str): File path.

        Returns:
            datetime.datetime: Extracted date.
        """
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
        """Calculates initialization times for a previous day.

        Args:
            first (datetime.time): First time.
            second (datetime.time): Second time.
            days (int): Days ago.
            time_to_end (datetime.datetime | None): End time reference.

        Returns:
            Tuple[datetime.datetime, datetime.datetime]: Calculated datetimes.
        """

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
        """Calculates the initialization time for tomorrow.

        Args:
            first (datetime.time): Target time.

        Returns:
            datetime.datetime: Calculated datetime.
        """
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
        """Calculates a 24-hour range starting from a specific time.

        Args:
            day_date (datetime.datetime): The date.
            first_init_time (datetime.time): The start time.

        Returns:
            Tuple[datetime.datetime, datetime.datetime]: Start and end datetimes.
        """
        start_time = datetime.datetime.combine(day_date.date(), first_init_time)
        end_time = start_time + datetime.timedelta(hours=24)
        return start_time, end_time

    def measure_time(self, func) -> Callable[..., Any]:
        """Decorator to measure execution time of a function.

        Args:
            func (Callable): Function to measure.

        Returns:
            Callable: Wrapped function.
        """

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
        """Finds the file closest to a given date and calculates time difference.

        Args:
            directory (str): Directory to search.
            prefix (str): Filename prefix.
            date (datetime.datetime): Target date.

        Returns:
            Tuple[str, int]: Path to closest file and seconds difference.
        """
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
        """Formats a duration in milliseconds to a string.

        Args:
            milliseconds (int): Duration in milliseconds.

        Returns:
            str: Formatted string ("HH:MM:SS.mmm").
        """
        hours = milliseconds // 3_600_000
        minutes = (milliseconds % 3_600_000) // 60_000
        seconds = (milliseconds % 60_000) // 1_000
        millis = milliseconds % 1_000
        return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

    class Chrono:
        """Simple specific chronometer for measuring elapsed time."""

        def __init__(self) -> None:
            """Initializes the Chrono."""
            self.init_time = time.monotonic()

        def reset(self) -> None:
            """Resets the chronometer."""
            self.init_time = time.monotonic()

        def get_time(self) -> float:
            """Returns elapsed time in seconds.

            Returns:
                float: Elapsed time.
            """
            return time.monotonic() - self.init_time

        def get_seconds(self) -> int:
            """Returns elapsed time in seconds as integer.

            Returns:
                int: Elapsed seconds.
            """
            return int(self.get_time())

        def get_milliseconds(self) -> int:
            """Returns elapsed time in milliseconds.

            Returns:
                int: Elapsed milliseconds.
            """
            return int(self.get_time() * 1000)

    class Timer:
        """Timer for checking if a specific duration has elapsed."""

        def __init__(self, seconds: int) -> None:
            """Initializes the Timer.

            Args:
                seconds (int): Duration in seconds.
            """
            self.seconds = seconds
            now = time.monotonic()
            self.init_time = now - self.seconds
            self.ten_seconds_time = now - 10.0

        def has_elapsed(self) -> bool:
            """Checks if the timer has elapsed.

            Returns:
                bool: True if elapsed, resets automatically.
            """
            now = time.monotonic()
            if now - self.init_time >= self.seconds:
                self.init_time = now
                self.ten_seconds_time = now
                return True
            return False

        def ten_seconds_elapsed(self) -> bool:
            """Checks if 10 seconds have elapsed.

            Returns:
                bool: True if 10 seconds elapsed, resets automatically.
            """
            now = time.monotonic()
            if now - self.ten_seconds_time >= 10:
                self.ten_seconds_time = now
                return True
            return False

        def reset(self) -> None:
            """Resets the timer."""
            now = time.monotonic()
            self.init_time = now
            self.ten_seconds_time = now

    class HourChangeDetector:
        """Detects if the hour has changed."""

        def __init__(self) -> None:
            """Initializes the HourChangeDetector."""
            self.last_hour = datetime.datetime.now().hour

        def has_hour_changed(self) -> bool:
            """Checks if the hour has changed since last check.

            Returns:
                bool: True if hour changed.
            """
            current_hour = datetime.datetime.now().hour
            if current_hour != self.last_hour:
                self.last_hour = current_hour
                return True
            return False

    class CycleChangeDetector:
        """Detects if the day/night cycle has changed."""

        def __init__(self, day_time: str, night_time: str) -> None:
            """Initializes the CycleChangeDetector.

            Args:
                day_time (str): Start time of day.
                night_time (str): Start time of night.
            """
            try:
                self.day_time = datetime.datetime.strptime(day_time, "%H:%M").time()
            except (ValueError, TypeError):
                self.day_time = datetime.time(8, 0)
            try:
                self.night_time = datetime.datetime.strptime(night_time, "%H:%M").time()
            except (ValueError, TypeError):
                self.night_time = datetime.time(20, 0)
            self.last_state = self._get_current_cycle()

        def _get_current_cycle(self) -> str:
            """Determines current cycle state.

            Returns:
                str: 'day' or 'night'.
            """
            t = datetime.datetime.now().time()
            if self.day_time < self.night_time:
                return "day" if self.day_time <= t < self.night_time else "night"
            else:
                return "day" if (t >= self.day_time or t < self.night_time) else "night"

        def has_cycle_changed(self) -> bool:
            """Checks if the cycle has changed.

            Returns:
                bool: True if cycle changed.
            """
            current = self._get_current_cycle()
            if current != self.last_state:
                self.last_state = current
                return True
            return False

    class TimestampTracker:
        """Tracks timestamps and checks for emptiness within a time window."""

        def __init__(self, hours: int) -> None:
            """Initializes the TimestampTracker.

            Args:
                hours (int): Time window in hours.
            """
            self.timestamps = [time.time()]
            self.hours = hours
            self.empty = False

        def add_timestamp(self) -> None:
            """Adds a current timestamp."""
            self.timestamps.append(time.time())

        def trigger_empty(self) -> bool:
            """Checks if the tracker is empty / inactive for the duration.

            Returns:
                bool: True if state changed to empty.
            """
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
