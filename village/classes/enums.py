from enum import Enum
from typing import Any


class SuperEnum(Enum):
    def __eq__(self, other) -> bool:
        assert hasattr(other, "value")
        return self.value == other.value

    @classmethod
    def keys(cls) -> list[str]:
        return [e.name for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        return [e.value for e in cls]

    @classmethod
    def get_index_from_value(cls, value: Enum) -> int:
        return cls.values().index(value.value)

    @classmethod
    def get_index_from_string(cls, string: str) -> int:
        return cls.values().index(string)


class Active(SuperEnum):
    ON = "ON"
    OFF = "OFF"


class Color(SuperEnum):
    BLACK = "BLACK"
    WHITE = "WHITE"


class ScreenActive(SuperEnum):
    SCREEN = "SCREEN"
    TOUCHSCREEN = "TOUCHSCREEN"
    OFF = "OFF"


class AreaActive(SuperEnum):
    ALLOWED = "ALLOWED"
    NOT_ALLOWED = "NOT_ALLOWED"
    OFF = "OFF"


class State(SuperEnum):
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
    SYNC = "Synchronizing data with the server or doing user-defined tasks"
    EXIT_GUI = "In the GUI window, ready to exit the app"

    def __init__(self, description: str) -> None:
        self.description = description

    def can_exit(self) -> bool:
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_edit_data(self) -> bool:
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_calibrate_scale(self) -> bool:
        if self in (State.WAIT, State.MANUAL_MODE):
            return True
        else:
            return False

    def can_stop_task(self) -> bool:
        if self in (
            State.RUN_FIRST,
            State.RUN_CLOSED,
            State.RUN_OPENED,
            State.RUN_MANUAL,
        ):
            return True
        else:
            return False

    def can_go_to_wait(self) -> bool:
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


class ThreadState(SuperEnum):
    RUNNING = "RUNNING"
    OFF = "OFF"
    ON = "ON"
