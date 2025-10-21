import getpass
from pathlib import Path

from village.classes.settings_class import (
    Actions,
    Active,
    AreaActive,
    Color,
    Controller,
    Cycle,
    Info,
    ScreenActive,
    Setting,
    Settings,
    SyncType,
)

main_settings = [
    Setting("SYSTEM_NAME", "village01", str, "The system’s unique name."),
    Setting(
        "DAYTIME",
        "08:00",
        str,
        """This setting defines when the daytime cycle begins. At the start of each
cycle, the system performs various checks. The entry plot for the behavioral box uses
this value to distinguish between day and night periods. If lighting conditions differ
between day and night, the system will adjust detection thresholds accordingly.""",
    ),
    Setting(
        "NIGHTTIME",
        "20:00",
        str,
        """This setting defines when the nighttime cycle begins. At the start of each
cycle, the system performs various checks. The entry plot for the behavioral box uses
this value to distinguish between day and night periods. If lighting conditions differ
between day and night, the system will adjust detection thresholds accordingly.""",
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

sound_settings = [
    Setting("USE_SOUNDCARD", "OFF", Active, "Use of a soundcard."),
    Setting("SOUND_DEVICE", "default", str, "The sound device."),
    Setting("SAMPLERATE", 192000, int, "The samplerate of the sound device."),
]

screen_settings = [
    Setting("USE_SCREEN", "OFF", ScreenActive, "Use of a regular or touch screen."),
    Setting(
        "SCREEN_SIZE_MM",
        [400, 200],
        list[int],
        """Physical screen size in millimeters. Useful when positioning stimuli
using real-world units instead of pixels.""",
    ),
    Setting(
        "SCREEN_RESOLUTION",
        [1600, 900],
        list[int],
        "Screen resolution.",
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
        "TOUCH_INTERVAL",
        0.5,
        float,
        """Minimum time (in seconds) after each registered touchscreen touch before
another touch can be recorded. Prevents multiple rapid detections from a single
response, ensuring each touch reflects a distinct action.""",
    ),
]

telegram_settings = [
    Setting("TELEGRAM_TOKEN", "", str, "The telegram bot token."),
    Setting(
        "TELEGRAM_CHAT",
        "",
        str,
        "The Telegram chat ID where alarm messages will be sent.",
    ),
    Setting(
        "HEALTHCHECKS_URL",
        "",
        str,
        "The URL of the healthchecks.io endpoint to notify when the system is running.",
    ),
]


default_project_name = "demo_project"
default_project_directory = str(
    Path("/home", getpass.getuser(), "village_projects", default_project_name)
)

default_sync_destination = "/sync_destination"
default_sync_directory = str(
    Path(default_sync_destination, default_project_name + "_data")
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
        "MEDIA_DIRECTORY",
        str(Path(default_project_directory, "media")),
        str,
        "The user media directory (e.g., images, videos, sounds, etc.).",
    ),
    Setting(
        "APP_DIRECTORY",
        str(Path(__file__).parent.parent),
        str,
        "The application directory.",
    ),
]


sync_settings = [
    Setting(
        "SYNC_TYPE",
        "OFF",
        SyncType,
        """Choose where to sync session data:
HD to copy data to a USB hard drive connected to the Raspberry Pi.
SERVER to sync data to a remote server over SSH.
OFF to disable synchronization (not recommended).
""",
    ),
    Setting(
        "SAFE_DELETE",
        "ON",
        Active,
        """If ON, the system deletes old video data only if it has been backed up
to a remote server or connected HD. If OFF, the system deletes old video data even if
no backup is found.""",
    ),
    Setting(
        "MAXIMUM_SYNC_TIME",
        1200,
        int,
        """Maximum time allowed (in seconds) to sync data. If synchronization is
not completed within this time, the process will stop to allow other animals to access
the behavioral box.""",
    ),
    Setting(
        "SYNC_DESTINATION",
        default_sync_destination,
        str,
        "The sync destination.",
    ),
    Setting(
        "SYNC_DIRECTORY",
        default_sync_directory,
        str,
        """The directory where data will be synced. This path is created inside
the sync destination, using the project name followed by the suffix _data.""",
    ),
]

server_settings = [
    Setting("SERVER_USER", "training_village", str, "The server user."),
    Setting("SERVER_HOST", "server", str, "The server hostname."),
    Setting(
        "SERVER_PORT",
        "",
        str,
        """The port number used to connect to the remote server. Leave this field empty
if you don't need to specify a particular port for the SSH connection.""",
    ),
]

device_settings = [
    Setting("MOTOR1_PIN", 12, int, "The pin of the motor 1."),
    Setting("MOTOR2_PIN", 13, int, "The pin of the motor 2."),
    Setting("SCALE_ADDRESS", "0x64", str, "The address of the scale."),
    Setting("TEMP_SENSOR_ADDRESS", "0x45", str, "The address of the temp sensor."),
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
]


hourly_alarm_settings = [
    Setting(
        "MINIMUM_TEMPERATURE",
        19,
        int,
        """Checked hourly. Minimum temperature (in Celsius). If the temperature falls
below this level, an alarm is triggered.""",
    ),
    Setting(
        "MAXIMUM_TEMPERATURE",
        27,
        int,
        """Checked hourly. Maximum temperature (in Celsius). If the temperature
exceeds this level, an alarm is triggered.""",
    ),
    Setting(
        "NO_DETECTION_HOURS",
        6,
        int,
        """Checked hourly. This alarm is triggered if no detections occur within a
specified number of hours.""",
    ),
    Setting(
        "NO_SESSION_HOURS",
        6,
        int,
        """Checked hourly. This alarm is triggered if no session is performed in the
behavioral box within a specified number of hours.""",
    ),
]

cycle_alarm_settings = [
    Setting(
        "NO_DETECTION_SUBJECT_24H",
        "ON",
        Active,
        """This check is performed every time the system switches between day and night.
If any animal has not been detected over a 24-hour period, an alarm is triggered.""",
    ),
    Setting(
        "NO_SESSION_SUBJECT_24H",
        "ON",
        Active,
        """This check is performed every time the system switches between day and night.
If any animal has not completed any task over a 24-hour period, an alarm is
triggered.""",
    ),
    Setting(
        "MINIMUM_WATER_SUBJECT_24H",
        400,
        int,
        """This check is performed every time the system switches between day and night.
If any animal drinks less than the specified minimum water intake (in mL) over a 24-hour
period, an alarm is triggered.""",
    ),
]

session_alarm_settings = [
    Setting(
        "NO_WATER_DRUNK",
        "ON",
        Active,
        """At the end of a session, an alarm is triggered if the animal has not
consumed any water.""",
    ),
    Setting(
        "NO_TRIALS_PERFORMED",
        "ON",
        Active,
        """At the end of a session, an alarm is triggered if the animal has not
completed any trials.""",
    ),
]

cam_fixed_settings = [
    Setting(
        "CAM_BOX_TRACKING_POSITION",
        "ON",
        Active,
        """Tracks the animal’s position inside the box. This feature significantly
increases CPU usage, so we recommend using it at a maximum of 30 fps and a
resolution of 640×480""",
    ),
    Setting(
        "CAM_CORRIDOR_FRAMERATE",
        10,
        int,
        """The number of frames per second at which the corridor camera
videos are saved. The recommended value is 10 fps, which provides reliable detection
while keeping the video file size low.""",
    ),
    Setting(
        "CAM_BOX_FRAMERATE",
        30,
        int,
        """The number of frames per second at which the box camera
videos are saved. The recommended value is 30 fps. If higher precision is needed for
video analysis, the frame rate can be increased up to 50 fps, but keep in mind that
this will significantly increase the file size and CPU usage.""",
    ),
    Setting(
        "CAM_BOX_RESOLUTION",
        [640, 480],
        list[int],
        """Camera resolution. Depending on the desired aspect ratio, the recommended
settings are 640 × 480 or 640 × 360, with a maximum of 1280 × 960 or 1280 × 720. Using
higher resolutions significantly increases CPU load, which makes it unsuitable for
running real-time visual stimuli. If auditory stimuli are used instead, latency may
also be affected and should therefore be measured.""",
    ),
    Setting(
        "CAM_PREVIEWS_FRAMERATE",
        5,
        int,
        """The number of frames per second for both camera previews. This setting does
not affect the frame rate at which videos are recorded. The recommended value is 5 fps,
which provides a clear view of the system activity while keeping CPU usage low.""",
    ),
]


corridor_settings = [
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
        "WEIGHT_THRESHOLD",
        10.0,
        float,
        "The minimum weight in grams to consider that the animal is on the scale.",
    ),
    Setting(
        "REPEAT_TARE_TIME",
        600,
        int,
        "The interval in seconds at which the scale is tared.",
    ),
]

extra_settings = [
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
    Setting(
        "DAYS_OF_VIDEO_STORAGE",
        7,
        int,
        "Number of days to store video data before deleting it.",
    ),
    Setting(
        "MATPLOTLIB_DPI",
        100,
        int,
        "The DPI of the matplotlib plots.",
    ),
]

controller_settings = [
    Setting(
        "BEHAVIOR_CONTROLLER",
        "BPOD",
        Controller,
        """The controller used to run the behavioral box. The options are:
        BPOD: The Bpod controller. ARDUINO: A custom controller that can be
        Arduino based. RASPBERRY: No need for an external controller.
        """,
    ),
    Setting(
        "CONTROLLER_PORT",
        "/dev/controller",
        str,
        """The USB serial port of the controller device
(e.g., Bpod, Arduino-compatible board...). Set this to the device path in /dev/.
Note: USB serial device names (e.g., ttyACM0, ttyACM1) may change each time the system
boots or if multiple devices are connected. To ensure a consistent device name,
it is recommended to create a symbolic link using udev rules. See the documentation
section "Udev rules for consistent USB device naming" for detailed instructions.
""",
    ),
]

bpod_settings = [
    Setting(
        "BPOD_BNC_PORTS",
        ["OFF", "OFF"],
        list[Active],
        "Enabled BNC ports on the Bpod.",
    ),
    Setting(
        "BPOD_BEHAVIOR_PORTS",
        ["ON", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF", "OFF"],
        list[Active],
        "Enabled behavior ports on the Bpod.",
    ),
    Setting(
        "BPOD_TARGET_FIRMWARE",
        22,
        int,
        """This system is compatible only with this Bpod firmware version. If you have
a different version, please update it by following the instructions at sanworks.com.""",
    ),
    Setting(
        "BPOD_NET_PORT",
        36000,
        int,
        "The network port of the Bpod (for sending and receiving softcodes).",
    ),
    Setting("BPOD_BAUDRATE", 256000, int, "Bpod baudrate."),
    Setting("BPOD_SYNC_CHANNEL", 255, int, "Bpod sync channel."),
    Setting("BPOD_SYNC_MODE", 1, int, "Bpod sync mode."),
]


camera_settings = [
    Setting(
        "AREA1_CORRIDOR",
        [100, 300, 200, 350, 100],
        list[int],
        """The first area of the corridor, located between the homecage and the first
door. Values include left, top, right, and bottom coordinates, along with the
detection threshold.""",
    ),
    Setting(
        "AREA2_CORRIDOR",
        [200, 300, 300, 350, 100],
        list[int],
        """The second area of the corridor, located between the first door and the
area3. Values include left, top, right, and bottom coordinates, along with the
detection threshold.""",
    ),
    Setting(
        "AREA3_CORRIDOR",
        [300, 300, 400, 350, 100],
        list[int],
        """The third area of the corridor, located between the area2 and the second
door. Values include left, top, right, and bottom coordinates, along with the
detection threshold.""",
    ),
    Setting(
        "AREA4_CORRIDOR",
        [400, 300, 500, 350, 100],
        list[int],
        """The fourth area of the corridor, located between the second door and the
behavioral box. Values include left, top, right, and bottom coordinates, along with the
detection threshold.""",
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
    Setting(
        "LENS_POSITION_CORRIDOR",
        [1.0, 1.0],
        list[float],
        "The lens position of the corridor camera (day, night).",
    ),
    Setting(
        "LENS_POSITION_BOX",
        1.0,
        float,
        "The lens position of the box camera.",
    ),
    Setting(
        "SHARPNESS_CORRIDOR",
        [1.0, 1.0],
        list[float],
        "The sharpness of the corridor camera (day, night).",
    ),
    Setting(
        "SHARPNESS_BOX",
        1.0,
        float,
        "The sharpness of the box camera.",
    ),
    Setting(
        "CONTRAST_CORRIDOR",
        [1.0, 1.0],
        list[float],
        "The contrast of the corridor camera (day, night).",
    ),
    Setting(
        "CONTRAST_BOX",
        1.0,
        float,
        "The contrast of the box camera.",
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

visual_settings = [
    Setting("COLOR_AREA1", [0, 136, 0], list[int], "The color of the first area."),
    Setting("COLOR_AREA2", [204, 51, 170], list[int], "The color of the second area."),
    Setting("COLOR_AREA3", [51, 119, 204], list[int], "The color of the third area."),
    Setting("COLOR_AREA4", [221, 51, 0], list[int], "The color of the fourth area."),
    Setting("COLOR_DETECTION", [255, 0, 255], list[int], "The color of the detection."),
    Setting("RECTANGLES_LINEWIDTH", 2, int, "The linewidth of the areas."),
    Setting("DETECTION_CIRCLE_SIZE", 5, int, "The size of the detection circle."),
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
]


settings = Settings(
    main_settings,
    sound_settings,
    screen_settings,
    touchscreen_settings,
    telegram_settings,
    directory_settings,
    sync_settings,
    server_settings,
    device_settings,
    hourly_alarm_settings,
    cycle_alarm_settings,
    session_alarm_settings,
    cam_fixed_settings,
    corridor_settings,
    extra_settings,
    controller_settings,
    bpod_settings,
    camera_settings,
    motor_settings,
    visual_settings,
    hidden_settings,
)

# settings.restore_factory_settings()
# settings.restore_visual_settings()
# settings.print()
