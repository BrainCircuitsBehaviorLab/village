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
        "DAYS_OF_VIDEO_STORAGE",
        7,
        int,
        "Number of days to store video data before deleting it.",
    ),
    Setting(
        "SAFE_DELETE",
        "ON",
        Active,
        """If ON, the system deletes old video data only if it has been backed up
to a remote server. If OFF, the system deletes old video data even if no backup
is found.""",
    ),
    Setting(
        "DETECTION_COLOR",
        "BLACK",
        Color,
        """If the animals are darker than the background, the system detects black
pixels against a white background. If the animals are lighter than the
background, the system detects white pixels against a black background.""",
    ),
    Setting(
        "WEIGHT_THRESHOLD",
        10.0,
        float,
        "The minimum weight in grams to consider that the animal is on the scale.",
    ),
]

sound_settings = [
    Setting("USE_SOUNDCARD", "OFF", Active, "Use of a soundcard."),
    Setting("SOUND_DEVICE", "default", str, "The sound device."),
    Setting("SAMPLERATE", 192000, int, "The samplerate of the sound device."),
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
default_project_directory = str(
    Path("/home", getpass.getuser(), "village_projects", default_project_name)
)

default_server_destination = "/server_destination"
default_server_directory = str(
    Path(default_server_destination, default_project_name + "_data")
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
        str(Path(default_project_directory, "data")),
        str,
        "The data directory.",
    ),
    Setting(
        "SESSIONS_DIRECTORY",
        str(Path(default_project_directory, "data", "sessions")),
        str,
        "The sessions directory.",
    ),
    Setting(
        "VIDEOS_DIRECTORY",
        str(Path(default_project_directory, "data", "videos")),
        str,
        "The videos directory.",
    ),
    Setting(
        "CODE_DIRECTORY",
        str(Path(default_project_directory, "code")),
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

server_settings = [
    Setting("SERVER_USER", "training_village", str, "The server user."),
    Setting("SERVER_HOST", "server", str, "The server hostname."),
    Setting("SERVER_PORT", 4022, int, "The server port."),
    Setting(
        "SERVER_DESTINATION",
        default_server_destination,
        str,
        "The server destination.",
    ),
    Setting(
        "SERVER_DIRECTORY",
        default_server_directory,
        str,
        "The server directory.",
    ),
]

bpod_settings = [
    Setting(
        "BPOD_BNC_PORTS_ENABLED",
        ["OFF", "OFF"],
        list[Active],
        "Enabled BNC ports on the Bpod.",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS_ENABLED",
        ["ON", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "Enabled behavior ports on the Bpod.",
    ),
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
        "ALLOWED",
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
        """If the number of detected pixels in any corridor area is less than
empty_limit, the area is considered empty. If the detected pixel count is between
empty_limit and subject_limit, the area is considered to contain one subject. If the
count exceeds subject_limit, the area is considered to contain multiple subjects.""",
    ),
    Setting(
        "DETECTION_OF_MOUSE_BOX",
        [50, 2000],
        list[int],
        """If the number of detected pixels in any box area is less than
empty_limit, the area is considered empty. If the detected pixel count is between
empty_limit and subject_limit, the area is considered to contain one subject. If the
count exceeds subject_limit, the area is considered to contain multiple subjects.""",
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

hidden_settings = [
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
        "DEFAULT_CODE_DIRECTORY",
        str(Path(default_project_directory, "code")),
        str,
        "The default directory of the user code.",
    ),
    Setting(
        "SCALE_WEIGHT_TO_CALIBRATE",
        20,
        float,
        "Weight in grams used to calibrate the scale.",
    ),
    Setting(
        "SCALE_CALIBRATION_VALUE",
        1,
        float,
        "Factor to transform electric signal to grams.",
    ),
    Setting("RFID_READER", "ON", Active, "The RFID reader status."),
    Setting("CYCLE", "AUTO", Cycle, "The cycle status (day/night)."),
    Setting("INFO", "SYSTEM_INFO", Info, "The information status."),
    Setting("ACTIONS", "CORRIDOR", Actions, "The actions status."),
    Setting("COLOR_AREA1", (0, 136, 0), tuple, "The color of the first area."),
    Setting("COLOR_AREA2", (204, 51, 170), tuple, "The color of the second area."),
    Setting("COLOR_AREA3", (51, 119, 204), tuple, "The color of the third area."),
    Setting("COLOR_AREA4", (221, 51, 0), tuple, "The color of the fourth area."),
]


advanced_settings = [
    Setting(
        "BPOD_TARGET_FIRMWARE",
        22,
        int,
        """This system is compatible only with this Bpod firmware version. If you have
a different version, please update it by following the instructions at sanworks.com.""",
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
    Setting(
        "DETECTION_DURATION",
        0.5,
        float,
        """To allow access, after a detection, the pixel detection must remain within
limits for this duration (in seconds).""",
    ),
    Setting(
        "TIME_BETWEEN_DETECTIONS",
        15.0,
        float,
        """To allow access, no other animals can have been detected within this number
of seconds prior to a detection.""",
    ),
    Setting(
        "WEIGHT_DEVIATION",
        5,
        float,
        """The standard deviation of the weight must be smaller than this value
to consider it as correct. If the ratio is greater than this value, the weight
is considered an outlier probably because the animal is moving or it is not
completely on the scale.""",
    ),
    Setting(
        "UPDATE_TIME_TABLE",
        1,
        int,
        """Duration in seconds of the update period for the tables displayed
in DATA. Setting a very low value could result in excessive CPU load.""",
    ),
    Setting(
        "SCREENSAVE_TIME",
        300,
        int,
        """The time in seconds after which the system automatically returns to
the MAIN screen if there is no user interaction. This helps reduce CPU usage by
preventing unnecessary processing.""",
    ),
    Setting(
        "CORRIDOR_VIDEO_DURATION",
        1800,
        int,
        "The duration of the corridor videos in seconds.",
    ),
    Setting("MOTOR1_PIN", 12, int, "The pin of the motor 1."),
    Setting("MOTOR2_PIN", 13, int, "The pin of the motor 2."),
    Setting("SCALE_ADDRESS", "0x64", str, "The address of the scale."),
    Setting("TEMP_SENSOR_ADDRESS", "0x45", str, "The address of the temp sensor."),
    Setting(
        "ALARM_REPEAT_TIME",
        3600,
        int,
        """Some alarms should be triggered each time an event occurs, while others
might be continuously triggered by the same ongoing event (e.g., two animals detected
inside the behavioral box, a malfunctioning scale, etc.). To prevent flooding the
system with repeated messages, this setting defines a time period during which the
same type of alarm will not be triggered again.""",
    ),
    Setting(
        "REPEAT_TARE_TIME",
        600,
        int,
        "The interval in seconds at which the scale is tared.",
    ),
    Setting(
        "MATPLOTLIB_DPI",
        100,
        int,
        "The DPI of the matplotlib plots.",
    ),
    Setting(
        "CAM_BOX_INDEX",
        0,
        int,
        "The index (0, 1) of the box camera.",
    ),
    Setting(
        "CAM_CORRIDOR_INDEX",
        1,
        int,
        "The index (0, 1) of the corridor camera.",
    ),
    Setting(
        "CAM_CORRIDOR_FRAMERATE",
        10,
        int,
        "The number of frames per second for the corridor camera.",
    ),
    Setting(
        "CAM_BOX_FRAMERATE",
        30,
        int,
        "The number of frames per second for the box camera.",
    ),
]


settings = Settings(
    main_settings,
    sound_settings,
    alarm_settings,
    directory_settings,
    screen_settings,
    touchscreen_settings,
    telegram_settings,
    server_settings,
    bpod_settings,
    camera_settings,
    motor_settings,
    hidden_settings,
    advanced_settings,
)

# settings.restore_factory_settings()
# settings.print()
