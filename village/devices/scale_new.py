from typing import Optional

import spidev

# Configure SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, SPI device CE0 (Chip Select)
spi.max_speed_hz = 100000  # Maximum SPI speed (100 kHz)
spi.mode = 0  # The MCP3550 uses SPI mode 0


def read_adc() -> Optional[int]:
    """Reads 3 bytes from the MCP3550, checks for overflow,
    and converts them into a 22-bit value."""
    raw_data = spi.readbytes(3)  # Read 3 bytes
    raw_value = (raw_data[0] << 16) | (raw_data[1] << 8) | raw_data[2]  # Combine bytes

    # Check for overflow (bit 23 and 24)
    if raw_value & 0xC00000:
        # 0xC00000 = 0b110000000000000000000000 (bits 23 and 24 set)
        print("Overflow detected! Value out of range.")
        return None  # Indicate an invalid reading

    # Detect negative values (22-bit two's complement)
    if raw_value & 0x200000:  # If bit 22 is set, it's a negative number
        raw_value -= 0x400000  # Adjust using two's complement

    return raw_value


# try:
#     while True:
#         value = read_adc()
#         if value is not None:
#             print(f"ADC Reading: {value}")
#         time.sleep(0.5)  # Read every 0.5 seconds

# except KeyboardInterrupt:
#     print("Exiting...")
#     spi.close()
