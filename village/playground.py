import time

from gpiozero import LED

led = LED(18)
led.on()
time.sleep(1)
led.off()
