import os
import subprocess
import time
from pathlib import Path


def find_pwmchip(target_device="1f00098000.pwm") -> str:
    """Finds the PWM chip path for a given target device.

    Args:
        target_device (str): The target device name to look for.
            Defaults to "1f00098000.pwm".

    Returns:
        str: The path to the PWM chip or raises RuntimeError if not found.

    Raises:
        RuntimeError: If no valid PWM chip is found.
    """
    for chip_path in Path("/sys/class/pwm").iterdir():
        if chip_path.name.startswith("pwmchip"):
            devlink = chip_path / "device"
            try:
                target = devlink.readlink().name
                if target == target_device:
                    return str(chip_path)
            except Exception:
                continue
    raise RuntimeError("No valid PWM chip found! Update target_device if needed.")


def angle_to_ns(angle: int) -> int:
    """Transforms an angle to the PWM high time of the old HAT servos.

    Args:
        angle (int): The angle in degrees (0-180).

    Returns:
        int: The high time in nanoseconds (500000 - 2500000).
    """
    # 0 to 180 degrees -> 500000 to 2500000 ns
    return int(angle / 180 * 2000000 + 500000)


class PwmPin:
    """One servo output of the old HAT (OLD_VERSION): a hardware PWM pin
    driven through sysfs. The servo itself (angles, ramps, hold) is MotorOld,
    in chip.py.

    Attributes:
        pin (int): The GPIO pin number used for the motor.
        pinIdx (int): The index of the pin in the internal configuration lists.
        pwmx (list[int]): Mapping of pin indices to PWM channels.
        flag (bool): State flag indicating if the PWM is enabled.
        chip (str): The path to the PWM chip.
    """

    def __init__(self, pin: int) -> None:
        """Initializes the pin, with the PWM disabled.

        Args:
            pin (int): The GPIO pin number.
        """
        self.pin = 0
        self.pinIdx = 0
        self.pwmx = [0, 1, 2, 3, 2, 3]
        self.flag = False
        pins = [12, 13, 14, 15, 18, 19]
        afunc = ["a0", "a0", "a0", "a0", "a3", "a3"]

        # Detect pwmchip dynamically!
        self.chip = find_pwmchip()
        if pin in pins:
            self.pin = pin
            self.pinIdx = pins.index(pin)
            # let's set pin ctrl
            subprocess.run(
                ["/usr/bin/pinctrl", "set", str(self.pin), afunc[self.pinIdx]]
            )
            # let export pin
            if not Path(f"{self.chip}/pwm{self.pwmx[self.pinIdx]}").exists():
                Path(self.chip, "export").write_text(f"{self.pwmx[self.pinIdx]}\n")
            # CLOCK AT 1gHZ  let put period to 20ms
            time.sleep(0.2)
            Path(self.chip, f"pwm{self.pwmx[self.pinIdx]}", "period").write_text(
                "20000000\n"
            )
            time.sleep(0.1)
            self.enable(False)
        else:
            raise ValueError(f"Invalid pin: {pin}. Must be one of {pins}.")

    def enable(self, flag) -> None:
        """Enables or disables the PWM. Disabled, the servo gets no pulses
        and releases its holding torque.

        Args:
            flag (bool): True to enable, False to disable.
        """
        self.flag = flag
        Path(self.chip, f"pwm{self.pwmx[self.pinIdx]}", "enable").write_text(
            f"{int(self.flag)}\n"
        )

    def __del__(self) -> None:
        """Cleans up PWM resources and resets pin control."""
        try:
            if self.pin is not None and os is not None:
                # ok take PWM out
                Path(self.chip, "unexport").write_text(f"{self.pwmx[self.pinIdx]}\n")
                # disable PWM Pin
                subprocess.run(["/usr/bin/pinctrl", "set", str(self.pin), "no"])
        except AttributeError:
            pass  # interpreter shutdown
        except Exception:
            pass

    def set(self, on_time_ns) -> None:
        """Sets the duty cycle in nanoseconds, enabling the PWM if needed.

        Args:
            on_time_ns (int): The high time in nanoseconds.
        """
        if not self.flag:
            self.enable(True)
        Path(self.chip, f"pwm{self.pwmx[self.pinIdx]}", "duty_cycle").write_text(
            f"{on_time_ns}\n"
        )
