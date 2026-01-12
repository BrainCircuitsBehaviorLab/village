import os
import time
import traceback

from village.classes.null_classes import NullMotor
from village.scripts.log import log
from village.settings import settings


def find_pwmchip(target_device="1f00098000.pwm") -> str:
    """Finds the PWM chip path for a given target device.

    Args:
        target_device (str): The target device name to look for. Defaults to "1f00098000.pwm".

    Returns:
        str: The path to the PWM chip or raises RuntimeError if not found.

    Raises:
        RuntimeError: If no valid PWM chip is found.
    """
    for chip in os.listdir("/sys/class/pwm"):
        if chip.startswith("pwmchip"):
            devlink = os.path.join("/sys/class/pwm", chip, "device")
            try:
                target = os.path.basename(os.readlink(devlink))
                if target == target_device:
                    return os.path.join("/sys/class/pwm", chip)
            except Exception:
                continue
    raise RuntimeError("No valid PWM chip found! Update target_device if needed.")


class Motor():
    """Controls a motor via PWM.

    Attributes:
        pin (int): The GPIO pin number used for the motor.
        pinIdx (int): The index of the pin in the internal configuration lists.
        pwmx (list[int]): Mapping of pin indices to PWM channels.
        flag (bool): State flag indicating if the motor is enabled.
        open_angle (int): The angle for the open position.
        close_angle (int): The angle for the close position.
        error (str): Error message if any.
        chip (str): The path to the PWM chip.
    """

    def __init__(self, pin: int, angles: list[int]) -> None:
        """Initializes the Motor.

        Args:
            pin (int): The GPIO pin number.
            angles (list[int]): A list containing [open_angle, close_angle].
        """
        self.pin = 0
        self.pinIdx = 0
        self.pwmx = [0, 1, 2, 3, 2, 3]
        self.flag = False
        self.open_angle = angles[0]
        self.close_angle = angles[1]
        self.error = ""
        pins = [12, 13, 14, 15, 18, 19]
        afunc = ["a0", "a0", "a0", "a0", "a3", "a3"]

        # Detect pwmchip dynamically!
        self.chip = find_pwmchip()
        if pin in pins:
            self.pin = pin
            self.pinIdx = pins.index(pin)
            # let's set pin ctrl
            os.system(f"/usr/bin/pinctrl set {self.pin} {afunc[self.pinIdx]}")
            # let export pin
            if not os.path.exists(f"{self.chip}/pwm{self.pwmx[self.pinIdx]}"):
                os.system(f"echo {self.pwmx[self.pinIdx]} > {self.chip}/export")
            # CLOCK AT 1gHZ  let put period to 20ms
            time.sleep(0.2)
            os.system(f"echo 20000000 > {self.chip}/pwm{self.pwmx[self.pinIdx]}/period")
            time.sleep(0.1)
            self.enable(False)
        else:
            self.pin = 0
            log.error("Error Invalid Pin")

    def enable(self, flag) -> None:
        """Enables or disables the motor PWM.

        Args:
            flag (bool): True to enable, False to disable.
        """
        self.flag = flag
        os.system(
            f"echo {int(self.flag)} > {self.chip}/pwm{self.pwmx[self.pinIdx]}/enable"
        )

    def __del__(self) -> None:
        """Cleans up PWM resources and resets pin control."""
        try:
            if self.pin is not None and os is not None:
                # ok take PWM out
                os.system(f"echo {self.pwmx[self.pinIdx]} > {self.chip}/unexport")
                # disable PWM Pin
                os.system(f"/usr/bin/pinctrl set {self.pin} no")
        except AttributeError:
            pass  # interpreter shutdown
        except Exception:
            pass

    def set(self, on_time_ns) -> None:
        """Sets the duty cycle in nanoseconds.

        Args:
            on_time_ns (int): The high time in nanoseconds.
        """
        if not self.flag:
            self.enable(True)
        os.system(
            f"echo {on_time_ns} > {self.chip}/pwm{self.pwmx[self.pinIdx]}/duty_cycle"
        )

    def transform(self, value: int) -> int:
        """Transforms an angle to a PWM duty cycle in nanoseconds.

        Args:
            value (int): The angle in degrees (0-180).

        Returns:
            int: The duty cycle in nanoseconds (500000 - 2500000).
        """
        # 0 to 180 degrees -> 500000 to 2500000 ns
        return int(value / 180 * 2000000 + 500000)

    def open(self) -> None:
        """Moves the motor to the open position."""
        self.set(self.transform(self.open_angle))

    def close(self) -> None:
        """Moves the motor to the close position."""
        self.set(self.transform(self.close_angle))


def get_motor(pin: int, angles: list[int]) -> Motor | NullMotor:
    """Factory function to create and initialize a Motor instance.

    Args:
        pin (int): The GPIO pin number.
        angles (list[int]): A list containing [open_angle, close_angle].

    Returns:
        MotorBase: An initialized Motor instance or a dummy MotorBase if initialization fails.
    """
    try:
        motor = Motor(pin=pin, angles=angles)
        log.info("Motor successfully initialized")
        return motor
    except Exception:
        log.error("Could not initialize motor", exception=traceback.format_exc())
        return NullMotor()


motor1 = get_motor(settings.get("MOTOR1_PIN"), settings.get("MOTOR1_VALUES"))
motor2 = get_motor(settings.get("MOTOR2_PIN"), settings.get("MOTOR2_VALUES"))
