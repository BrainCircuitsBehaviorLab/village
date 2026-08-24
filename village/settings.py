import getpass
from pathlib import Path

from village.classes.settings_class import (
    Actions,
    Active,
    AreaActive,
    Color,
    ControllerEnum,
    Cycle,
    CycleDay,
    Info,
    OldVersion,
    PixelType,
    Samplerate,
    ScreenActive,
    Setting,
    Settings,
    SyncType,
)

default_system_name = "village01"
default_project_name = "demo-village-project"
default_project_directory = str(
    Path("/home", getpass.getuser(), "village_projects", default_project_name)
)
default_code_directory = str(Path(default_project_directory, "code"))
default_sync_destination = "/sync_destination"
default_sync_directory = str(
    Path(default_sync_destination, default_project_name + "_data")
)

main_settings = [
    Setting("SYSTEM_NAME", default_system_name, str, "The system’s unique name."),
    Setting(
        "USE_CORRIDOR",
        "ON",
        Active,
        """Enables the complete Corridor subsystem, integrating the control PCB
(RFID reader, scale, temperature sensor, motors, and lighting) and the dedicated
corridor camera. This setting also activates Telegram notifications for real-time
remote monitoring. Keep ON for fully automated Training Village experiments. Disable
only when running standalone Operant Box sessions without the corridor, such as for
tethered ephys or optogenetics recordings.""",
    ),
    Setting(
        "USE_BOX_BOARD",
        "ON",
        Active,
        """Enables the Operant Box PCB. This setting allows the Raspberry Pi to control
some box components, such as LED stimuli, visible/infrared lighting, and motors.""",
    ),
    Setting(
        "FAVOURITE_TASK",
        "None",
        str,
        """A favourite (★) task that is preselected when opening the TASKS tab, so that
the user can start a session immediately. Set to None to disable preselection.""",
    ),
]

sound_settings = [
    Setting("USE_SOUNDCARD", "OFF", Active, "Use of a soundcard."),
    Setting("SOUND_DEVICE", "default", str, "The sound device."),
    Setting("SAMPLERATE", "96000", Samplerate, "The samplerate of the sound device."),
    Setting(
        "SOUND_RAMP_MS",
        "5",
        int,
        """Duration in milliseconds of a raised-cosine smoothing ramp used to eliminate
harsh, audible clicks caused by abrupt volume changes. This cosine envelope ensures an
acoustically smooth transition, and is automatically applied to the onset (start) and
offset (end) of every sound, as well as dynamically when playback is cut short by a
stop() command. Setting this value to zero completely disables the smoothing
mechanism.""",
    ),
]

screen_settings = [
    Setting("USE_SCREEN", "OFF", ScreenActive, "Use of a regular or touch screen."),
    Setting(
        "SCREEN_RESOLUTION",
        [1600, 900],
        list[int],
        "Screen resolution.",
    ),
]

touchscreen_settings = [
    Setting(
        "TOUCHSCREEN_DEVICE",
        "",
        str,
        """Name of the touchscreen input device as it appears in
/proc/bus/input/devices (e.g. 'USB Touch USB Touch'). The system uses this
name to locate the device path automatically at startup.""",
    ),
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
    Setting(
        "CHECK_MICE_TIME",
        "20:00",
        str,
        """Deadline to confirm that the mice have been checked.
If nobody has confirmed it by this time, an alarm is triggered.""",
    ),
    Setting(
        "TELEGRAM_REPEAT_MINUTES",
        60,
        int,
        "Minutes between reminders for an alarm until it is acknowledged.",
    ),
]

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
        "SYSTEM_DIRECTORY",
        str(Path(default_project_directory, "data", default_system_name)),
        str,
        "The system directory.",
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
the operant box.""",
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


led_strip_settings = [
    Setting(
        "SPI_DEVICE",
        "/dev/spidev0.0",
        str,
        "SPI device path used to communicate with the LED strip.",
    ),
    Setting(
        "NUMBER_OF_LEDS",
        10,
        int,
        "Number of LEDs in the strip.",
    ),
    Setting(
        "SPI_SPEED_KHZ",
        800,
        int,
        "SPI bus speed in kHz.",
    ),
    Setting(
        "PIXEL_TYPE",
        "RGB",
        PixelType,
        """Color channel order of the LED strip pixels.
RGB and GRB are for 3-channel LEDs; RGBW and GRBW are for 4-channel LEDs
with a dedicated white channel.""",
    ),
]

device_settings = [
    Setting(
        "CHIP_CORRIDOR_ADDRESS", "0x55", str, "The address of the corridor PWM chip."
    ),
    Setting(
        "MOTOR1_CORRIDOR_INDEX",
        4,
        int,
        """The index of the motor 1 of the corridor. Corresponds to the first door,
which is the one closer to the homecage.""",
    ),
    Setting(
        "MOTOR2_CORRIDOR_INDEX",
        5,
        int,
        """The index of the motor 2 of the corridor. Corresponds to the second door,
which is the one closer to the operant box.""",
    ),
    Setting(
        "MOTOR3_CORRIDOR_INDEX",
        6,
        int,
        """The index of the motor 3 of the corridor. This motor can be used for
additional functions, such as raising or lowering a water bottle in the home cage.""",
    ),
    Setting(
        "MOTOR4_CORRIDOR_INDEX",
        7,
        int,
        """The index of the motor 4 of the corridor. This motor can be used for
additional functions, such as raising or lowering a water bottle in the home cage.""",
    ),
    Setting(
        "VISIBLE_LIGHT_CORRIDOR_INDEX",
        8,
        int,
        "The index of the visible light of the corridor.",
    ),
    Setting(
        "IR_LIGHT_CORRIDOR_INDEX",
        0,
        int,
        "The index of the infrared light of the corridor.",
    ),
    Setting("SCALE_ADDRESS", "0x48", str, "The address of the scale."),
    Setting(
        "SCALE_BOX_ADDRESS",
        "0x2A",
        str,
        """The I2C address of the box scale (only used if SCALE_BOX is ON).""",
    ),
    Setting("TEMP_SENSOR_ADDRESS", "0x44", str, "The address of the temp sensor."),
    Setting("CHIP_BOX_ADDRESS", "0x6a", str, "The address of the box PWM chip."),
    Setting("MOTOR1_BOX_INDEX", 4, int, "The index of the motor 1 of the box."),
    Setting("MOTOR2_BOX_INDEX", 5, int, "The index of the motor 2 of the box."),
    Setting("MOTOR3_BOX_INDEX", 6, int, "The index of the motor 3 of the box."),
    Setting("MOTOR4_BOX_INDEX", 7, int, """The index of the motor 4 of the box."""),
    Setting("MOTOR5_BOX_INDEX", 8, int, """The index of the motor 5 of the box."""),
    Setting("MOTOR6_BOX_INDEX", 9, int, """The index of the motor 6 of the box."""),
    Setting("MOTOR7_BOX_INDEX", 10, int, """The index of the motor 7 of the box."""),
    Setting(
        "VISIBLE_LIGHT_BOX_INDEX",
        11,
        int,
        "The index of the visible light of the box.",
    ),
    Setting(
        "IR_LIGHT_BOX_INDEX",
        9,
        int,
        "The index of the infrared light of the box.",
    ),
    Setting(
        "GPIO_IN",
        27,
        int,
        """BCM number of the GPIO pin used as input by GpioBase: it reads an
external signal and fires the triggers (trigger_on / trigger_off).""",
    ),
    Setting(
        "GPIO_OUT",
        26,
        int,
        """BCM number of the GPIO pin used as output by GpioBase: gpio.set_on() /
gpio.set_off() drive it. It can be used at the same time as GPIO_IN, since they are
different pins.""",
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
operant box within a specified number of hours.""",
    ),
    Setting(
        "CORRIDOR_OCCUPATION_ALARM",
        "ON",
        Active,
        """Checked hourly. This alarm is triggered if any corridor area is occupied
more than 90% of the time during the last hour, which may indicate an animal sleeping
in that area, debris in the corridor, or a false detection from a badly tuned
threshold. Whatever the cause, an area that is always occupied stops the animals from
entering and leaving the operant box normally.""",
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
If any animal drinks less than the specified minimum water intake (in µL) over a 24-hour
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
        "CAM_CORRIDOR_INDEX",
        1,
        int,
        "The index (0, 1) of the corridor camera.",
    ),
    Setting(
        "CAM_BOX_INDEX",
        0,
        int,
        "The index (0, 1) of the box camera.",
    ),
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
        "DAYTIME",
        "08:00",
        str,
        """This setting defines when the daytime cycle begins. At the start of each
cycle, the system performs various checks. The lights in the corridor will be adjusted
accordingly if they are in AUTO mode.""",
    ),
    Setting(
        "NIGHTTIME",
        "20:00",
        str,
        """This setting defines when the nighttime cycle begins. At the start of each
cycle, the system performs various checks. The lights in the corridor will be adjusted
accordingly if they are in AUTO mode.""",
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
        "MIN_WEIGHT_THRESHOLD",
        10.0,
        float,
        """Minimum weight (g) considered a valid measurement. Values below this
threshold are discarded as noise or as the animal being only partially on the scale
(not properly positioned).""",
    ),
    Setting(
        "MAX_WEIGHT_THRESHOLD",
        40.0,
        float,
        """Maximum weight (g) considered a valid measurement. Values above this
threshold are discarded as they likely reflect movement artifacts
(e.g., running or jumping), resulting in overestimated weight.""",
    ),
    Setting(
        "REPEAT_TARE_TIME",
        600,
        int,
        "The interval in seconds at which the scale is tared.",
    ),
    Setting(
        "MOTOR3_CORRIDOR",
        "ON",
        Active,
        """Whether the third corridor motor is physically present and used.""",
    ),
    Setting(
        "MOTOR4_CORRIDOR",
        "OFF",
        Active,
        """Whether a fourth corridor motor is physically present and used.""",
    ),
]

box_settings = [
    Setting(
        "MOTOR1_BOX", "ON", Active, """Whether box motor 1 is physically present."""
    ),
    Setting(
        "MOTOR2_BOX", "ON", Active, """Whether box motor 2 is physically present."""
    ),
    Setting(
        "MOTOR3_BOX", "ON", Active, """Whether box motor 3 is physically present."""
    ),
    Setting(
        "MOTOR4_BOX", "OFF", Active, """Whether box motor 4 is physically present."""
    ),
    Setting(
        "MOTOR5_BOX", "OFF", Active, """Whether box motor 5 is physically present."""
    ),
    Setting(
        "MOTOR6_BOX", "OFF", Active, """Whether box motor 6 is physically present."""
    ),
    Setting(
        "MOTOR7_BOX", "OFF", Active, """Whether box motor 7 is physically present."""
    ),
    Setting(
        "VISIBLE_LIGHT_BOX",
        "ON",
        Active,
        """Whether the box's visible light is physically present.""",
    ),
    Setting(
        "IR_LIGHT_BOX",
        "ON",
        Active,
        """Whether the box's infrared light is physically present.""",
    ),
    Setting(
        "LED_STRIP_BOX",
        "OFF",
        Active,
        """Whether an LED strip is physically present in the box.""",
    ),
    Setting(
        "SCALE_BOX",
        "OFF",
        Active,
        """Whether a scale is physically present in the box.""",
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
    Setting(
        "OLD_VERSION",
        "OFF",
        OldVersion,
        """Use the old version of the Hardware Attached on Top (HAT) that only has
2 servo motors and no LEDs.""",
    ),
]

controller_settings = [
    Setting(
        "BEHAVIOR_CONTROLLER",
        "RASPBERRY",
        ControllerEnum,
        """The controller used to run the operant box. The options are:
BPOD: The Bpod controller. ARDUINO: A custom controller that can be
Arduino based. RASPBERRY: No need for an external controller.""",
    ),
    Setting(
        "CONTROLLER_PORT",
        "/dev/controller",
        str,
        """The USB serial port path of the controller device (e.g., Bpod,
Arduino-compatible board). By default, this is set to '/dev/controller'. The system
features a pre-configured udev rule that automatically generates this consistent
symbolic link, so no manual configuration is required. Simply ensure the controller is
plugged into the designated USB port as specified in the hardware guide.
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
        [22, 23],
        list[int],
        """This system is compatible only with these Bpod firmware versions. If you have
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
        [100, 300, 200, 350, 100, 100],
        list[int],
        """The first area of the corridor, located between the homecage and the first
door. Values include left, top, right, and bottom coordinates, along with the
day and night detection thresholds.""",
    ),
    Setting(
        "AREA2_CORRIDOR",
        [200, 300, 300, 350, 100, 100],
        list[int],
        """The second area of the corridor, located between the first door and the
area3. Values include left, top, right, and bottom coordinates, along with the
day and night detection thresholds.""",
    ),
    Setting(
        "AREA3_CORRIDOR",
        [300, 300, 400, 350, 100, 100],
        list[int],
        """The third area of the corridor, located between the area2 and the second
door. Values include left, top, right, and bottom coordinates, along with the
day and night detection thresholds.""",
    ),
    Setting(
        "AREA4_CORRIDOR",
        [400, 300, 500, 350, 100, 100],
        list[int],
        """The fourth area of the corridor, located between the second door and the
operant box. Values include left, top, right, and bottom coordinates, along with the
day and night detection thresholds.""",
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
        1.0,
        float,
        "The lens position of the corridor camera.",
    ),
    Setting(
        "LENS_POSITION_BOX",
        1.0,
        float,
        "The lens position of the box camera.",
    ),
    Setting(
        "SHARPNESS_CORRIDOR",
        1.0,
        float,
        "The sharpness of the corridor camera.",
    ),
    Setting(
        "SHARPNESS_BOX",
        1.0,
        float,
        "The sharpness of the box camera.",
    ),
    Setting(
        "CORRIDOR_CYCLE_MODE",
        "AUTO",
        CycleDay,
        """Which day/night mode the corridor uses for camera detection
thresholds/exposure and for the visible/IR lights. AUTO = follow the actual
day/night; DAY = always use day values and lights; NIGHT = always use night
values and lights.""",
    ),
    Setting(
        "EXPOSURE_DAY_CORRIDOR",
        0,
        int,
        """Corridor camera exposure during the day, 0-2 (higher = brighter).
0 = Normal auto-exposure. 1 = Long mode: lets the camera use longer
exposure times, so it is brighter and cleaner when there is little
light. 2 = Long plus a brighter target (digital gain -> brightest but
noisier).""",
    ),
    Setting(
        "EXPOSURE_NIGHT_CORRIDOR",
        2,
        int,
        """Corridor camera exposure at night / IR, 0-2 (higher = brighter).
0 = Normal auto-exposure. 1 = Long mode: lets the camera use longer
exposure times, so it is brighter and cleaner when there is little
light. 2 = Long plus a brighter target (digital gain -> brightest but
noisier).""",
    ),
    Setting(
        "EXPOSURE_BOX",
        0,
        int,
        """Box camera exposure, 0-2 (higher = brighter). 0 = Normal auto-exposure.
1 = Long mode: lets the camera use longer exposure times, so it is
brighter and cleaner when there is little light. 2 = Long plus a
brighter target (digital gain -> brightest but noisier).""",
    ),
]

motor_settings = [
    Setting(
        "MOTOR1_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Corridor door 1: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR2_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Corridor door 2: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR3_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Corridor door 3: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR4_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Corridor door 4: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR1_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 1: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR2_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 2: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR3_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 3: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR4_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 4: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR5_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 5: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR6_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 6: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
    ),
    Setting(
        "MOTOR7_BOX_VALUES",
        [50, 80, 0, 300],
        list[int],
        """Box motor 7: [open, close, time_open, time_close]. Angles 0-180;
time_open/time_close = total ms to open/close (0 = instant).""",
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
    Setting("LAST_SUBJECT", "None", str, "The last subject selected in the TASKS tab."),
    Setting("MICE_CHECKED_AT", "", str, "When the mice were last checked."),
    Setting("MICE_CHECKED_BY", "", str, "Who checked the mice last."),
    Setting(
        "GITHUB_REPOSITORIES_DOWNLOADED",
        "OFF",
        Active,
        "GitHub repositories downloaded.",
    ),
    Setting(
        "DEFAULT_PROJECT_NAME", default_project_name, str, "The default project name."
    ),
    Setting(
        "GITHUB_REPOSITORY_EXAMPLES",
        [
            "https://github.com/BrainCircuitsBehaviorLab/follow-the-light-project.git",
            "https://github.com/BrainCircuitsBehaviorLab/demo-village-project.git",
        ],
        list[str],
        "GitHub repositories with downloadable example projects.",
    ),
    Setting(
        "DEFAULT_CODE_DIRECTORY",
        default_code_directory,
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
        "SCALE_BOX_WEIGHT_TO_CALIBRATE",
        20,
        float,
        """Weight in grams used to calibrate the box scale.""",
    ),
    Setting(
        "SCALE_CALIBRATION_VALUE",
        1,
        float,
        "Factor to transform electric signal to grams.",
    ),
    Setting(
        "SCALE_BOX_CALIBRATION_VALUE",
        1,
        float,
        """Factor to transform electric signal to grams, for the box scale.""",
    ),
    Setting("RFID_READER", "ON", Active, "The RFID reader status."),
    Setting("VISIBLE_BOX", "ON", Cycle, "The visible light of the box."),
    Setting("IR_BOX", "OFF", Cycle, "The infrared light of the box."),
    Setting("INFO", "INFO", Info, "The information status."),
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
    led_strip_settings,
    hourly_alarm_settings,
    cycle_alarm_settings,
    session_alarm_settings,
    cam_fixed_settings,
    corridor_settings,
    box_settings,
    extra_settings,
    controller_settings,
    bpod_settings,
    camera_settings,
    motor_settings,
    visual_settings,
    hidden_settings,
)

# settings.set("DEFAULT_PROJECT_NAME", default_project_name)
# settings.set("DEFAULT_CODE_DIRECTORY", default_code_directory)
# settings.set("GITHUB_REPOSITORIES_DOWNLOADED", "OFF")
# settings.restore_all_settings()
# settings.restore_factory_settings()
# settings.restore_visual_settings()
# settings.restore_directory_settings()
# settings.print()
