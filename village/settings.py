import getpass
from pathlib import Path

from village.classes.settings_class import (
    Actions,
    Active,
    AreaActive,
    Color,
    Cycle,
    Info,
    ScreenActive,
    Setting,
    Settings,
)

main_settings = [
    Setting("SYSTEM_NAME", "village01", str, "The system’s unique name."),
    Setting(
        "DAYTIME",
        "08:00",
        str,
        """If lighting differs between day and night, the system needs to adjust
detection thresholds accordingly. This setting defines the hour at which
daytime begins.""",
    ),
    Setting(
        "NIGHTTIME",
        "20:00",
        str,
        """If lighting differs between day and night, the system needs to adjust
detection thresholds accordingly. This setting defines the hour at which
nighttime begins.""",
    ),
    Setting(
        "DETECTION_COLOR",
        "BLACK",
        Color,
        """If the animals are darker than the background, the system detects black
pixels against a white background. If the animals are lighter than the
background, the system detects white pixels against a black background.""",
    ),
]

corridor_settings = [
    Setting(
        "DETECTION_DURATION",
        0.5,
        float,
        """To allow access, after a detection, the pixel detection must remain within
limits for this duration.""",
    ),
    Setting(
        "TIME_BETWEEN_DETECTIONS",
        15.0,
        float,
        """To allow access, no other animals can have been detected within this number
of seconds prior to a detection.""",
    ),
    Setting(
        "CORRIDOR_VIDEOS_DURATION",
        1800,
        int,
        "Duration of corridor videos (in seconds).",
    ),
    Setting(
        "CORRIDOR_VIDEOS_STORED",
        100,
        int,
        """Number of corridor videos stored. When the limit is reached, the oldest
video is deleted each time a new video is recorded.""",
    ),
]

sound_settings = [
    Setting("USE_SOUNDCARD", "OFF", Active, "Use of a soundcard."),
    Setting("SOUND_DEVICE", "default", str, "The sound device."),
]

alarm_settings = [
    Setting(
        "MINIMUM_WATER_24",
        400,
        int,
        """Minimum water intake in ml over 24 hours. If the animal drinks less than
this amount, an alarm is triggered.""",
    ),
    Setting(
        "MINIMUM_WATER_48",
        1000,
        int,
        """Minimum water intake in ml over 48 hours. If the animal drinks less than
this amount, an alarm is triggered.""",
    ),
    Setting(
        "MINIMUM_TEMPERATURE",
        19,
        int,
        """Minimum temperature (in Celsius). If the temperature falls below this level,
an alarm is triggered.""",
    ),
    Setting(
        "MAXIMUM_TEMPERATURE",
        27,
        int,
        """Maximum temperature (in Celsius). If the temperature exceeds this level,
an alarm is triggered.""",
    ),
]

default_project_name = "demo_project"
default_project_directory = (
    "/home/" + getpass.getuser() + "/village_projects/" + default_project_name
)

directory_settings = [
    Setting(
        "PROJECT_DIRECTORY",
        default_project_directory,
        str,
        "The project directory.",
    ),
    Setting(
        "DATA_DIRECTORY",
        default_project_directory + "/data",
        str,
        "The data directory.",
    ),
    Setting(
        "SESSIONS_DIRECTORY",
        default_project_directory + "/data/sessions",
        str,
        "The sessions directory.",
    ),
    Setting(
        "VIDEOS_DIRECTORY",
        default_project_directory + "/data/videos",
        str,
        "The videos directory.",
    ),
    Setting(
        "CODE_DIRECTORY",
        default_project_directory + "/code",
        str,
        "The user code directory.",
    ),
    Setting(
        "APP_DIRECTORY",
        str(Path(__file__).parent.parent),
        str,
        "The application directory.",
    ),
]

screen_settings = [
    Setting("USE_SCREEN", "OFF", ScreenActive, "Use of a regular or touch screen."),
    Setting("SCREEN_SIZE_MM", [400, 200], list[int], "Screen size (in mm)."),
    Setting(
        "SCREEN_RESOLUTION",
        [1024, 768],
        list[int],
        """Screen resolution.
TODO. If this is a fixed value or not.""",
    ),
]

touchscreen_settings = [
    Setting(
        "TOUCH_RESOLUTION",
        [4096, 4096],
        list[int],
        """Touch screen reading resolution. This value is typically different from the
screen's display resolution.""",
    ),
    Setting(
        "TIME_BETWEEN_TOUCHES",
        0.5,
        float,
        """Refractory period after a touch (in seconds) to prevent recording an
excessive number of touches per second.""",
    ),
]

telegram_settings = [
    Setting("TELEGRAM_TOKEN", "", str, "Telegram bot token."),
    Setting("TELEGRAM_CHAT", "", str, "Telegram chat ID."),
    Setting(
        "TELEGRAM_USERS",
        ["", "", "", "", ""],
        list[str],
        "Users authorized to use the Telegram bot.",
    ),
]

bpod_settings = [
    Setting(
        "BPOD_TARGET_FIRMWARE",
        22,
        int,
        """This system is compatible only with this Bpod firmware version. If you have
a different version, please update it by following the instructions at sanworks.com.""",
    ),
    Setting(
        "BPOD_BNC_PORTS_ENABLED",
        ["OFF", "OFF"],
        list[Active],
        "Enabled BNC ports on the Bpod.",
    ),
    Setting(
        "BPOD_WIRED_PORTS_ENABLED",
        ["OFF", "OFF"],
        list[Active],
        "Enabled wired ports on the Bpod.",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_ENABLED",
        ["ON", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "Enabled behavior ports on the Bpod.",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_WATER",
        ["OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "Behavior ports that deliver water.",
    ),
    Setting("BPOD_SERIAL_PORT", "/dev/Bpod", str, "The serial port of the Bpod"),
    Setting(
        "BPOD_NET_PORT",
        36000,
        int,
        "The network port of the Bpod (for sending and receiving softcodes).",
    ),
    Setting("BPOD_BAUDRATE", 115200, int, "Bpod baudrate."),
    Setting("BPOD_SYNC_CHANNEL", 255, int, "Bpod sync channel."),
    Setting("BPOD_SYNC_MODE", 1, int, "Bpod sync mode."),
]


camera_settings = [
    Setting(
        "AREA1_CORRIDOR",
        [100, 300, 200, 350, 100, 100],
        list[int],
        """The first area of the corridor, located between the homecage and the first
door. Values include left, top, right, and bottom coordinates, as well as detection
thresholds for daytime and nighttime.""",
    ),
    Setting(
        "AREA2_CORRIDOR",
        [200, 300, 300, 350, 100, 100],
        list[int],
        """The second area of the corridor, located between the first door and the
area3. Values include left, top, right, and bottom coordinates, as well as detection
thresholds for daytime and nighttime.""",
    ),
    Setting(
        "AREA3_CORRIDOR",
        [300, 300, 400, 350, 100, 100],
        list[int],
        """The third area of the corridor, located between the area2 and the second
door. Values include left, top, right, and bottom coordinates, as well as detection
thresholds for daytime and nighttime.""",
    ),
    Setting(
        "AREA4_CORRIDOR",
        [400, 300, 500, 350, 100, 100],
        list[int],
        """The fourth area of the corridor, located between the second door and the
behavioral box. Values include left, top, right, and bottom coordinates, as well as
detection thresholds for daytime and nighttime.""",
    ),
    Setting(
        "AREA1_BOX",
        [200, 100, 300, 200, 100],
        list[int],
        """The first area of the box. Values include left, top, right, and bottom
coordinates, along with the detection threshold.""",
    ),
    Setting(
        "USAGE1_BOX",
        "MICE_ALLOWED",
        AreaActive,
        """Specifies if animals are allowed in this area, not allowed, or if the area
is deactivated.""",
    ),
    Setting(
        "AREA2_BOX",
        [350, 100, 450, 200, 100],
        list[int],
        """The secpnd area of the box. Values include left, top, right, and bottom
coordinates, along with the detection threshold.""",
    ),
    Setting(
        "USAGE2_BOX",
        "OFF",
        AreaActive,
        """Specifies if animals are allowed in this area, not allowed, or if the area
is deactivated.""",
    ),
    Setting(
        "AREA3_BOX",
        [200, 250, 300, 350, 100],
        list[int],
        """The third area of the box. Values include left, top, right, and bottom
coordinates, along with the detection threshold.""",
    ),
    Setting(
        "USAGE3_BOX",
        "OFF",
        AreaActive,
        """Specifies if animals are allowed in this area, not allowed, or if the area
is deactivated.""",
    ),
    Setting(
        "AREA4_BOX",
        [350, 250, 450, 350, 100],
        list[int],
        """The fourth area of the box. Values include left, top, right, and bottom
coordinates, along with the detection threshold.""",
    ),
    Setting(
        "USAGE4_BOX",
        "OFF",
        AreaActive,
        """Specifies if animals are allowed in this area, not allowed, or if the area
is deactivated.""",
    ),
    Setting(
        "DETECTION_OF_MOUSE_CORRIDOR",
        [50, 2000],
        list[int],
        """If the number of black pixels in any corridor area is less than the first
value, the area is considered empty. If the black pixel count falls between the first
and second values, one mouse is considered to be in the area. If the count exceeds the
second value, more than one mouse is assumed to be present.""",
    ),
    Setting(
        "DETECTION_OF_MOUSE_BOX",
        [50, 2000],
        list[int],
        """If the number of black pixels in any box area is less than the first
value, the area is considered empty. If the black pixel count falls between the first
and second values, one mouse is considered to be in the area. If the count exceeds the
second value, more than one mouse is assumed to be present.""",
    ),
    Setting(
        "VIEW_DETECTION_CORRIDOR",
        "ON",
        Active,
        "Preview the pixel detection on the image.",
    ),
    Setting(
        "VIEW_DETECTION_BOX",
        "ON",
        Active,
        "Preview the pixel detection on the image.",
    ),
]

motor_settings = [
    Setting(
        "MOTOR1_VALUES",
        [50, 80],
        list[int],
        "Opening and closing angles for door 1 (values between 0 and 180 degrees).",
    ),
    Setting(
        "MOTOR2_VALUES",
        [50, 80],
        list[int],
        "Opening and closing angles for door 2 (values between 0 and 180 degrees).",
    ),
]

extra_settings = [
    Setting("FIRST_LAUNCH", "OFF", Active, "First launch of the system."),
    Setting(
        "DEFAULT_PROJECT_NAME", default_project_name, str, "The default project name."
    ),
    Setting(
        "GITHUB_REPOSITORY_EXAMPLE",
        "https://github.com/BrainCircuitsBehaviorLab/follow-the-light-task.git",
        str,
        "The github repository to download.",
    ),
    Setting(
        "SCALE_CALIBRATION_VALUE",
        20,
        int,
        "Weight in grams used to calibrate the scale.",
    ),
    Setting("COLOR_AREA1", (0, 136, 0), tuple, "The color of the first area."),
    Setting("COLOR_AREA2", (204, 51, 170), tuple, "The color of the second area."),
    Setting("COLOR_AREA3", (51, 119, 204), tuple, "The color of the third area."),
    Setting("COLOR_AREA4", (221, 51, 0), tuple, "The color of the fourth area."),
    Setting("TAG_READER", "ON", Active, "The tag reader status."),
    Setting("CYCLE", "AUTO", Cycle, "The cycle status (day/night)."),
    Setting("INFO", "SYSTEM_INFO", Info, "The information status."),
    Setting("ACTIONS", "CORRIDOR", Actions, "The actions status."),
    Setting(
        "UPDATE_TIME_MS", 2000, int, "The update time in ms for the tables and plots."
    ),
    Setting("SCREENSAVE_TIME_MS", 300000, int, "The time in ms for the screensave."),
    Setting("MOTOR1_PIN", 12, int, "The pin of the motor 1."),
    Setting("MOTOR2_PIN", 13, int, "The pin of the motor 2."),
    Setting("SCALE_ADDRESS", "0x64", str, "The address of the scale."),
    Setting("TEMP_SENSOR_ADDRESS", "0x45", str, "The address of the temp sensor."),
    Setting(
        "DEFAULT_CODE_DIRECTORY",
        default_project_directory + "/code",
        str,
        "The default directory of the user code.",
    ),
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
    camera_settings,
    motor_settings,
    extra_settings,
)


# settings.print()
# settings.create_factory_settings()
# settings.restore_factory_settings()
