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


class ControlDevice(SuperEnum):
    BPOD = "BPOD"
    HARP = "HARP"


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
    WAIT = "all subjects at home, waiting for rfid detection"
    DETECTION = "subject detected, checking if it is allowed to enter"
    ACCESS = "access granted, launching the task"
    LAUNCH = (
        "task launched, waiting for the subject to perform the first action in the box"
    )
    ACTION = "subject performed the first action in the box, closing the door"
    CLOSE = "door closed, running the task, subject can not leave the box yet"
    OPEN = "task finished, opening the door"
    RUN_OPENED = "door opened, subject can leave the box"
    EXIT_UNSAVED = "subject leaving, task is not saved yet"
    SAVE_OUTSIDE = "task saved, subject is already outside"
    SAVE_INSIDE = "task saved, subject is still inside"
    WAIT_EXIT = "waiting for the subject to leave the box"
    EXIT_SAVED = "subject leaving, task is already saved"
    STOP = "automatic task, manually stopped"
    ERROR = "error occurred, disconnecting rfids and stopping the task"
    PREPARE = "manually preparing a task"
    MANUAL = "manually running a task"

    def __init__(self, description: str) -> None:
        self.description = description


class Cycle(SuperEnum):
    AUTO = "AUTO"
    DAY = "DAY"
    NIGHT = "NIGHT"
    OFF = "OFF"


class Actions(SuperEnum):
    CORRIDOR = "CORRIDOR"
    PORTS = "PORTS"
    SOFTCODES = "SOFTCODES"


class Info(SuperEnum):
    SYSTEM_INFO = "SYSTEM_INFO"
    CAMERA_SETTINGS = "CAMERA_SETTINGS"
