from enum import Enum
from typing import Any


class SuperEnum(Enum):
    """Base Enum class with extended functionality."""

    def __eq__(self, other) -> bool:
        """Equality comparison that checks value equality."""
        if not hasattr(other, "value"):
            return False
        return self.value == other.value

    @classmethod
    def keys(cls) -> list[str]:
        """Returns a list of all enum names.

        Returns:
            list[str]: usage: [e.name for e in cls]
        """
        return [e.name for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        """Returns a list of all enum values.

        Returns:
            list[Any]: usage: [e.value for e in cls]
        """
        return [e.value for e in cls]

    @classmethod
    def get_index_from_value(cls, value: Enum) -> int:
        """Gets the index of an enum member by its value.

        Args:
            value (Enum): The enum member or value.

        Returns:
            int: The index.
        """
        return cls.values().index(value.value)

    @classmethod
    def get_index_from_string(cls, string: str) -> int:
        """Gets the index of an enum member by its string value.

        Args:
            string (str): The string string.

        Returns:
            int: The index.
        """
        return cls.values().index(string)


class Active(SuperEnum):
    ON = "ON"
    OFF = "OFF"


class SyncType(SuperEnum):
    HD = "HD"
    SERVER = "SERVER"
    OFF = "OFF"


class Color(SuperEnum):
    BLACK = "BLACK"
    WHITE = "WHITE"


class ControllerEnum(SuperEnum):
    BPOD = "BPOD"
    ARDUINO = "ARDUINO"
    RASPBERRY = "RASPBERRY"


class ScreenActive(SuperEnum):
    SCREEN = "SCREEN"
    TOUCHSCREEN = "TOUCHSCREEN"
    OFF = "OFF"


class AreaActive(SuperEnum):
    ALLOWED = "ALLOWED"
    NOT_ALLOWED = "NOT_ALLOWED"
    TRIGGER = "TRIGGER"
    OFF = "OFF"


class State(SuperEnum):
    """Enum representing the state of the village system."""

    WAIT = "All subjects are at home, waiting for RFID detection"
    DETECTION = "Gathering subject data, checking requirements to enter"
    ACCESS = "Closing door1, opening door2"
    LAUNCH_AUTO = "Automatically launching the task"
    RUN_FIRST = "Task running, waiting for the corridor to become empty"
    CLOSE_DOOR2 = "Closing door2"
    RUN_CLOSED = "Task running, the subject cannot leave yet"
    OPEN_DOOR2 = "Opening door2"
    RUN_OPENED = "Task running, the subject can leave"
    EXIT_UNSAVED = "Closing door2, opening door1; data still not saved"
    SAVE_OUTSIDE = "Stopping the task, saving the data; the subject is already outside"
    SAVE_INSIDE = "Stopping the task, saving the data; the subject is still inside"
    WAIT_EXIT = "Task finished, waiting for the subject to leave"
    EXIT_SAVED = "Closing door2, opening door1; data already saved"
    OPEN_DOOR2_STOP = "Opening door2, disconnecting RFID"
    MANUAL_MODE = "Settings are being changed or task is being manually prepared"
    LAUNCH_MANUAL = "Manually launching the task"
    RUN_MANUAL = "Task running manually"
    SAVE_MANUAL = "Stopping the task, saving the data; task is running manually"
    SYNC = "Synchronizing data or doing user-defined tasks"
    EXIT_GUI = "In the GUI window, ready to exit the app"

    def __init__(self, description: str) -> None:
        """Initializes the State enum with a description."""
        self.description = description

    def can_exit(self) -> bool:
        """Checks if the system can exit in this state.

        Returns:
            bool: True if exit is allowed.
        """
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_edit_data(self) -> bool:
        """Checks if data editing is allowed in this state.

        Returns:
            bool: True if editing is allowed.
        """
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_calibrate_scale(self) -> bool:
        """Checks if scale calibration is allowed in this state.

        Returns:
            bool: True if calibration is allowed.
        """
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_stop_task(self) -> bool:
        """Checks if the running task can be stopped.

        Returns:
            bool: True if task can be stopped.
        """
        if self in (
            State.RUN_FIRST,
            State.RUN_CLOSED,
            State.RUN_OPENED,
            State.RUN_MANUAL,
        ):
            return True
        else:
            return False

    def can_stop_syncing(self) -> bool:
        """Checks if syncing process can be stopped.

        Returns:
            bool: True if syncing can be stopped.
        """
        if self == State.SYNC:
            return True
        else:
            return False

    def can_go_to_wait(self) -> bool:
        """Checks if the state can transition to WAIT.

        Returns:
            bool: True if transition to WAIT is allowed.
        """
        if self == State.WAIT_EXIT:
            return True
        else:
            return False


class Cycle(SuperEnum):
    AUTO = "AUTO"
    DAY = "DAY"
    NIGHT = "NIGHT"


class Actions(SuperEnum):
    CORRIDOR = "CORRIDOR"
    PORTS = "PORTS"
    FUNCTIONS = "FUNCTIONS"
    VIRTUAL_MOUSE = "VIRTUAL_MOUSE"


class Info(SuperEnum):
    SYSTEM_INFO = "SYSTEM_INFO"
    DETECTION_SETTINGS = "DETECTION_SETTINGS"
    DETECTION_PLOT = "DETECTION_PLOT"


class DataTable(SuperEnum):
    EVENTS = "EVENTS"
    SESSIONS_SUMMARY = "SESSIONS_SUMMARY"
    SUBJECTS = "SUBJECTS"
    WATER_CALIBRATION = "WATER_CALIBRATION"
    SOUND_CALIBRATION = "SOUND_CALIBRATION"
    TEMPERATURES = "TEMPERATURES"
    SESSION = "SESSION"
    SESSION_RAW = "SESSION_RAW"
    OLD_SESSION = "OLD_SESSION"
    OLD_SESSION_RAW = "OLD_SESSION_RAW"


class Save(SuperEnum):
    YES = "YES"
    NO = "NO"
    ZERO = "ZERO"
    ERROR = "ERROR"
