from time import perf_counter

import numpy as np
from pi5neo import EPixelType

from village.devices.led_strip import get_led_strip

spi = 800  # has to be 800 kHz
iters = 10
num_leds_list = [1, 10, 50, 100, 150, 200, 250, 300]

initialize_durations = {num: np.zeros(iters) for num in num_leds_list}
fill_durations = {num: np.zeros(iters) for num in num_leds_list}
update_durations = {num: np.zeros(iters) for num in num_leds_list}

for num_led in num_leds_list:
    # Measure initialization latency
    for iter_idx in range(iters):
        start_init = perf_counter()
        led_strip = get_led_strip(
            "/dev/spidev0.0",
            num_leds=num_led,
            spi_speed_khz=spi,
            pixel_type=EPixelType.RGB,
            quiet_mode=True,
        )
        t_init = perf_counter() - start_init
        initialize_durations[num_led][iter_idx] = t_init

    # Create one strip for update benchmarking
    led_strip = get_led_strip(
        "/dev/spidev0.0",
        num_leds=num_led,
        spi_speed_khz=spi,
        pixel_type=EPixelType.RGB,
        quiet_mode=True,
    )

    # Measure fill and update latency
    for iter_idx in range(iters):
        start_fill = perf_counter()
        for i in range(led_strip.num_leds):
            led_strip.set_led_color(i, 10, 10, 10)
        t_fill = perf_counter() - start_fill
        fill_durations[num_led][iter_idx] = t_fill

        start_update = perf_counter()
        led_strip.update_strip(sleep_duration=None)
        t_update = perf_counter() - start_update
        update_durations[num_led][iter_idx] = t_update

        # Reset strip so we can see the strip flicker
        for i in range(led_strip.num_leds):
            led_strip.set_led_color(i, 0, 0, 0)
        led_strip.update_strip()

print("Initialization latencies (s):")
for n in num_leds_list:
    print(
        f"{n:3d} LEDs: "
        f"{initialize_durations[n].mean()*1000:.3f} ms "
        f"± {initialize_durations[n].std()*1000:.3f} ms"
    )

print("\nFill latencies (s):")
for n in num_leds_list:
    print(
        f"{n:3d} LEDs: "
        f"{fill_durations[n].mean()*1000:.3f} ms "
        f"± {fill_durations[n].std()*1000:.3f} ms"
    )

print("\nUpdate latencies (s):")
for n in num_leds_list:
    print(
        f"{n:3d} LEDs: "
        f"{update_durations[n].mean()*1000:.3f} ms "
        f"± {update_durations[n].std()*1000:.3f} ms"
    )


# Results:
# Initialization latencies (s):
#   1 LEDs: 200.668 ms ± 0.769 ms
#  10 LEDs: 201.185 ms ± 0.708 ms
#  50 LEDs: 203.113 ms ± 0.794 ms
# 100 LEDs: 204.192 ms ± 0.105 ms
# 150 LEDs: 206.820 ms ± 0.471 ms
# 200 LEDs: 209.313 ms ± 1.729 ms
# 250 LEDs: 211.002 ms ± 0.766 ms
# 300 LEDs: 212.653 ms ± 0.262 ms

# Fill latencies (s):
#   1 LEDs: 0.015 ms ± 0.003 ms
#  10 LEDs: 0.023 ms ± 0.003 ms
#  50 LEDs: 0.040 ms ± 0.003 ms
# 100 LEDs: 0.077 ms ± 0.024 ms
# 150 LEDs: 0.128 ms ± 0.004 ms
# 200 LEDs: 0.166 ms ± 0.006 ms
# 250 LEDs: 0.209 ms ± 0.020 ms
# 300 LEDs: 0.246 ms ± 0.011 ms

# Update latencies (s):
#   1 LEDs: 0.440 ms ± 0.620 ms
#  10 LEDs: 0.531 ms ± 0.030 ms
#  50 LEDs: 1.942 ms ± 0.026 ms
# 100 LEDs: 3.854 ms ± 0.222 ms
# 150 LEDs: 6.140 ms ± 0.300 ms
# 200 LEDs: 8.069 ms ± 0.121 ms
# 250 LEDs: 10.237 ms ± 0.444 ms
# 300 LEDs: 12.109 ms ± 0.336 ms
