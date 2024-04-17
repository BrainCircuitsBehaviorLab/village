from enum import Enum

from PyQt5.QtCore import QSettings

from village.log import log


class YesNo(Enum):
    Yes = "Yes"
    No = "No"


class ControlDevice(Enum):
    Bpod = "Bpod"
    Harp = "Harp"


class UseScreen(Enum):
    Screen = "Screen"
    Touchscreen = "Touchscreen"
    No_screen = "No Screen"


class Setting:
    def __init__(self, name, value, type, description):
        self.name = name
        self.value = value
        self.type = type
        self.description = description


class Settings:
    def __init__(
        self,
        main_settings,
        duration_settings,
        directory_settings,
        alarm_settings,
        telegram_settings,
        advanced_settings,
        touchscreen_settings,
        screen_settings,
        sound_settings,
        bpod_settings,
        bpod_advanced_settings,
        harp_settings,
        harp_advanced_settings,
        extra_settings,
    ):

        self.main_settings = main_settings
        self.duration_settings = duration_settings
        self.touchscreen_settings = touchscreen_settings
        self.screen_settings = screen_settings
        self.sound_settings = sound_settings
        self.alarm_settings = alarm_settings
        self.telegram_settings = telegram_settings
        self.bpod_settings = bpod_settings
        self.bpod_advanced_settings = bpod_advanced_settings
        self.harp_settings = harp_settings
        self.harp_advanced_settings = harp_advanced_settings
        self.directory_settings = directory_settings
        self.advanced_settings = advanced_settings
        self.extra_settings = extra_settings

        self.saved_settings = QSettings("village", "village")

        self.restorable_settings = (
            main_settings
            + duration_settings
            + touchscreen_settings
            + screen_settings
            + sound_settings
            + alarm_settings
            + bpod_settings
            + bpod_advanced_settings
            + harp_settings
            + harp_advanced_settings
            + directory_settings
            + advanced_settings
        )

        self.all_settings = (
            self.restorable_settings + extra_settings + telegram_settings
        )

    def restore_factory_settings(self):
        for s in self.restorable_settings:
            self.saved_settings.setValue(s.name, s.value)

        keys = self.saved_settings.allKeys()
        log(keys)

    def create_factory_settings(self):
        for s in self.all_settings:
            self.saved_settings.setValue(s.name, s.value)

        keys = self.saved_settings.allKeys()
        log(keys)

    def get(self, key):
        type = next((s.type for s in self.all_settings if s.name == key), None)
        if type == int:
            return int(self.saved_settings.value(key))
        elif type == float:
            return float(self.saved_settings.value(key))
        return self.saved_settings.value(key)

    def set(self, key, value):
        return self.saved_settings.setValue(key, value)

    def print(self):
        for s in self.all_settings:
            print(s.name, s.value, s.type)


main_settings = [
    Setting("SYSTEM_NAME", "village01", str, "The unique name of the system"),
    Setting("USE_SOUNDCARD", "No", YesNo, "Use of a soundcard"),
    Setting("USE_SCREEN", "No Screen", UseScreen, "Use of a regular or touch screen"),
    Setting(
        "CONTROL_DEVICE",
        "Bpod",
        ControlDevice,
        "The device that controls the tasks and behavioral ports",
    ),
]

duration_settings = [
    Setting(
        "DEFAULT_REFRACTARY_PERIOD",
        14400,
        int,
        """Period of time in seconds that the animal is not allowed to enter after a
        completed session from the same animal""",
    ),
    Setting(
        "DEFAULT_DURATION_MIN",
        1800,
        int,
        """Default minimum duration of the session in seconds.
        Door2 is opened after this time.""",
    ),
    Setting(
        "DEFAULT_DURATION_MAX",
        3600,
        int,
        """Default maximum duration of the session in seconds.
        The session is ended after this time.""",
    ),
]

directory_settings = [
    Setting(
        "APP_DIRECTORY",
        "/home/mousevillage/village",
        str,
        "The directory of the application",
    ),
    Setting(
        "USER_DIRECTORY", "/home/mousevillage/user", str, "The directory of the user"
    ),
    Setting(
        "DATA_DIRECTORY", "/home/mousevillage/data", str, "The directory of the data"
    ),
    Setting(
        "BACKUP_TASKS_DIRECTORY",
        "/home/mousevillage/backup_tasks",
        str,
        """Directory where a copy of the task with a particular code is saved
        every time a task is run""",
    ),
]

alarm_settings = [
    Setting(
        "MINIMUM_WATER_24",
        400,
        int,
        """Minimum water in ml for 24 hours.
        If the animal drinks less, an alarm is triggered""",
    ),
    Setting(
        "MINIMUM_WATER_48",
        1000,
        int,
        """Minimum water in ml for 48 hours.
        If the animal drinks less, an alarm is triggered""",
    ),
    Setting(
        "MINIMUM_TEMPERATURE",
        19,
        int,
        """Minimum temperature in celsius.
        If the temperature is lower, an alarm is triggered""",
    ),
    Setting(
        "MAXIMUM_TEMPERATURE",
        27,
        int,
        """Maximum temperature in celsius.
        If the temperature is higher, an alarm is triggered""",
    ),
]

telegram_settings = [
    Setting("TOKEN", "", str, "The token of the telegram bot"),
    Setting("TELEGRAM_CHAT", "", str, "The chat id of the telegram bot"),
    Setting(
        "TELEGRAM_USERS",
        ["", "", "", "", ""],
        list,
        "The users allowed to use the telegram bot",
    ),
]

advanced_settings = [
    Setting("TAG_DURATION", 0.5, float, "The duration of the tag in seconds"),
    Setting(
        "DIFFERENT_TAG_SEPARATION",
        15.0,
        float,
        """If a tag is detected but the previous one was less than this time ago,
        animal is not allowed to enter""",
    ),
    Setting(
        "CAM_CORRIDOR_DURATION_VIDEO",
        1800,
        int,
        "Duration of the corridor videos in seconds.",
    ),
    Setting(
        "CAM_CORRIDOR_VIDEOS_STORED", 100, int, "The number of corridor videos stored"
    ),
]

touchscreen_settings = [
    Setting(
        "TOUCH_RESOLUTION",
        (4096, 4096),
        tuple,
        "The resolution for the reading of the touch screen",
    ),
    Setting("SCREEN_SIZE_MM", (400, 200), tuple, "The size of the screen in mm"),
    Setting(
        "TIME_BETWEEN_TOUCHES_S",
        0.5,
        float,
        "Refractary period after a touch to not record multiple touches per second",
    ),
]

screen_settings = [
    Setting("SCREEN_SIZE_MM", (400, 200), tuple, "The size of the screen in mm")
]

sound_settings = [Setting("PARAMETER", 1, int, "The parameter of the sound")]

bpod_settings = [
    Setting(
        "BPOD_TARGET_FIRMWARE",
        22,
        int,
        """This system only works with this firmware version of the Bpod.
        If you have another version, update it,
        following instructions in sanworks.com""",
    ),
    Setting(
        "BPOD_BNC_PORTS_ENABLED",
        ["No", "No"],
        list,
        "The enabled BNC ports of the Bpod",
    ),
    Setting(
        "BPOD_WIRED_PORTS_ENABLED",
        ["No", "No"],
        list,
        "The enabled wired ports of the Bpod",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_ENABLED",
        ["Yes", "No", "No", "No", "No", "No", "No", "No"],
        list,
        "The enabled behavior ports of the Bpod",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_WATER",
        ["No", "No", "No", "No", "No", "No", "No", "No"],
        list,
        "The behavior ports that deliver water",
    ),
]

bpod_advanced_settings = [
    Setting("BPOD_SERIAL_PORT", "/dev/Bpod", str, "The serial port of the Bpod"),
    Setting(
        "BPOD_NET_PORT",
        36000,
        int,
        "The network port of the Bpod (for receiving softcodes)",
    ),
    Setting("BPOD_BAUDRATE", 115200, int, "The baudrate of the Bpod"),
    Setting("BPOD_SYNC_CHANNEL", 255, int, "The sync channel of the Bpod"),
    Setting("BPOD_SYNC_MODE", 1, int, "The sync mode of the Bpod"),
]

harp_settings = [Setting("PARAMETER", 1, int, "The parameter of the harp")]

harp_advanced_settings = [
    Setting("HARP_SERIAL_PORT", "/dev/Harp", str, "The serial port of the Harp")
]

extra_settings = [
    Setting("FIRST_LAUNCH", "No", YesNo, "First launch of the system"),
    Setting(
        "SESSIONS_DIRECTORY",
        "/home/mousevillage/data/sessions",
        str,
        "The directory of the sessions",
    ),
]

settings = Settings(
    main_settings,
    duration_settings,
    directory_settings,
    alarm_settings,
    telegram_settings,
    advanced_settings,
    touchscreen_settings,
    screen_settings,
    sound_settings,
    bpod_settings,
    bpod_advanced_settings,
    harp_settings,
    harp_advanced_settings,
    extra_settings,
)


if settings.get("FIRST_LAUNCH") is None:
    settings.create_factory_settings()


# settings.create_factory_settings()

# settings.print()
