## LED Strip

The Training Village supports an addressable LED strip connected to the Raspberry Pi
via SPI. The strip uses the **Pi5Neo** library and is configured through
`SETTINGS` → `LED STRIP SETTINGS`.

---

### Setup

#### Hardware connection

The LED strip connects to its designated connector on the box board (3-pin connector:
5 V, GND, and signal).

#### Enabling SPI

The LED strip is driven through the SPI interface, which must be enabled in
`Preferences` → `Control Centre` → `Interfaces` (it already is in the
[Raspberry Pi Disk Image](../resources/image.md)). For long strips or matrices, also
increase the SPI buffer size, as explained in the
[manual installation](../resources/software_installation.md) (`spidev.bufsiz`).

#### Finding the device path

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

#### Settings

First enable the strip with `LED_STRIP_BOX` (`SETTINGS` → `BOX SETTINGS`): while it is
`OFF`, the strip is not used at all (see the note in
[Using It in Tasks](#using-it-in-tasks)). Then configure it under `SETTINGS` →
`LED STRIP SETTINGS`. Changes are applied when Village is restarted.

##### `SPI_DEVICE`

Path of the SPI device node. Default: `/dev/spidev0.0`.

Change this only if you are using a non-default chip select or a second SPI bus
(e.g. `/dev/spidev0.1` or `/dev/spidev1.0`).

##### `NUMBER_OF_LEDS`

Total number of LEDs in the strip. Must match the physical strip length exactly —
an incorrect value will cause some LEDs to be unreachable or produce incorrect
color output.

##### `SPI_SPEED_KHZ`

SPI bus clock speed in kHz. Default: `800` (800 kHz).

Most WS2812-compatible strips work reliably at 800 kHz. If you observe flickering
or communication errors, try lowering this value (e.g. `400`).

##### `PIXEL_TYPE`

Color channel order of the strip's pixels. Default: `RGB`. This setting must match
the hardware of your specific LED strip:

| Value | Description |
|-------|-------------|
| `RGB` | 3-channel, red–green–blue order |
| `GRB` | 3-channel, green–red–blue order *(most common for WS2812B)* |
| `RGBW` | 4-channel, with a dedicated white channel |
| `GRBW` | 4-channel, green–red–blue–white order |

```{admonition} Note
:class: note
WS2812B LEDs are physically wired as **GRB** even though the chip is commonly called
"RGB". If colors appear swapped, switch between `RGB` and `GRB`.
```

---

### Using It in Tasks

Import the module-level instance and call its methods directly:

```python
from village.devices.led_strip import led_strip

# Set LED at index 0 to red
led_strip.set_led_color(0, 255, 0, 0)

# Set LED at index 1 to green
led_strip.set_led_color(1, 0, 255, 0)

# Apply the changes — nothing is visible until update_strip() is called
led_strip.update_strip(sleep_duration=None)

# Turn off all LEDs
led_strip.clear_strip()
led_strip.update_strip(sleep_duration=None)
```

#### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `set_led_color(index, red, green, blue, white=0)` | `index`: int, colors: 0–255; `white` only for `RGBW`/`GRBW` strips | Stages a color change for one LED. |
| `fill_strip(red, green, blue, white=0)` | colors: 0–255 | Stages the same color for every LED. |
| `clear_strip()` | — | Stages all LEDs off. |
| `update_strip(sleep_duration=0.1)` | `sleep_duration`: seconds, or `None` | Sends all staged changes to the strip, then waits `sleep_duration` seconds. |

```{admonition} update_strip() waits 0.1 s by default
:class: warning
After sending the colors, `update_strip()` waits `sleep_duration` seconds, 0.1 by
default (a value of the Pi5Neo library). The strip does not need that wait, and it
blocks whatever called it: a trigger or a task would lose 100 ms on every update.
Pass `sleep_duration=None`, as in the example above, to return as soon as the colors
are sent (a few ms, see
[Timing](../system_operation/timing.md)).
```

```{admonition} Note
:class: note
If `LED_STRIP_BOX` is `OFF`, or the strip cannot be initialised (SPI not enabled, wrong
device path, etc.), the system uses a `NullLEDStrip` instance instead: calls to its
methods have no effect, so tasks still run without errors, but nothing lights up.
When the initialisation fails, an error is logged at startup.
```

#### LED matrices

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
