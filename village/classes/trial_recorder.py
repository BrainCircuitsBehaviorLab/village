import csv
from datetime import datetime
from typing import Any


class TrialRecorder:
    """Universal trial data recorder for all controller types.

    Records states, events, and values during a trial.
    Generates both a raw CSV (line per event) and a per-trial data dictionary.

    Usage:
        recorder = TrialRecorder(csv_path="session.csv")
        recorder.start_trial(datetime.now().timestamp())
        recorder.enter_state("WaitForPoke", datetime.now().timestamp())
        recorder.add_event("Port1In", datetime.now().timestamp())
        recorder.enter_state("Reward", datetime.now().timestamp())
        recorder.end_trial(datetime.now().timestamp())
        data = recorder.get_trial_data()
    """

    # CSV_COLUMNS = ["TRIAL", "TIMESTAMP", "TYPE", "NAME", "VALUE"]
    CSV_COLUMNS = ["TRIAL", "START", "END", "MSG", "VALUE"]

    def __init__(self, csv_path: str | None = None) -> None:
        self._csv_path = csv_path
        self._csv_file = None
        self._csv_writer = None
        self._trial_number: int = 0

        # Current trial state
        self._trial_start: float | None = None
        self._current_state: str | None = None
        self._current_state_start: float | None = None
        self._states_start: dict[str, list[float]] = {}
        self._states_end: dict[str, list[float]] = {}
        self._events: dict[str, list[float]] = {}
        self._ordered_events: list[str] = []
        self._values: dict[str, Any] = {}

        if csv_path:
            self._csv_file = open(csv_path, "w", newline="")
            self._csv_writer = csv.writer(
                self._csv_file, delimiter=";", lineterminator="\n"
            )
            self._csv_writer.writerow(self.CSV_COLUMNS)
            self._csv_file.flush()

    def start_trial(self, timestamp: float) -> None:
        """Mark the beginning of a new trial.

        Args:
            timestamp: UNIX epoch in seconds.
        """
        self._trial_number += 1
        self._trial_start = round(timestamp, 4)
        self._current_state = None
        self._current_state_start = None
        self._states_start = {}
        self._states_end = {}
        self._events = {}
        self._ordered_events = []
        self._values = {}
        timestamp_str = f"{timestamp:.4f}"
        self._write_csv_row(timestamp_str, "", "TRIAL_START", "")

    def enter_state(self, state_name: str, timestamp: float) -> None:
        """Record entering a new state. Closes the previous state.

        Args:
            state_name: Name of the state being entered.
            timestamp: UNIX epoch in seconds.
        """
        self._close_current_state(timestamp)
        self._current_state = state_name
        self._current_state_start = round(timestamp, 4)
        timestamp_str = f"{timestamp:.4f}"
        self._write_csv_row(timestamp_str, "", f"_Transition_to_{state_name}", "")

    def add_event(self, event_name: str, timestamp: float) -> None:
        """Record an event occurrence.

        Args:
            event_name: Name of the event.
            timestamp: UNIX epoch in seconds.
        """
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(round(timestamp, 4))
        self._ordered_events.append(event_name)
        timestamp_str = f"{timestamp:.4f}"
        self._write_csv_row(timestamp_str, "", event_name, "")

    def add_value(self, name: str, value: Any) -> None:
        """Record a key-value pair for the current trial.

        Args:
            name: Name of the value.
            value: The value to record.
        """
        self._values[name] = value
        self._write_csv_row("", "", name, str(value))

    def end_trial(self, timestamp: float) -> None:
        """Mark the end of the current trial. Closes the last open state.

        Args:
            timestamp: UNIX epoch in seconds.
        """
        self._close_current_state(timestamp)
        timestamp_str = f"{timestamp:.4f}"
        self._write_csv_row(timestamp_str, "", "TRIAL_END", "")


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
                self._states_start[f"STATE_{self._current_state}_START"] = [self._current_state_start]
            else:
                self._states_start[f"STATE_{self._current_state}_START"].append(self._current_state_start)
            if f"STATE_{self._current_state}_END" not in self._states_end:
                self._states_end[f"STATE_{self._current_state}_END"] = [round(timestamp, 4)]
            else:
                self._states_end[f"STATE_{self._current_state}_END"].append(round(timestamp, 4))
            self._current_state = None
            self._current_state_start = None

    def _write_csv_row(
        self, start: str, end: str, msg: str, value: str
    ) -> None:
        """Write a row to the raw CSV file."""
        if self._csv_writer:
            self._csv_writer.writerow(
                [self._trial_number, start, end, msg, value]
            )
            self._csv_file.flush() 

    def __del__(self) -> None:
        self.close()
