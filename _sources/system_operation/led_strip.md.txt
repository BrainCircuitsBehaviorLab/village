## LED Strip

The Training Village supports an addressable LED strip connected to the Raspberry Pi
via SPI. The strip uses the **Pi5Neo** library and is configured through
`SETTINGS` → `LED STRIP SETTINGS`.

### Hardware connection

The LED strip connects to its designated connector on the box board (3-pin connector:
5 V, GND, and signal).

### Finding the device path

Verify the device is present:

```
ls /dev/spidev*
```

A typical output is:

```
/dev/spidev0.0   /dev/spidev0.1
```

Use the path that matches your wiring — the first device (`/dev/spidev0.0`) is the
default.

---

### Settings

Configure the LED strip under `SETTINGS` → `LED STRIP SETTINGS`.

#### `SPI_DEVICE`

Path of the SPI device node. Default: `/dev/spidev0.0`.

Change this only if you are using a non-default chip select or a second SPI bus
(e.g. `/dev/spidev0.1` or `/dev/spidev1.0`).

#### `NUMBER_OF_LEDS`

Total number of LEDs in the strip. Must match the physical strip length exactly —
an incorrect value will cause some LEDs to be unreachable or produce incorrect
color output.

#### `SPI_SPEED_KHZ`

SPI bus clock speed in kHz. Default: `800` (800 kHz).

Most WS2812-compatible strips work reliably at 800 kHz. If you observe flickering
or communication errors, try lowering this value (e.g. `400`).

#### `PIXEL_TYPE`

Color channel order of the strip's pixels. This setting must match the hardware of
your specific LED strip:

| Value | Description |
|-------|-------------|
| `RGB` | 3-channel, red–green–blue order |
| `GRB` | 3-channel, green–red–blue order *(most common for WS2812B)* |
| `RGBW` | 4-channel, with a dedicated white channel |
| `GRBW` | 4-channel, green–red–blue–white order |

```{admonition} Note
:class: tip
WS2812B LEDs are physically wired as **GRB** even though the chip is commonly called
"RGB". If colors appear swapped, switch between `RGB` and `GRB`.
```

---

### LED matrices

Addressable LEDs are not limited to linear strips. The same hardware and settings
work with **2D LED matrices**, where rows of LEDs are wired end-to-end in a
serpentine or sequential layout. From the software's perspective a matrix is just a
longer strip: `NUMBER_OF_LEDS` should be set to **width × height** (total pixel
count), and each LED is still addressed by a single integer index.

To target a specific cell, convert its row and column to a linear index:

```python
def led_index(row: int, col: int, width: int) -> int:
    return row * width + col
```

If the matrix uses a **serpentine layout** (alternating rows run in opposite
directions, which is common in pre-assembled panels), odd rows must be mirrored:

```python
def led_index_serpentine(row: int, col: int, width: int) -> int:
    if row % 2 == 0:
        return row * width + col
    else:
        return row * width + (width - 1 - col)
```

---

### Using the LED strip in tasks

Import the module-level instance and call its methods directly:

```python
from village.devices.led_strip import led_strip

# Set LED at index 0 to red
led_strip.set_led_color(0, 255, 0, 0)

# Set LED at index 1 to green
led_strip.set_led_color(1, 0, 255, 0)

# Apply the changes — nothing is visible until update_strip() is called
led_strip.update_strip()

# Turn off all LEDs
led_strip.clear_strip()
led_strip.update_strip()
```

#### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `set_led_color(index, red, green, blue)` | `index`: int, colors: 0–255 | Stages a color change for one LED. |
| `update_strip()` | — | Sends all staged changes to the strip. |
| `clear_strip()` | — | Stages all LEDs off. Call `update_strip()` afterwards. |

```{admonition} Note
:class: note
If the LED strip cannot be initialised (SPI not enabled, wrong device path, etc.)
the system falls back silently to a `NullLEDStrip` instance. Calls to its methods
have no effect, so tasks will still run without errors.
```
