from enum import Enum
from typing import Any


class SuperEnum(Enum):
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
    WAIT = "all subjects at home, waiting for a not empty rfid detection"
    DETECTION = "getting subject data, checking areas and minimum time"
    ACCESS = "closing door1, opening door2"
    LAUNCH = "launching the task"
    ACTION = "waiting for first action in behavioral box"
    CLOSE = "closing door2"
    RUN_CLOSED = "task running, subject can not leave"
    OPEN = "opening door2"
    RUN_OPENED = "task running, subject can leave"
    EXIT_UNSAVED = "closing door2, opening door1"
    SAVE_OUTSIDE = "stopping the task, saving the data"
    SAVE_INSIDE = "stopping the task, saving the data"
    WAIT_EXIT = "waiting for the subject to leave"
    EXIT_SAVED = "closing door2, opening door1"
    OPEN_TRAPPED = "opening door2, subject trapped"
    CLOSE_TRAPPED = "closing door2, subject trapped"
    RUN_TRAPPED = "task running, waiting for the trapped subject to go home"
    STOP = "opening door2, disconnecting rfid"
    PREPARATION = "task being prepared manually"
    MANUAL = "task running manually"
    SETTINGS = "settings being changed manually"
    SETTINGS_CHANGED = "settings changed manually"
    EXIT_APP = "exiting the app"
    END = "end"

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
    CAMERA_SETTINGS = "CAMERA_SETTINGS"


class DataTable(SuperEnum):
    EVENTS = "EVENTS"
    SESSIONS_SUMMARY = "SESSIONS_SUMMARY"
    SUBJECTS = "SUBJECTS"
    WATER_CALIBRATION = "WATER_CALIBRATION"
    SOUND_CALIBRATION = "SOUND_CALIBRATION"
    SESSION = "SESSION"
