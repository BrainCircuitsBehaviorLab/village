import csv
from pathlib import Path
from typing import Any

from village.settings import settings


class TrialRecorder:
    """Universal trial data recorder for all controller types.

    Records states, events, and values during a trial.
    Generates both a raw CSV (line per event) and a per-trial data dictionary.

    Args:
        same_clock: If True (default), timestamps are already in raspberry time.
            If False, a different device clock is used and timestamps
            are auto-converted using the offset from start_trial().

    Usage (same clock - Arduino/Raspberry):
        recorder = TrialRecorder()
        recorder.start_trial(datetime.now().timestamp())
        recorder.add_event("Port1In", datetime.now().timestamp())
        recorder.end_trial(datetime.now().timestamp())

    Usage (different clock - Bpod):
        recorder = TrialRecorder(same_clock=False)
        recorder.start_trial(raspberry_timestamp, controller_timestamp=0.0)
        recorder.add_event("Port1In", 2.5)  # controller-relative
        # → stored as raspberry_timestamp + 2.5
    """

    CSV_COLUMNS = ["TRIAL", "START", "END", "MSG", "VALUE"]

    def __init__(self, same_clock: bool = True) -> None:
        self._csv_path = str(Path(settings.get("SESSIONS_DIRECTORY"), "session.csv"))
        self._csv_file = None
        self._csv_writer = None
        self._trial_number: int = 0
        self._same_clock = same_clock
        self._time_offset: float = 0.0

        # Current trial state
        self._trial_start: float | None = None
        self._current_state: str | None = None
        self._current_state_start: float | None = None
        self._states_start: dict[str, list[float]] = {}
        self._states_end: dict[str, list[float]] = {}
        self._events: dict[str, list[float]] = {}
        self._ordered_events: list[str] = []
        self._values: dict[str, Any] = {}

        self._csv_file = open(self._csv_path, "w", newline="")
        self._csv_writer = csv.writer(
            self._csv_file, delimiter=";", lineterminator="\n"
        )
        self._csv_writer.writerow(self.CSV_COLUMNS)
        self._csv_file.flush()

    def _to_absolute(self, controller_timestamp: float) -> float:
        """Convert a controller timestamp to absolute raspberry time.

        If same_clock=True, returns timestamp unchanged.
        If same_clock=False, adds the offset computed in start_trial.
        """
        if self._same_clock:
            return controller_timestamp
        return controller_timestamp + self._time_offset

    def start_trial(
        self, controller_timestamp: float, raspberry_timestamp: float
    ) -> None:
        """Mark the beginning of a new trial.

        Args:
            controller_timestamp: Controller clock value at trial start.
                If same_clock=True, this is the raspberry time directly.
            raspberry_timestamp: Raspberry time (UNIX epoch in seconds).
                Only used when same_clock=False. The offset is computed as:
                offset = raspberry_timestamp - controller_timestamp
        """
        self._trial_number += 1

        if not self._same_clock:
            self._time_offset = raspberry_timestamp - controller_timestamp
        else:
            self._time_offset = 0.0

        self._trial_start = round(raspberry_timestamp, 4)
        self._trial_end = 0.0
        self._current_state = None
        self._current_state_start = None
        self._states_start = {}
        self._states_end = {}
        self._events = {}
        self._ordered_events = []
        self._values = {}
        timestamp_str = f"{raspberry_timestamp:.4f}"
        self._write_csv_row(timestamp_str, "", "TRIAL_START", "")

    def enter_state(self, state_name: str, controller_timestamp: float) -> None:
        """Record entering a new state. Closes the previous state.

        Args:
            state_name: Name of the state being entered.
            controller_timestamp: Controller clock timestamp.
        """
        abs_ts = self._to_absolute(controller_timestamp)
        self._close_current_state(abs_ts)
        self._current_state = state_name
        self._current_state_start = round(abs_ts, 4)
        timestamp_str = f"{abs_ts:.4f}"
        self._write_csv_row(timestamp_str, "", f"_Transition_to_{state_name}", "")

    def add_event(self, event_name: str, controller_timestamp: float) -> None:
        """Record an event occurrence.

        Args:
            event_name: Name of the event.
            controller_timestamp: Controller clock timestamp.
        """
        abs_ts = self._to_absolute(controller_timestamp)
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(round(abs_ts, 4))
        self._ordered_events.append(event_name)
        timestamp_str = f"{abs_ts:.4f}"
        self._write_csv_row(timestamp_str, "", event_name, "")

    def add_value(self, name: str, value: Any) -> None:
        """Record a key-value pair for the current trial.

        Args:
            name: Name of the value.
            value: The value to record.
        """
        self._values[name] = value
        self._write_csv_row("", "", name, str(value))

    def end_trial(self, controller_timestamp: float) -> None:
        """Mark the end of the current trial. Closes the last open state.

        Args:
            controller_timestamp: Controller clock timestamp.
        """
        abs_ts = self._to_absolute(controller_timestamp)
        self._close_current_state(abs_ts)
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
            for start, end in zip(start_times, end_times):
                self._write_csv_row(
                    f"{start:.4f}",
                    f"{end:.4f}",
                    state.replace("_START", ""),
                    "",
                )

    def get_trial_data(self) -> dict:
        """Returns the fully processed trial_data dict ready for Task.

        Includes TRIAL_START, TRIAL_END, state start/end times, event
        timestamps, ordered list of events, and any custom values.

        Returns:
            dict: Processed trial data.
        """
        trial_data: dict[str, Any] = {"TRIAL_START": self._trial_start}

        # Events
        trial_data.update(self._events)

        # States
        trial_data.update(self._states_start)
        trial_data.update(self._states_end)

        # Custom values
        trial_data.update(self._values)

        trial_data["ordered_list_of_events"] = self._ordered_events

        return trial_data

    def close(self) -> None:
        """Close the CSV file if open."""
        if self._csv_file:
            self._csv_file.flush()
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None

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
                self._states_end[f"STATE_{self._current_state}_END"] = [
                    round(timestamp, 4)
                ]
            else:
                self._states_end[f"STATE_{self._current_state}_END"].append(
                    round(timestamp, 4)
                )
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
