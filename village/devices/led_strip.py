import traceback

from pi5neo import Pi5Neo

from village.classes.abstract_classes import LEDStripBase
from village.scripts.log import log


def get_led_strip(
    spi_device: str = "/dev/spidev0.0",
    num_leds: int = 10,
    spi_speed_khz: int = 800,
    pixel_type: str = "RGB",
    quiet_mode: bool = True,
):
    """Factory function to get an instance of the LED strip.

    Args:
        spi_device (str): SPI device path
        num_leds (int): Number of LEDs in the strip
        spi_speed_khz (int): SPI speed in kHz
        pixel_type (str): Type of LED pixels 'RGB' or 'RGBW'
        quiet_mode (bool): Whether to suppress output
    Returns:
        LEDStripBase: An instance of the LED strip class or
        a base class if initialization fails
    """
    try:
        led_strip = Pi5Neo(
            spi_device=spi_device,
            num_leds=num_leds,
            spi_speed_khz=spi_speed_khz,
            quiet_mode=quiet_mode,
        )
        log.info("LED strip initialized successfully.")
        return led_strip
    except Exception as e:
        log.error(
            f"Error initializing LED strip: {e}", exception=traceback.format_exc()
        )
        return LEDStripBase()


led_strip = get_led_strip()


if __name__ == "__main__":
    import time

    led_strip = get_led_strip(num_leds=300)
    led_strip.set_led_color(0, 255, 0, 0)
    led_strip.update_strip()
    time.sleep(1)
    led_strip.set_led_color(0, 0, 255, 0)
    led_strip.update_strip()
    time.sleep(1)
    led_strip.set_led_color(0, 0, 0, 255)
    led_strip.update_strip()
    time.sleep(1)
    led_strip.clear_strip()
    led_strip.update_strip()

    _n = [0, 50, 100, 150, 160]
    for n in _n:
        led_strip = get_led_strip(num_leds=300)
        led_strip.set_led_color(n, 255, 255, 255)
        led_strip.update_strip()
        time.sleep(1)

    led_strip.clear_strip()
    led_strip.update_strip()
