import os
import time

from village.settings import settings


class Motor:

    def __init__(self, pin: int, angles: list[int]) -> None:
        self.open_angle = angles[0]
        self.close_angle = angles[1]
        pins = [12, 13, 14, 15, 18, 19]
        afunc = ["a0", "a0", "a0", "a0", "a3", "a3"]
        self.pwmx = [0, 1, 2, 3, 2, 3]
        self.enableFlag = False
        if pin in pins:
            self.pin = pin
            self.pinIdx = pins.index(pin)
            # let's set pin ctrl
            os.system("/usr/bin/pinctrl set {} {}".format(self.pin, afunc[self.pinIdx]))
            # let export pin
            if not os.path.exists(
                "/sys/class/pwm/pwmchip2/pwm{}".format(self.pwmx[self.pinIdx])
            ):
                os.system(
                    "echo {} > /sys/class/pwm/pwmchip2/export".format(
                        self.pwmx[self.pinIdx]
                    )
                )
            # CLOCK AT 1gHZ  let put period to 20ms
            time.sleep(0.2)
            os.system(
                "echo 20000000 > /sys/class/pwm/pwmchip2/pwm{}/period".format(
                    self.pwmx[self.pinIdx]
                )
            )
            time.sleep(0.1)
            self.enable(False)
        else:
            self.pin = 0
            print("Error Invalid Pin")

    def enable(self, flag) -> None:
        self.enableFlag = flag
        os.system(
            "echo {} > /sys/class/pwm/pwmchip2/pwm{}/enable".format(
                int(self.enableFlag), self.pwmx[self.pinIdx]
            )
        )

    def __del__(self) -> None:
        if self.pin is not None:
            # ok take PWM out
            os.system(
                "echo {} > /sys/class/pwm/pwmchip2/unexport".format(
                    self.pwmx[self.pinIdx]
                )
            )
            # disable PWM Pin
            os.system("/usr/bin/pinctrl set {} no".format(self.pin))

    def set(self, onTime_us) -> None:
        if not self.enableFlag:
            self.enable(True)
        self.onTime_ns = onTime_us * 1000
        os.system(
            "echo {} > /sys/class/pwm/pwmchip2/pwm{}/duty_cycle".format(
                self.onTime_ns, self.pwmx[self.pinIdx]
            )
        )
        print("setting")

    def transform(self, value: int) -> int:
        # 0 to 180 degrees -> 500 to 2500 us
        return int(value / 180 * 2000 + 500)

    def open(self) -> None:
        self.set(self.transform(self.open_angle))
        print("opening")

    def close(self) -> None:
        self.set(self.transform(self.close_angle))
        print("closing")


motor1 = Motor(settings.get("MOTOR1_PIN"), settings.get("MOTOR1_VALUES"))
motor2 = Motor(settings.get("MOTOR2_PIN"), settings.get("MOTOR2_VALUES"))
