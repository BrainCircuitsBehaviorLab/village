import time

from PCA9685_smbus2 import PCA9685  # type: ignore

# Init
pwm = PCA9685.PCA9685(i2c_bus=1, address=0x40)

# ---- SERVOS (50 Hz) ----
pwm.set_pwm_freq(50)


def servo_pulse(ms):
    # 20 ms period → 4096 ticks
    return int(ms * 4096 / 20)


def set_servo(channel, angle):
    # map 0–180° → 1ms–2ms
    pulse_ms = 1 + (angle / 180.0)
    ticks = servo_pulse(pulse_ms)
    pwm.set_pwm(channel, 0, ticks)


# Move servos
set_servo(1, 0)
set_servo(2, 180)
time.sleep(1)

set_servo(1, 90)
set_servo(2, 90)
time.sleep(1)
