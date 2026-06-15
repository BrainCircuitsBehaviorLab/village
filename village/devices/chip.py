import threading
import traceback

from PCA9685_smbus2 import PCA9685  # type: ignore

from village.classes.enums import Active, OldVersion
from village.classes.null_classes import NullChip, NullMotor
from village.devices.motor_old import MotorOld
from village.scripts.log import log
from village.settings import settings

use_of_corridor: bool = settings.get("USE_CORRIDOR") == Active.ON
use_of_box_chip: bool = settings.get("USE_BOX_BOARD") == Active.ON
old_version_rfid: bool = settings.get("OLD_VERSION") == OldVersion.V01
old_version_motor: bool = settings.get("OLD_VERSION") != OldVersion.OFF

# Init (50 Hz for servos)
if use_of_corridor and not old_version_motor:
    try:
        pwm_corridor = PCA9685.PCA9685(
            interface=1, address=int(settings.get("CHIP_CORRIDOR_ADDRESS"), 16)
        )
        pwm_corridor.set_pwm_freq(50)
        error_corridor = ""
    except Exception:
        error_corridor = "Error connecting to the corridor chip "
        pwm_corridor = NullChip()
else:
    error_corridor = ""
    pwm_corridor = NullChip()

if use_of_box_chip and not old_version_motor:
    try:
        pwm_box = PCA9685.PCA9685(
            interface=1, address=int(settings.get("CHIP_BOX_ADDRESS"), 16)
        )
        pwm_box.set_pwm_freq(50)
        error_box = ""
    except Exception:
        error_box = "Error connecting to the box chip "
        pwm_box = NullChip()
else:
    error_box = ""
    pwm_box = NullChip()


class Motor:
    def __init__(self, channel: int, angles: list[int], pwm) -> None:
        self.pwm = pwm
        self.channel = channel
        self.open_angle = angles[0]
        self.close_angle = angles[1]
        self.error = ""

    def servo_pulse(self, ms: float) -> int:
        # 20 ms period → 4096 ticks
        return int(ms * 4096 / 20)

    def move(self, angle: int) -> None:
        # map 0–180° → 1ms–2ms
        pulse_ms = 1 + angle / 180.0
        ticks = self.servo_pulse(pulse_ms)
        self.pwm.set_pwm(self.channel, 0, ticks)

    def disable(self) -> None:
        """Stops PWM signal to release holding torque."""
        self.pwm.set_pwm(self.channel, 0, 4096)

    def open(self) -> None:
        """Moves the motor to the open position."""
        self.move(self.open_angle)
        threading.Timer(1.0, self.disable).start()

    def close(self) -> None:
        """Moves the motor to the close position."""
        self.move(self.close_angle)
        threading.Timer(1.0, self.disable).start()


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


def get_motor(channel: int, angles: list[int], pwm) -> Motor:
    """Factory function to create and initialize a Motor instance.

    Args:
        channel (int): The PWM channel number.
        angles (list[int]): A list containing [open_angle, close_angle].

    Returns:
        Motor: An initialized Motor instance.
    """

    motor = Motor(channel=channel, angles=angles, pwm=pwm)
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
        log.info("Motor successfully initialized")
        return motor
    except Exception:
        log.error("Could not initialize motor", exception=traceback.format_exc())
        return NullMotor()


motor_corridor1: Motor | MotorOld | NullMotor
motor_corridor2: Motor | MotorOld | NullMotor
motor_corridor3: Motor | MotorOld | NullMotor

motor_box1 = get_motor(
    settings.get("MOTOR1_BOX_INDEX"), settings.get("MOTOR1_VALUES"), pwm_box
)
motor_box2 = get_motor(
    settings.get("MOTOR2_BOX_INDEX"), settings.get("MOTOR2_VALUES"), pwm_box
)
motor_box3 = get_motor(
    settings.get("MOTOR3_BOX_INDEX"), settings.get("MOTOR3_VALUES"), pwm_box
)
motor_box4 = get_motor(
    settings.get("MOTOR4_BOX_INDEX"), settings.get("MOTOR4_VALUES"), pwm_box
)
motor_box5 = get_motor(
    settings.get("MOTOR5_BOX_INDEX"), settings.get("MOTOR5_VALUES"), pwm_box
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
    motor_corridor1.error = error_corridor
    motor_box1.error = error_box
