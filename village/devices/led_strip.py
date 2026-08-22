import traceback
from typing import Any

from pi5neo import EPixelType, Pi5Neo

from village.classes.enums import Active
from village.classes.null_classes import NullLEDStrip
from village.scripts.log import log
from village.settings import settings


def get_led_strip(
    spi_device: str = "/dev/spidev0.0",
    num_leds: int = 10,
    spi_speed_khz: int = 800,
    pixel_type: EPixelType = EPixelType.RGB,
    quiet_mode: bool = True,
    enabled: bool = True,
) -> Any | NullLEDStrip:
    """Factory function to get an instance of the LED strip.

    Args:
        spi_device (str): SPI device path
        num_leds (int): Number of LEDs in the strip
        spi_speed_khz (int): SPI speed in kHz
        pixel_type (EPixelType): Color channel order of the pixels. One of
            EPixelType.RGB / GRB / RGBW / GRBW (RGB/GRB are 3-channel,
            RGBW/GRBW have a dedicated white channel).
        quiet_mode (bool): Whether to suppress output
        enabled (bool): Whether the LED strip is physically present and should
            be initialized at all.
    Returns:
        NullLEDStrip: An instance of the LED strip class or
        a base class if disabled or initialization fails
    """
    if not enabled:
        return NullLEDStrip()
    try:
        led_strip = Pi5Neo(
            spi_device=spi_device,
            num_leds=num_leds,
            spi_speed_khz=spi_speed_khz,
            pixel_type=pixel_type,
            quiet_mode=quiet_mode,
        )
        log.info("LED strip initialized successfully.")
        return led_strip
    except Exception as e:
        log.error(
            f"Error initializing LED strip: {e}", exception=traceback.format_exc()
        )
        return NullLEDStrip()


led_strip = get_led_strip(
    spi_device=settings.get("SPI_DEVICE"),
    num_leds=settings.get("NUMBER_OF_LEDS"),
    spi_speed_khz=settings.get("SPI_SPEED_KHZ"),
    pixel_type=EPixelType[settings.get("PIXEL_TYPE").name],
    quiet_mode=True,
    enabled=settings.get("LED_STRIP_BOX") == Active.ON,
)
