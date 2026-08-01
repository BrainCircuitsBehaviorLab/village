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
# move() steps the angle in MOTOR_STEP_DEGREES-degree increments, pausing `speed`
# milliseconds after each step, so the door travels slowly and smoothly instead
# of snapping to the target. Travel time is approx:
#   (abs(target - start) / MOTOR_STEP_DEGREES) * speed_ms
# Per-motor speeds live in the MOTOR*_VALUES settings (speed_open, speed_close);
# higher = slower, 0 = as fast as possible. DEFAULT_MOTOR_SPEED is used for
# legacy settings that only store [open, close] with no speeds.
MOTOR_STEP_DEGREES = 5  # degrees moved per step
DEFAULT_MOTOR_SPEED = 30  # ms paused per step when the setting has no speed


def parse_motor_values(values: list[int]) -> tuple[int, int, int, int]:
    """Unpack a MOTOR*_VALUES setting into (open, close, speed_open, speed_close).

    Legacy settings only store [open, close]; missing speeds fall back to
    DEFAULT_MOTOR_SPEED so old calibrations keep working.
    """
    open_angle = int(values[0])
    close_angle = int(values[1])
    speed_open = int(values[2]) if len(values) > 2 else DEFAULT_MOTOR_SPEED
    speed_close = int(values[3]) if len(values) > 3 else DEFAULT_MOTOR_SPEED
    return open_angle, close_angle, speed_open, speed_close


class Motor:
    def __init__(self, channel: int, values: list[int], pwm) -> None:
        self.pwm = pwm
        self.channel = channel
        open_angle, close_angle, speed_open, speed_close = parse_motor_values(values)
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.speed_open = speed_open  # ms paused per step while opening
        self.speed_close = speed_close  # ms paused per step while closing
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

    def move(self, angle: int, speed: int) -> None:
        """Ramps the servo to `angle` in steps, pausing `speed` ms after each.

        The first move after boot goes straight to the target (the real
        position is unknown, so ramping from an assumed start could jerk) and
        just syncs current_angle; every later move ramps smoothly.
        """
        if not self._initialized:
            self._write_angle(angle)
            self.current_angle = angle
            self._initialized = True
            return
        start = self.current_angle
        if angle == start:
            self._write_angle(angle)
            return
        step = MOTOR_STEP_DEGREES if angle > start else -MOTOR_STEP_DEGREES
        a = start
        while a != angle:
            a += step
            if (step > 0 and a > angle) or (step < 0 and a < angle):
                a = angle  # last step: land exactly on the target
            self._write_angle(a)
            time.sleep(speed / 1000)
        self.current_angle = angle

    def disable(self) -> None:
        """Stops PWM signal to release holding torque."""
        self.pwm.set_pwm(self.channel, 0, 4096)

    def open(self) -> None:
        """Moves the motor to the open position."""
        self.move(self.open_angle, self.speed_open)

    def close(self) -> None:
        """Moves the motor to the close position."""
        self.move(self.close_angle, self.speed_close)


class LED:
    def __init__(self, channel: int, led_strip: bool, pwm) -> None:
        self.channel = channel
        self.led_strip = led_strip
        self.pwm = pwm

    def set(self, value: float) -> None:
        ticks = int(4095 * value)
        if self.led_strip:
            self.pwm.set_pwm(self.channel, 0, ticks)
        else:
            for c in range(self.channel, self.channel + 4):
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
        values (list[int]): [open, close, speed_open, speed_close]. Legacy
            settings with only [open, close] are also accepted.

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

motor_box1 = get_motor(
    settings.get("MOTOR1_BOX_INDEX"), settings.get("MOTOR1_BOX_VALUES"), pwm_box
)
motor_box2 = get_motor(
    settings.get("MOTOR2_BOX_INDEX"), settings.get("MOTOR2_BOX_VALUES"), pwm_box
)
motor_box3 = get_motor(
    settings.get("MOTOR3_BOX_INDEX"), settings.get("MOTOR3_BOX_VALUES"), pwm_box
)
visible_light_corridor = LED(
    settings.get("VISIBLE_LIGHT_CORRIDOR_INDEX"), True, pwm_corridor
)
ir_light_corridor = LED(settings.get("IR_LIGHT_CORRIDOR_INDEX"), False, pwm_corridor)
visible_light_box = LED(settings.get("VISIBLE_LIGHT_BOX_INDEX"), True, pwm_box)
ir_light_box = LED(settings.get("IR_LIGHT_BOX_INDEX"), False, pwm_box)

if old_version_motor:
    motor_corridor1 = get_motor_old(
        settings.get("MOTOR1_CORRIDOR_INDEX"), settings.get("MOTOR1_VALUES")
    )
    motor_corridor2 = get_motor_old(
        settings.get("MOTOR2_CORRIDOR_INDEX"), settings.get("MOTOR2_VALUES")
    )
    motor_corridor3 = NullMotor()
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
    motor_corridor3 = get_motor(
        settings.get("MOTOR3_CORRIDOR_INDEX"),
        settings.get("MOTOR3_VALUES"),
        pwm_corridor,
    )
