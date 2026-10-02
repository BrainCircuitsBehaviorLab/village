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
    OTHER = "OTHER"


class ScreenActive(SuperEnum):
    SCREEN = "SCREEN"
    TOUCHSCREEN = "TOUCHSCREEN"
    OFF = "OFF"


class AreaActive(SuperEnum):
    ALLOWED = "ALLOWED"
    NOT_ALLOWED = "NOT_ALLOWED"
    TRIGGER = "TRIGGER"
    OFF = "OFF"


class OldVersion(SuperEnum):
    OFF = "OFF"
    V01 = "V0.1"
    V02 = "V0.2"


class State(SuperEnum):
    """Enum representing the state of the village system."""

    WAIT = "All subjects are at home, waiting for RFID detection"
    DETECTION = "Gathering subject data, checking requirements to enter"
    ACCESS = "Closing door1, opening door2"
    LAUNCH_AUTO = "Automatically launching the task"
    RUN_INITIAL = "Task running, waiting for the corridor to become empty"
    CLOSE_DOOR2 = "Closing door2"
    RUN_CLOSED = "Task running, the subject cannot leave yet"
    OPEN_DOOR2 = "Opening door2"
    RUN_OPEN = "Task running, the subject can leave"
    EXIT_UNSAVED = "Closing door2, opening door1; data still not saved"
    SAVE_OUTSIDE = "Stopping the task, saving the data; the subject is already outside"
    SAVE_INSIDE = "Stopping the task, saving the data; the subject is still inside"
    WAIT_SUBJECT_EXIT = "Task finished, waiting for the subject to leave"
    EXIT_SAVED = "Closing door2, opening door1; data already saved"
    OPEN_DOOR2_STOP = "Opening door2, disconnecting RFID"
    MANUAL_MODE = "Settings are being changed or task is being manually prepared"
    LAUNCH_MANUAL = "Manually launching the task"
    RUN_MANUAL = "Task running manually"
    SAVE_MANUAL = "Stopping the task, saving the data; task is running manually"
    SYNC = "Synchronizing data or doing user-defined tasks"
    QUIT_APP = "Confirming whether to quit the app"

    def __init__(self, description: str) -> None:
        """Initializes the State enum with a description."""
        self.description = description

    def can_exit(self) -> bool:
        """Checks if the system can exit in this state.

        Returns:
            bool: True if exit is allowed.
        """
        return self in (State.WAIT, State.MANUAL_MODE)

    def can_edit_data(self) -> bool:
        """Checks if data editing is allowed in this state.

        Returns:
            bool: True if editing is allowed.
        """
        return self in (State.WAIT, State.MANUAL_MODE)

    def can_calibrate_scale(self) -> bool:
        """Checks if scale calibration is allowed in this state.

        Returns:
            bool: True if calibration is allowed.
        """
        return self in (State.WAIT, State.MANUAL_MODE)

    def is_heavy_work(self) -> bool:
        """Checks if this is a state where the system saves or syncs data.

        That work (saving the session and video CSVs, the garbage collection
        and the rsync in SYNC) can keep Python busy long enough for the
        cameras to miss frames, so their watchdog tolerates it.

        Returns:
            bool: True if heavy saving/syncing work happens in this state.
        """
        return self in (
            State.SAVE_INSIDE,
            State.SAVE_OUTSIDE,
            State.SAVE_MANUAL,
            State.SYNC,
        )

    def can_restart_corridor_video(self) -> bool:
        """Checks if a new corridor video can be started in this state.

        Starting one stalls Python for ~1 s (stopping the encoder, launching
        ffmpeg), which would disturb a running task, so
        the periodic split (CORRIDOR_VIDEO_DURATION) waits until no task is
        being launched, run or saved. A restart after a camera failure is
        not restricted.

        Returns:
            bool: True if a new corridor video can be started.
        """
        return self in (State.WAIT, State.MANUAL_MODE, State.WAIT_SUBJECT_EXIT)

    def box_in_use(self) -> bool:
        """Checks if the box is in use in this state.

        True from the moment a task is launched until the subject has left
        the box (or, for a manual task, until it is saved): a task is running
        in the box or a subject may be inside. Not the same as "a subject is
        in the box": while launching the subject may still be in the corridor,
        and a manual task or a calibration may run with no subject at all.

        Returns:
            bool: True if the box is in use.
        """
        return self in (
            State.LAUNCH_AUTO,
            State.LAUNCH_MANUAL,
            State.RUN_INITIAL,
            State.CLOSE_DOOR2,
            State.OPEN_DOOR2,
            State.RUN_OPEN,
            State.RUN_CLOSED,
            State.SAVE_INSIDE,
            State.WAIT_SUBJECT_EXIT,
            State.OPEN_DOOR2_STOP,
            State.RUN_MANUAL,
        )

    def task_is_running(self) -> bool:
        """Checks if a task is currently running.

        Returns:
            bool: True if a task is running.
        """
        return self in (
            State.RUN_INITIAL,
            State.CLOSE_DOOR2,
            State.RUN_CLOSED,
            State.OPEN_DOOR2,
            State.RUN_OPEN,
            State.RUN_MANUAL,
        )

    def manual_task_running(self) -> bool:
        """Checks if a manual task is being launched or running.

        Returns:
            bool: True if a manual task is being launched or running.
        """
        return self in (State.LAUNCH_MANUAL, State.RUN_MANUAL)

    def auto_task_running(self) -> bool:
        """Checks if an automatic task is being launched or running.

        Returns:
            bool: True if an automatic task is being launched or running.
        """
        return self in (
            State.LAUNCH_AUTO,
            State.RUN_INITIAL,
            State.RUN_OPEN,
            State.RUN_CLOSED,
            State.OPEN_DOOR2,
            State.CLOSE_DOOR2,
        )

    def manual_task_in_progress(self) -> bool:
        """Checks if a manual task (or calibration) is running or being saved.

        Returns:
            bool: True if a manual task has not finished yet.
        """
        return self in (State.RUN_MANUAL, State.SAVE_MANUAL)

    def can_enter_manual_mode(self) -> bool:
        """Checks if the system can switch to MANUAL_MODE in this state.

        Returns:
            bool: True if switching to MANUAL_MODE is allowed.
        """
        return self in (State.WAIT, State.MANUAL_MODE)

    def can_stop_syncing(self) -> bool:
        """Checks if syncing process can be stopped.

        Returns:
            bool: True if syncing can be stopped.
        """
        return self == State.SYNC

    def can_go_to_wait(self) -> bool:
        """Checks if the state can transition to WAIT.

        Returns:
            bool: True if transition to WAIT is allowed.
        """
        return self == State.WAIT_SUBJECT_EXIT


class Cycle(SuperEnum):
    AUTO = "AUTO"
    ON = "ON"
    OFF = "OFF"


class CycleDay(SuperEnum):
    AUTO = "AUTO"
    DAY = "DAY"
    NIGHT = "NIGHT"


class Actions(SuperEnum):
    CORRIDOR = "CORRIDOR"
    BOX = "BOX"
    FUNCTIONS = "FUNCTIONS"
    VIRTUAL_MOUSE = "VIRTUAL_MOUSE"


class Info(SuperEnum):
    INFO = "INFO"
    PLOT = "PLOT"
    DETECTION_SETTINGS = "DETECTION_SETTINGS"
    EXTRA = "EXTRA"


class DataTable(SuperEnum):
    EVENTS = "EVENTS"
    SESSIONS_SUMMARY = "SESSIONS_SUMMARY"
    TEMPERATURES = "TEMPERATURES"
    SESSION = "SESSION"
    SESSION_RAW = "SESSION_RAW"
    OLD_SESSION = "OLD_SESSION"
    OLD_SESSION_RAW = "OLD_SESSION_RAW"
    SUBJECTS = "SUBJECTS"


class Save(SuperEnum):
    YES = "YES"
    NO = "NO"
    ZERO = "ZERO"
    ERROR = "ERROR"


class PixelType(SuperEnum):
    RGB = "RGB"
    GRB = "GRB"
    RGBW = "RGBW"
    GRBW = "GRBW"


class Samplerate(SuperEnum):
    HZ44100 = "44100"
    HZ48000 = "48000"
    HZ96000 = "96000"
    HZ192000 = "192000"
