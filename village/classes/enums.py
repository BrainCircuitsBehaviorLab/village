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
    MICE_ALLOWED = "MICE_ALLOWED"
    MICE_NOT_ALLOWED = "MICE_NOT_ALLOWED"
    OFF = "OFF"


class State(SuperEnum):
    WAIT = "All subjects are at home, waiting for RFID detection"
    DETECTION = "Gathering subject data, checking requirements to enter"
    ACCESS = "Closing door1, opening door2"
    LAUNCH = "Launching the task"
    RUN_ACTION = "Waiting for the first action in the behavioral box"
    CLOSE_DOOR2 = "Closing door2"
    RUN_CLOSED = "Task running, the subject cannot leave yet"
    OPEN_DOOR2 = "Opening door2"
    RUN_OPENED = "Task running, the subject can leave"
    EXIT_UNSAVED = "Closing door2, opening door1 (data still not saved)"
    SAVE_OUTSIDE = "Stopping the task, saving the data; the subject is already outside"
    SAVE_INSIDE = "Stopping the task, saving the data; the subject is still inside"
    WAIT_EXIT = "Task finished, waiting for the subject to leave"
    EXIT_SAVED = "Closing door2, opening door1 (data already saved)"
    OPEN_DOOR1 = "Opening door1, a subject is trapped"
    CLOSE_DOOR1 = "Closing door1, the subject is not trapped anymore"
    RUN_TRAPPED = "Task running, waiting for the trapped subject to return home"
    OPEN_DOOR2_STOP = "Opening door2, disconnecting RFID"
    OPEN_DOORS_STOP = "Opening both doors, disconnecting RFID"
    SAVE_TRAPPED = "Stopping the task, saving the data; a subject is trapped"
    ERROR = "Manual intervention required"
    MANUAL_RUN = "Task is running manually"
    SETTINGS = "Settings are being changed or task is being manually prepared"
    EXIT_GUI = "In the GUI window, ready to exit the app"
    EXIT = "Exit"

    def __init__(self, description: str) -> None:
        self.description = description


class Cycle(SuperEnum):
    AUTO = "AUTO"
    DAY = "DAY"
    NIGHT = "NIGHT"


class Actions(SuperEnum):
    CORRIDOR = "CORRIDOR"
    PORTS = "PORTS"
    SOFTCODES = "SOFTCODES"


class Info(SuperEnum):
    SYSTEM_INFO = "SYSTEM_INFO"
    CORRIDOR_SETTINGS = "CORRIDOR_SETTINGS"


class DataTable(SuperEnum):
    EVENTS = "EVENTS"
    SESSIONS_SUMMARY = "SESSIONS_SUMMARY"
    SUBJECTS = "SUBJECTS"
    WATER_CALIBRATION = "WATER_CALIBRATION"
    SOUND_CALIBRATION = "SOUND_CALIBRATION"
    TEMPERATURES = "TEMPERATURES"
    SESSION = "SESSION"
