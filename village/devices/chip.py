import time
import traceback

from PCA9685_smbus2 import PCA9685  # type: ignore

from village.classes.enums import Active, OldVersion
from village.classes.null_classes import NullChip, NullMotor
from village.devices.motor_old import MotorOld
from village.scripts.log import log
from village.settings import settings

use_of_corridor: bool = settings.get("USE_CORRIDOR") == Active.ON
use_of_box_chip: bool = settings.get("USE_BOX_BOARD") == Active.ON
old_version_motor: bool = settings.get("OLD_VERSION") != OldVersion.OFF

# Init (50 Hz for servos)
# chip_corridor/chip_box only ever carry the PCA9685 connection error (Motor
# objects on this path never fail on their own, they are thin wrappers around
# a channel number and the shared chip), so motor error attributes stay "" in
# this mode -- get_motor_old() is the only path that sets a per-motor error.
chip_corridor = NullChip()
if use_of_corridor and not old_version_motor:
    try:
        pwm_corridor = PCA9685.PCA9685(
            interface=1, address=int(settings.get("CHIP_CORRIDOR_ADDRESS"), 16)
        )
        pwm_corridor.set_pwm_freq(50)
    except Exception:
        chip_corridor.error = log.clean_text(
            traceback.format_exc(), "Could not initialize corridor chip"
        )
        pwm_corridor = NullChip()
else:
    pwm_corridor = NullChip()

chip_box = NullChip()
if use_of_box_chip and not old_version_motor:
    try:
        pwm_box = PCA9685.PCA9685(
            interface=1, address=int(settings.get("CHIP_BOX_ADDRESS"), 16)
        )
        pwm_box.set_pwm_freq(50)
    except Exception:
        chip_box.error = log.clean_text(
            traceback.format_exc(), "Could not initialize box chip"
        )
        pwm_box = NullChip()
else:
    pwm_box = NullChip()


# Servo motion ramp (normal PCA9685 Motor only -- MotorOld is untouched).
# move() steps the angle in MOTOR_STEP_DEGREES-degree increments so the door
# travels smoothly instead of snapping. The MOTOR*_VALUES settings give the
# TOTAL time (ms) to open and to close; move() splits that time evenly across
# the steps of the travel (steps = ceil(distance / MOTOR_STEP_DEGREES)), so a
# 27 deg move is 6 steps and each waits total_ms / 6. 0 ms = as fast as
# possible. DEFAULT_MOTOR_TIME is used for legacy settings with no times.
MOTOR_STEP_DEGREES = 5  # degrees moved per step


def parse_motor_values(values: list[int]) -> tuple[int, int, int, int]:
    """Unpack a MOTOR*_VALUES setting into (open, close, time_open, time_close).

    time_open/time_close are the TOTAL milliseconds to open/close. Legacy
    settings only store [open, close]; missing times fall back to
    DEFAULT_MOTOR_TIME so old calibrations keep working.
    """
    open_angle = int(values[0])
    close_angle = int(values[1])
    time_open = int(values[2]) if len(values) > 2 else 0
    time_close = int(values[3]) if len(values) > 3 else 0
    return open_angle, close_angle, time_open, time_close


class Motor:
    def __init__(self, channel: int, values: list[int], pwm) -> None:
        self.pwm = pwm
        self.channel = channel
        open_angle, close_angle, time_open, time_close = parse_motor_values(values)
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.time_open = time_open  # total ms to travel to the open position
        self.time_close = time_close  # total ms to travel to the close position
        self.error = ""
        # Last commanded angle; ramps start here. The real position is unknown
        # at boot, so the first move() goes straight to the target and syncs.
        self.current_angle = close_angle
        self._initialized = False

    def servo_pulse(self, ms: float) -> int:
        # 20 ms period → 4096 ticks
        return int(ms * 4096 / 20)

    def _write_angle(self, angle: int) -> None:
        # map 0–180° → 1ms–2ms
        pulse_ms = 1 + angle / 180.0
        ticks = self.servo_pulse(pulse_ms)
        self.pwm.set_pwm(self.channel, 0, ticks)

    def move(self, angle: int, total_ms: int = 0) -> None:
        """Ramps the servo to `angle`, spreading `total_ms` over the steps.

        The travel is split into MOTOR_STEP_DEGREES-degree steps; each step waits
        total_ms / number_of_steps, so the whole move takes about total_ms. The
        first move after boot goes straight to the target (the real position is
        unknown) and just syncs current_angle; every later move ramps smoothly.
        """
        total_ms = max(0, total_ms)  # negative time -> instant, never a bad sleep
        if not self._initialized:
            self._write_angle(angle)
            self.current_angle = angle
            self._initialized = True
            return
        start = self.current_angle
        if angle == start:
            self._write_angle(angle)
            return
        span = abs(angle - start)
        num_steps = (span + MOTOR_STEP_DEGREES - 1) // MOTOR_STEP_DEGREES  # ceil
        delay = (total_ms / num_steps) / 1000.0  # seconds paused per step
        step = MOTOR_STEP_DEGREES if angle > start else -MOTOR_STEP_DEGREES
        a = start
        while a != angle:
            a += step
            if (step > 0 and a > angle) or (step < 0 and a < angle):
                a = angle  # last step: land exactly on the target
            self._write_angle(a)
            time.sleep(delay)
        self.current_angle = angle

    def disable(self) -> None:
        """Stops PWM signal to release holding torque."""
        self.pwm.set_pwm(self.channel, 0, 4096)

    def open(self) -> None:
        """Moves the motor to the open position."""
        self.move(self.open_angle, self.time_open)

    def close(self) -> None:
        """Moves the motor to the close position."""
        self.move(self.close_angle, self.time_close)


class LED:
    def __init__(self, channel: int, n_channels: int, pwm) -> None:
        self.channel = channel
        self.n_channels = n_channels
        self.pwm = pwm

    def set(self, value: float) -> None:
        ticks = int(4095 * value)
        # single channel is a visible LED strip connected to a single channel
        # multiple channels is individual IR LEDs, each connected to its own
        # channel, with inverted logic (4095 - ticks): they turn on at 0 and
        # off at 4095
        if self.n_channels == 1:
            self.pwm.set_pwm(self.channel, 0, ticks)
        else:
            for c in range(self.channel, self.channel + self.n_channels):
                self.pwm.set_pwm(c, 0, (4095 - ticks))

    def on(self) -> None:
        """Turns the LED on."""
        self.set(1.0)

    def off(self) -> None:
        """Turns the LED off."""
        self.set(0.0)


def get_motor(channel: int, values: list[int], pwm) -> Motor:
    """Factory function to create and initialize a Motor instance.

    Args:
        channel (int): The PWM channel number.
        values (list[int]): [open, close, time_open, time_close] (times are the
            total ms to open/close). Legacy [open, close] is also accepted.

    Returns:
        Motor: An initialized Motor instance.
    """

    motor = Motor(channel=channel, values=values, pwm=pwm)
    return motor


def get_motor_old(channel: int, angles: list[int]) -> MotorOld | NullMotor:
    """Factory function to create and initialize a Motor instance.

    Args:
        channel (int): The GPIO channel number.
        angles (list[int]): A list containing [open_angle, close_angle].

    Returns:
        Motor: An initialized Motor instance.
    """

    if not use_of_corridor:
        null_motor = NullMotor()
        null_motor.error = ""
        return null_motor
    try:
        motor = MotorOld(pin=channel, angles=angles)
        return motor
    except Exception:
        null_motor = NullMotor()
        null_motor.error = log.clean_text(
            traceback.format_exc(), "Could not initialize motor"
        )
        return null_motor


motor_corridor1: Motor | MotorOld | NullMotor
motor_corridor2: Motor | MotorOld | NullMotor
motor_corridor3: Motor | MotorOld | NullMotor
motor_corridor4: Motor | MotorOld | NullMotor


def get_motor_if_active(
    key: str, index_key: str, values_key: str, pwm
) -> Motor | NullMotor:
    """Builds a Motor from its settings if the `key` presence flag is ON.

    Args:
        key (str): The Active setting that gates whether this motor exists.
        index_key (str): The setting holding the motor's PWM channel index.
        values_key (str): The setting holding the motor's [open, close,
            time_open, time_close] values.
        pwm: The PWM chip (or NullChip) the motor is wired to.

    Returns:
        Motor | NullMotor: A real Motor if enabled, otherwise a NullMotor.
    """
    if settings.get(key) != Active.ON:
        return NullMotor()
    return get_motor(settings.get(index_key), settings.get(values_key), pwm)


motor_box1 = get_motor_if_active(
    "MOTOR1_BOX", "MOTOR1_BOX_INDEX", "MOTOR1_BOX_VALUES", pwm_box
)
motor_box2 = get_motor_if_active(
    "MOTOR2_BOX", "MOTOR2_BOX_INDEX", "MOTOR2_BOX_VALUES", pwm_box
)
motor_box3 = get_motor_if_active(
    "MOTOR3_BOX", "MOTOR3_BOX_INDEX", "MOTOR3_BOX_VALUES", pwm_box
)
motor_box4 = get_motor_if_active(
    "MOTOR4_BOX", "MOTOR4_BOX_INDEX", "MOTOR4_BOX_VALUES", pwm_box
)
motor_box5 = get_motor_if_active(
    "MOTOR5_BOX", "MOTOR5_BOX_INDEX", "MOTOR5_BOX_VALUES", pwm_box
)
motor_box6 = get_motor_if_active(
    "MOTOR6_BOX", "MOTOR6_BOX_INDEX", "MOTOR6_BOX_VALUES", pwm_box
)
motor_box7 = get_motor_if_active(
    "MOTOR7_BOX", "MOTOR7_BOX_INDEX", "MOTOR7_BOX_VALUES", pwm_box
)

visible_light_corridor = LED(
    settings.get("VISIBLE_LIGHT_CORRIDOR_INDEX"), 1, pwm_corridor
)
ir_light_corridor = LED(settings.get("IR_LIGHT_CORRIDOR_INDEX"), 4, pwm_corridor)
visible_light_box = LED(
    settings.get("VISIBLE_LIGHT_BOX_INDEX"),
    1,
    pwm_box if settings.get("VISIBLE_LIGHT_BOX") == Active.ON else NullChip(),
)
ir_light_box = LED(
    settings.get("IR_LIGHT_BOX_INDEX"),
    4,
    pwm_box if settings.get("IR_LIGHT_BOX") == Active.ON else NullChip(),
)

if old_version_motor:
    motor_corridor1 = get_motor_old(
        settings.get("MOTOR1_CORRIDOR_INDEX"), settings.get("MOTOR1_VALUES")
    )
    motor_corridor2 = get_motor_old(
        settings.get("MOTOR2_CORRIDOR_INDEX"), settings.get("MOTOR2_VALUES")
    )
    # The old HAT only wires up 2 servo motors, regardless of MOTOR3_CORRIDOR /
    # MOTOR4_CORRIDOR -- those settings only apply to the current PCA9685 HAT.
    motor_corridor3 = NullMotor()
    motor_corridor4 = NullMotor()
else:
    motor_corridor1 = get_motor(
        settings.get("MOTOR1_CORRIDOR_INDEX"),
        settings.get("MOTOR1_VALUES"),
        pwm_corridor,
    )
    motor_corridor2 = get_motor(
        settings.get("MOTOR2_CORRIDOR_INDEX"),
        settings.get("MOTOR2_VALUES"),
        pwm_corridor,
    )
    motor_corridor3 = get_motor_if_active(
        "MOTOR3_CORRIDOR", "MOTOR3_CORRIDOR_INDEX", "MOTOR3_VALUES", pwm_corridor
    )
    motor_corridor4 = get_motor_if_active(
        "MOTOR4_CORRIDOR", "MOTOR4_CORRIDOR_INDEX", "MOTOR4_VALUES", pwm_corridor
    )
