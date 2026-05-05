import traceback

from PCA9685_smbus2 import PCA9685  # type: ignore

from village.classes.enums import Active
from village.classes.null_classes import NullChip, NullMotor
from village.devices.motor_old import MotorOld
from village.scripts.log import log
from village.settings import settings

# Init (50 Hz for servos)
try:
    pwm_corridor = PCA9685.PCA9685(
        interface=1, address=int(settings.get("CHIP_CORRIDOR_ADDRESS"), 16)
    )
    pwm_corridor.set_pwm_freq(50)
    error_corridor = ""
except Exception:
    error_corridor = "Error connecting to the corridor chip "
    pwm_corridor = NullChip()

try:
    pwm_box = PCA9685.PCA9685(
        interface=1, address=int(settings.get("CHIP_BOX_ADDRESS"), 16)
    )
    pwm_box.set_pwm_freq(50)
    error_box = ""
except Exception:
    error_box = "Error connecting to the box chip "
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

    def open(self) -> None:
        """Moves the motor to the open position."""
        self.move(self.open_angle)

    def close(self) -> None:
        """Moves the motor to the close position."""
        self.move(self.close_angle)


class LED:
    def __init__(self, channel: int, nchannels: int, pwm) -> None:
        self.channel = channel
        self.nchannels = nchannels
        self.pwm = pwm

    def set(self, value: float) -> None:
        ticks = int(4095 * (1 - value))
        for c in range(self.channel, self.channel + self.nchannels):
            pwm_corridor.set_pwm(self.channel, 0, ticks)

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

    try:
        motor = MotorOld(pin=channel, angles=angles)
        log.info("Motor successfully initialized")
        return motor
    except Exception:
        log.error("Could not initialize motor", exception=traceback.format_exc())
        return NullMotor()


motor_corridor1: Motor | MotorOld | NullMotor
motor_corridor2: Motor | MotorOld | NullMotor

motor_box1 = get_motor(settings.get("MOTOR1_BOX_INDEX"), settings.get("MOTOR1_VALUES"), pwm_box)
motor_box2 = get_motor(settings.get("MOTOR2_BOX_INDEX"), settings.get("MOTOR2_VALUES"), pwm_box)
visible_light_corridor = LED(settings.get("VISIBLE_LIGHT_CORRIDOR_INDEX"), 1, pwm_corridor)
ir_light_corridor = LED(settings.get("IR_LIGHT_CORRIDOR_INDEX"), 4, pwm_corridor)
visible_light_box = LED(settings.get("VISIBLE_LIGHT_BOX_INDEX"), 1, pwm_box)
ir_light_box = LED(settings.get("IR_LIGHT_BOX_INDEX"), 4, pwm_box)

if settings.get("OLD_VERSION") == Active.ON:
    motor_corridor1 = get_motor_old(
        settings.get("MOTOR1_CORRIDOR_INDEX"), settings.get("MOTOR1_VALUES")
    )
    motor_corridor2 = get_motor_old(
        settings.get("MOTOR2_CORRIDOR_INDEX"), settings.get("MOTOR2_VALUES")
    )
else:
    motor_corridor1 = get_motor(
        settings.get("MOTOR1_CORRIDOR_INDEX"), settings.get("MOTOR1_VALUES"), pwm_corridor
    )
    motor_corridor2 = get_motor(
        settings.get("MOTOR2_CORRIDOR_INDEX"), settings.get("MOTOR2_VALUES"), pwm_corridor
    )
    motor_corridor1.error = error_corridor
    motor_box1.error = error_box
