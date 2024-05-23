from village.classes.settings_class import (
    Active,
    AreaActive,
    Color,
    ControlDevice,
    ScreenActive,
    Setting,
    Settings,
)

main_settings = [
    Setting("SYSTEM_NAME", "village01", str, "The unique name of the system"),
    Setting("USE_SOUNDCARD", "OFF", Active, "Use of a soundcard"),
    Setting("USE_SCREEN", "OFF", ScreenActive, "Use of a regular or touch screen"),
    Setting(
        "CONTROL_DEVICE",
        "BPOD",
        ControlDevice,
        "The device that controls the tasks and behavioral ports",
    ),
    Setting(
        "DETECTION_COLOR",
        "BLACK",
        Color,
        """If the animals are darker than the background the system will try to detect
        black pixels in white background. If the aninals are lighter than the background
        the system will try to detect white pixels in black background.""",
    ),
]

corridor_settings = [
    Setting(
        "DETECTION_DURATION",
        0.5,
        float,
        """When an animal is detected, the corridor must be kept clear of other animals
        for this duration in seconds to allow access.""",
    ),
    Setting(
        "TIME_BETWEEN_DETECTIONS",
        15.0,
        float,
        """When a tag is detected, the previous tag detection must have happened
        at least this number of seconds before to allow access""",
    ),
    Setting(
        "CORRIDOR_VIDEOS_DURATION",
        1800,
        int,
        "Duration of the corridor videos in seconds.",
    ),
    Setting("CORRIDOR_VIDEOS_STORED", 100, int, "The number of corridor videos stored"),
]

sound_settings = [Setting("PARAMETER", 1, int, "The parameter of the sound")]

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

directory_settings = [
    Setting(
        "PROJECT_DIRECTORY",
        "/home/mousevillage/project",
        str,
        "The directory of the project",
    ),
    Setting(
        "DATA_DIRECTORY",
        "/home/mousevillage/project/data",
        str,
        "The directory of the data",
    ),
    Setting(
        "SESSIONS_DIRECTORY",
        "/home/mousevillage/project/data/sessions",
        str,
        "The directory of the sessions",
    ),
    Setting(
        "VIDEOS_DIRECTORY",
        "/home/mousevillage/project/data/videos",
        str,
        "The directory of the sessions",
    ),
    Setting(
        "APP_DIRECTORY",
        "/home/mousevillage/village",
        str,
        "The directory of the application",
    ),
]

screen_settings = [
    Setting("SCREEN_SIZE_MM", [400, 200], list[int], "The size of the screen in mm")
]

touchscreen_settings = [
    Setting("SCREEN_SIZE_MM", [400, 200], list[int], "The size of the screen in mm"),
    Setting(
        "TOUCH_RESOLUTION",
        [4096, 4096],
        list[int],
        "The resolution for the reading of the touch screen",
    ),
    Setting(
        "TIME_BETWEEN_TOUCHES",
        0.5,
        float,
        "Refractary period after a touch to not record multiple touches per second",
    ),
]

telegram_settings = [
    Setting("TOKEN", "", str, "The token of the telegram bot"),
    Setting("TELEGRAM_CHAT", "", str, "The chat id of the telegram bot"),
    Setting(
        "TELEGRAM_USERS",
        ["", "", "", "", ""],
        list[str],
        "The users allowed to use the telegram bot",
    ),
]

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
        ["OFF", "OFF"],
        list[Active],
        "The enabled BNC ports of the Bpod",
    ),
    Setting(
        "BPOD_WIRED_PORTS_ENABLED",
        ["OFF", "OFF"],
        list[Active],
        "The enabled wired ports of the Bpod",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_ENABLED",
        ["ON", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "The enabled behavior ports of the Bpod",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_WATER",
        ["OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "The behavior ports that deliver water",
    ),
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

harp_settings = [
    Setting("PARAMETER", 1, int, "The parameter of the harp"),
    Setting("HARP_SERIAL_PORT", "/dev/Harp", str, "The serial port of the Harp"),
]

camera_settings = [
    Setting(
        "AREA1_CORRIDOR",
        [100, 300, 200, 350, 100, 100],
        list[int],
        """The first area of the corridor, between the homecage and the first door.
        Values are left, top, right, bottom, threshold for detection during day
        and threshold for deterction during night.""",
    ),
    Setting(
        "AREA2_CORRIDOR",
        [200, 300, 300, 350, 100, 100],
        list[int],
        """The second area of the corridor, between the first and the second door.
        Values are left, top, right, bottom, threshold for detection during day
        and threshold for deterction during night.""",
    ),
    Setting(
        "AREA3_CORRIDOR",
        [300, 300, 400, 350, 100, 100],
        list[int],
        """The third area of the corridor, between the second door and the behavioral
        box. Values are left, top, right, bottom, threshold for detection during day
        and threshold for deterction during night.""",
    ),
    Setting(
        "AREA1_BOX",
        [200, 100, 300, 200, 100],
        list[int],
        """The first area of the box.
        Values are left, top, right, bottom, threshold for detection.""",
    ),
    Setting(
        "USAGE1_BOX",
        "MICE_ALLOWED",
        AreaActive,
        """If animals are allowed to be in this area, on they are not allowed,
        or the area is deactivated""",
    ),
    Setting(
        "AREA2_BOX",
        [350, 100, 450, 200, 100],
        list[int],
        """The second area of the box.
        Values are left, top, right, bottom, threshold for detection.""",
    ),
    Setting(
        "USAGE2_BOX",
        "OFF",
        AreaActive,
        """If animals are allowed to be in this area, on they are not allowed,
        or the area is deactivated""",
    ),
    Setting(
        "AREA3_BOX",
        [200, 150, 300, 250, 100],
        list[int],
        """The third area of the box.
        Values are left, top, right, bottom, threshold for detection.""",
    ),
    Setting(
        "USAGE3_BOX",
        "OFF",
        AreaActive,
        """If animals are allowed to be in this area, on they are not allowed,
        or the area is deactivated""",
    ),
    Setting(
        "AREA4_BOX",
        [350, 250, 450, 350, 100],
        list[int],
        """The fourth area of the box.
        Values are left, top, right, bottom, threshold for detection.""",
    ),
    Setting(
        "USAGE4_BOX",
        "OFF",
        AreaActive,
        """If animals are allowed to be in this area, on they are not allowed,
        or the area is deactivated""",
    ),
    Setting(
        "DETECTION_OF_MOUSE_CORRIDOR",
        [50, 2000],
        list[int],
        """If the number of black pixels in any of the areas of the corridor
        is smaller than the first number we consider that the area is empty.
        If the number of black pixels is between first and second number we consider
        that there is one mouse in that area, if the number of black pixels is
        larger than the second number we consider that there is more than one
        mouse.""",
    ),
    Setting(
        "DETECTION_OF_MOUSE_BOX",
        [50, 2000],
        list[int],
        """If the number of black pixels in any of the areas of the box
        is smaller than the first number we consider that the area is empty.
        If the number of black pixels is between first and second number we consider
        that there is one mouse in that area, if the number of black pixels is
        larger than the second number we consider that there is more than one
        mouse.""",
    ),
    Setting(
        "VIEW_DETECTION_CORRIDOR",
        "ON",
        Active,
        "Preview the pixel detection on the image",
    ),
    Setting(
        "VIEW_DETECTION_BOX",
        "ON",
        Active,
        "Preview the pixel detection on the image",
    ),
]

motor_settings = [
    Setting(
        "MOTOR1_VALUES",
        [50, 80],
        list[int],
        """Opening angle, closing angle for the door 1""",
    ),
    Setting(
        "MOTOR2_VALUES",
        [50, 80],
        list[int],
        """Opening angle, closing angle for the door 2""",
    ),
]

extra_settings = [
    Setting("FIRST_LAUNCH", "OFF", Active, "First launch of the system"),
    Setting(
        "SCALE_CALIBRATION_VALUE",
        20,
        int,
        "The weight in grams used to calibrate the scale",
    ),
    Setting("COLOR_AREA1", (128, 0, 128), tuple, "The color of the first area"),
    Setting("COLOR_AREA2", (165, 42, 42), tuple, "The color of the second area"),
    Setting("COLOR_AREA3", (0, 100, 0), tuple, "The color of the third area"),
    Setting("COLOR_AREA4", (122, 122, 122), tuple, "The color of the fourth area"),
]


settings = Settings(
    main_settings,
    corridor_settings,
    sound_settings,
    alarm_settings,
    directory_settings,
    screen_settings,
    touchscreen_settings,
    telegram_settings,
    bpod_settings,
    harp_settings,
    camera_settings,
    motor_settings,
    extra_settings,
)

# settings.create_factory_settings()
