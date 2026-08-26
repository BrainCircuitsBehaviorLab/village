import csv
import threading
from pathlib import Path
from typing import Any

from village.settings import settings


class TrialRecorder:
    """Universal trial data recorder for all controller types.

    Records states, events, and values during a trial.
    Generates both a raw CSV (line per event) and a per-trial data dictionary
    """

    CSV_COLUMNS = ["TRIAL", "START", "END", "MSG", "VALUE"]

    def __init__(self) -> None:
        # Reentrant: device threads (sound worker, touch reader, GL paint) record
        # events concurrently with the task thread. Every public method takes this
        # lock, so the accumulators and the CSV writer are never touched by two
        # threads at once. Reentrant because some public methods call others.
        self._lock = threading.RLock()
        # Events are only recorded between start_trial() and get_trial_data();
        self._trial_active: bool = False
        self._csv_path = str(Path(settings.get("SESSIONS_DIRECTORY"), "session.csv"))
        self._csv_file = None
        self._csv_writer = None
        self._trial_number: int = 0
        self._time_offset: float = 0.0

        # Current trial state
        self._trial_start: float | None = None
        self._trial_end: float | None = None
        self._current_state: str | None = None
        self._current_state_start: float | None = None
        self._states_start: dict[str, list[float]] = {}
        self._states_end: dict[str, list[float]] = {}
        self._events: dict[str, list[float]] = {}
        self._ordered_events: list[str] = []
        self._values: dict[str, Any] = {}

        Path(self._csv_path).parent.mkdir(parents=True, exist_ok=True)
        self._csv_file = Path(self._csv_path).open("w", newline="")  # noqa: SIM115
        self._csv_writer = csv.writer(
            self._csv_file, delimiter=";", lineterminator="\n"
        )
        self._csv_writer.writerow(self.CSV_COLUMNS)
        self._csv_file.flush()

    # public methods
    def start_trial(
        self, raspberry_timestamp: float, controller_timestamp: float
    ) -> None:
        """Mark the beginning of a new trial.

        Args:
            raspberry_timestamp: Raspberry time (UNIX epoch in seconds).
            controller_timestamp: Controller clock value at trial start. If you are
            not using a controller, this should be the same as raspberry_timestamp.

        The offset is computed as:
                offset = raspberry_timestamp - controller_timestamp
        """
        with self._lock:
            self._trial_number += 1

            self._time_offset = raspberry_timestamp - controller_timestamp

            self._trial_start = round(raspberry_timestamp, 4)
            self._current_state = None
            self._current_state_start = None
            self._states_start = {}
            self._states_end = {}
            self._events = {}
            self._ordered_events = []
            self._values = {}
            self._trial_active = True
            timestamp_str = f"{raspberry_timestamp:.4f}"
            self._write_csv_row(timestamp_str, "", "TRIAL_START", "")

    def enter_state(self, state_name: str, controller_timestamp: float) -> None:
        """Record entering a new state. Closes the previous state.

        Args:
            state_name: Name of the state being entered.
            controller_timestamp: Controller clock timestamp.
        """
        with self._lock:
            abs_ts = self._to_absolute(controller_timestamp)
            self._close_current_state(abs_ts)
            self._current_state = state_name
            self._current_state_start = abs_ts
            timestamp_str = f"{abs_ts:.4f}"
            self._write_csv_row(timestamp_str, "", f"_Transition_to_{state_name}", "")

    def add_controller_event(
        self, event_name: str, controller_timestamp: float
    ) -> None:
        """Record an event using a controller clock timestamp.

        Args:
            event_name: Name of the event.
            controller_timestamp: Controller clock timestamp, converted to
                absolute raspberry time.
        """
        with self._lock:
            if self._trial_active:
                self._add_event(event_name, self._to_absolute(controller_timestamp))

    def add_raspberry_event(self, event_name: str, raspberry_timestamp: float) -> None:
        """Record an event using an already-absolute raspberry timestamp.

        Args:
            event_name: Name of the event.
            raspberry_timestamp: Raspberry time, used as-is regardless of
                whether a controller is being used.
        """
        with self._lock:
            if self._trial_active:
                self._add_event(event_name, round(raspberry_timestamp, 4))

    def add_value(self, name: str, value: Any) -> None:
        """Record a key-value pair for the current trial.

        Args:
            name: Name of the value.
            value: The value to record.
        """
        with self._lock:
            self._values[name] = value
            self._write_csv_row("", "", name, str(value))

    def end_trial(self, controller_timestamp: float) -> None:
        """Mark the end of the current trial. Closes the last open state.

        Args:
            controller_timestamp: Controller clock timestamp.
        """
        with self._lock:
            abs_ts = self._to_absolute(controller_timestamp)
            self._close_current_state(abs_ts)
            self._trial_end = abs_ts
            timestamp_str = f"{abs_ts:.4f}"
            self._write_csv_row(timestamp_str, "", "TRIAL_END", "")

            self._write_csv_row(
                f"{self._trial_start:.4f}",
                timestamp_str,
                "TRIAL",
                "",
            )

            for state, start_times in self._states_start.items():
                end_times = self._states_end.get(state.replace("START", "END"), [])
                for start, end in zip(start_times, end_times, strict=False):
                    self._write_csv_row(
                        f"{start:.4f}",
                        f"{end:.4f}",
                        state.replace("_START", ""),
                        "",
                    )

    def get_trial_data(
        self, date: str, trial: int, subject: str, name: str, system_name: str
    ) -> dict:
        """Returns the fully processed trial_data dict ready for Task.

        Includes TRIAL_START, TRIAL_END, state start/end times, event
        timestamps, ordered list of events, and any custom values.

        Returns:
            dict: Processed trial data.
        """
        with self._lock:
            # No more async events belong to this trial once we snapshot it.
            self._trial_active = False
            trial_data: dict[str, Any] = {
                "date": date,
                "trial": trial,
                "subject": subject,
                "task": name,
                "system_name": system_name,
            }
            trial_data["TRIAL_START"] = self._trial_start
            trial_data["TRIAL_END"] = self._trial_end

            # States
            interleaved = {}
            for state, start_times in self._states_start.items():
                interleaved[state] = start_times
                end_key = state.replace("START", "END")
                if end_key in self._states_end:
                    interleaved[end_key] = self._states_end[end_key]

            trial_data.update(interleaved)

            # Events
            trial_data.update(self._events)

            trial_data["ordered_list_of_events"] = self._ordered_events

            self._write_csv_row("", "", "date", date)
            self._write_csv_row("", "", "trial", str(trial))
            self._write_csv_row("", "", "subject", subject)
            self._write_csv_row("", "", "task", name)
            self._write_csv_row("", "", "system_name", system_name)

            return trial_data

    def close(self) -> None:
        """Close the CSV file if open."""
        with self._lock:
            self._trial_active = False
            if self._csv_file:
                self._csv_file.flush()
                self._csv_file.close()
                self._csv_file = None
                self._csv_writer = None

    # private methods below this line
    def _to_absolute(self, controller_timestamp: float) -> float:
        """Convert a controller timestamp to absolute raspberry time.
        Round to 4 decimals so that data is easier to read and occupies less space.
        """
        return round(controller_timestamp + self._time_offset, 4)

    def _add_event(self, event_name: str, abs_ts: float) -> None:
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(abs_ts)
        self._ordered_events.append(event_name)
        timestamp_str = f"{abs_ts:.4f}"
        self._write_csv_row(timestamp_str, "", event_name, "")

    def _close_current_state(self, timestamp: float) -> None:
        """Close the currently open state with the given end timestamp."""
        if self._current_state is not None and self._current_state_start is not None:
            if f"STATE_{self._current_state}_START" not in self._states_start:
                self._states_start[f"STATE_{self._current_state}_START"] = [
                    self._current_state_start
                ]
            else:
                self._states_start[f"STATE_{self._current_state}_START"].append(
                    self._current_state_start
                )
            if f"STATE_{self._current_state}_END" not in self._states_end:
                self._states_end[f"STATE_{self._current_state}_END"] = [timestamp]
            else:
                self._states_end[f"STATE_{self._current_state}_END"].append(timestamp)
            self._current_state = None
            self._current_state_start = None

    def _write_csv_row(self, start: str, end: str, msg: str, value: str) -> None:
        """Write a row to the raw CSV file."""
        if self._csv_writer:
            self._csv_writer.writerow([self._trial_number, start, end, msg, value])
            if self._csv_file:
                self._csv_file.flush()

    def __del__(self) -> None:
        self.close()
