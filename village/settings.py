from enum import Enum

from PyQt5.QtCore import QSettings

from village.log import log

# TODO: should we separate class definition and scripting?


class YesNo(Enum):
    YES = "Yes"
    NO = "No"


class ControlDevice(Enum):
    BPOD = "Bpod"
    HARP = "Harp"


class UseScreen(Enum):
    SCREEN = "Screen"
    TOUCHSCREEN = "Touchscreen"
    NO_SCREEN = "No Screen"


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
        camera_settings,
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
        self.camera_settings = camera_settings

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
            self.restorable_settings
            + extra_settings
            + telegram_settings
            + camera_settings
        )

    def restore_factory_settings(self):
        for s in self.restorable_settings:
            self.saved_settings.setValue(s.name, s.value)

        keys = self.saved_settings.allKeys()
        log(keys)

    def restore_camera_settings(self):
        for s in self.camera_settings:
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
        elif type == tuple:
            try:
                return tuple(map(int, self.saved_settings.value(key)))
            except ValueError:
                return tuple([0] * len(self.saved_settings.value(key)))
        else:
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

# TODO: any way we can make this generalizable? e.g. __file__?
# TODO: also, does the app need to live with the data? Or is this for the gui?
# Does the GUI takes the last saved parameters?
user = "hmv"
directory_settings = [
    Setting(
        "APP_DIRECTORY",
        "/home/" + user + "/village",
        str,
        "The directory of the application",
    ),
    Setting(
        "USER_DIRECTORY", "/home/" + user + "/user", str, "The directory of the user"
    ),
    Setting(
        "DATA_DIRECTORY", "/home/" + user + "/data", str, "The directory of the data"
    ),
    # TODO: should the backup be saved together with the session data?
    Setting(
        "BACKUP_TASKS_DIRECTORY",
        "/home/" + user + "/backup_tasks",
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
    # TODO: what is a tag?
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
# TODO: is there anywhere that checks that a setting is the right type?

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
    # TODO: what is the saving structure like? why sessions dir in extra settings?
    Setting(
        "SESSIONS_DIRECTORY",
        "/home/mousevillage/data/sessions",
        str,
        "The directory of the sessions",
    ),
]

camera_settings = [
    Setting(
        "AREA1_CORRIDOR",
        (50, 100, 150, 150, 100),
        tuple,
        """The first area of the corridor, between the homecage and the first door.
        Values are left, top, right, bottom and threshold for detection""",
    ),
    Setting(
        "AREA2_CORRIDOR",
        (150, 100, 250, 150, 100),
        tuple,
        "The second area of the corridor, between first and second door",
    ),
    Setting(
        "AREA3_CORRIDOR",
        (250, 100, 350, 150, 100),
        tuple,
        """The third area of the corridor, between the second door
        and the behavioral box""",
    ),
    Setting(
        "AREA4_CORRIDOR",
        (0, 0, 0, 0, 100),
        tuple,
        "Not in use for the moment",
    ),
    Setting(
        "AREA1_BOX",
        (0, 10, 20, 30, 100),
        tuple,
        "User defined area where the animals can be",
    ),
    Setting(
        "AREA2_BOX",
        (0, 10, 20, 30, 100),
        tuple,
        "User defined area where the animals can be",
    ),
    Setting(
        "AREA3_BOX",
        (0, 10, 20, 30, 100),
        tuple,
        "User defined area where the animals are not supposed to be",
    ),
    Setting(
        "AREA4_BOX",
        (0, 10, 20, 30, 100),
        tuple,
        "User defined area where the animals are not supposed to be",
    ),
    Setting(
        "NOMOUSE_CORRIDOR",
        25,
        int,
        """If the number of black pixels in any of the areas of the corridor
        is larger than this number we consider there is a mouse in that area.""",
    ),
    Setting(
        "ONEMOUSE_CORRIDOR",
        2000,
        int,
        """If the number of black pixels in any of the areas of the corridor
        is smaller than this number we consider there is not more than one mouse
        in that area.""",
    ),
    Setting(
        "TWOMICE_CORRIDOR",
        2000,
        int,
        """If the number of black pixels in any of the areas of the corridor
        is larger than this number we consider there is more than one mouse
        in that area.""",
    ),
    Setting(
        "NOMOUSE_BOX",
        25,
        int,
        """If the number of black pixels in any of the areas of the behavioral box
        is larger than this number we consider there is a mouse in that area.""",
    ),
    Setting(
        "ONEMOUSE_BOX",
        2000,
        int,
        """If the number of black pixels in any of the areas of the behavioral box
        is smaller than this number we consider there is not more than one mouse
        in that area.""",
    ),
    Setting(
        "TWOMICE_BOX",
        2000,
        int,
        """If the number of black pixels in any of the areas of the behavioral box
        is larger than this number we consider there is more than one mouse
        in that area.""",
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
    camera_settings,
)


if settings.get("FIRST_LAUNCH") is None:
    settings.create_factory_settings()


settings.create_factory_settings()

settings.print()
