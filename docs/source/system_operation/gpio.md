## GPIO

A GPIO (General Purpose Input/Output) pin is a digital pin on the Raspberry Pi
that can either read an external signal (input) or drive one (output). Unlike
the specialized connectors on the corridor and box boards (servos, lighting,
RFID...), a GPIO pin has no fixed purpose — it is a generic way to wire the
system to whatever external hardware you need: an optogenetics TTL line, a
lickometer, a mechanical switch, a sync pulse to another device, and so on.

### Voltage

The Raspberry Pi's GPIO pins operate at **3.3 V logic** and are **not 5 V
tolerant** — connecting a 5 V signal directly to an input pin can damage the
Pi. If your external hardware works at 5 V or higher, use a level shifter, a
relay, or an optocoupler between it and the Pi rather than wiring it directly.

- **Input**: reads HIGH (~3.3 V) or LOW (~0 V). The pin is configured with an
  internal pull-down, so an unconnected input reads LOW by default.
- **Output**: drives HIGH (3.3 V) or LOW (0 V). Like all Raspberry Pi GPIO
  pins, it can only source a small current (a few mA) — enough to trigger a
  relay, optocoupler, or logic-level input on another device, but not enough
  to drive a motor, solenoid, or high-power LED directly.

### Where to connect

You can wire directly to the Raspberry Pi's 40-pin GPIO header. In the
standard assembly, though, the Main HAT and Audio HAT are stacked on top of
the Pi using pass-through GPIO header extensions (see
[Raspberry Pi Assembly](../resources/hardware.md)), so every pin — including
`GPIO_IN`/`GPIO_OUT` — is also exposed on the header on top of the HAT stack,
which is usually easier to reach once the Pi is mounted in its enclosure.

```{admonition} Note
:class: note
`SETTINGS` uses **BCM numbering** for `GPIO_IN`/`GPIO_OUT` (the Broadcom
channel number), not the physical pin position on the 40-pin header — see the
pinout below.
```

```{image} /_static/pinout.png
:width: 100%
:alt: Raspberry Pi GPIO pinout (BCM numbering)
```

### Default pins

By default `GPIO_IN` is BCM 27 and `GPIO_OUT` is BCM 26 (`SETTINGS` →
`DEVICE ADDRESSES`). Both are free — neither the Main HAT nor the Audio HAT
uses them — so they are safe to use as-is.

`GPIO_IN` (BCM 27) is already wired, at the PCB level, to the **Switch
Connector** on the Box Board: it lets a mechanical switch drive the pin
directly, going HIGH when the switch is activated and LOW when it is
released, without any extra wiring. See
[Satellite Board 2: The Box Board](../overview/system.md#satellite-board-2-the-box-board)
for the full list of Box Board connectors.

If you need the input or output pin for something else, change `GPIO_IN` /
`GPIO_OUT` in `SETTINGS` to any other free BCM number and wire your hardware
to that pin instead.

### Using the output pin

The output pin (`GPIO_OUT`) is available at all times via `gpio.set_on()` and
`gpio.set_off()`, regardless of the input pin's state — call them from
anywhere: a task, a trigger, a direct function, the screen sync, and so on.

```python
from village.devices.gpio import gpio

gpio.set_on()   # drives GPIO_OUT HIGH
gpio.set_off()  # drives GPIO_OUT LOW
```

---

See [GPIO Trigger](../protocols/gpio_trigger.md) for how to react to the input
pin from your task code.
