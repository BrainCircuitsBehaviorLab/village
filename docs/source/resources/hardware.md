## System Assembly Guide

### Hardware Construction

You will need a few basic tools: Allen key, screwdriver, scissors, double-sided tape, and glue.

#### Phase 1: Frame Construction

The frame is built using 20×20 V-slot aluminum profiles.

::::{grid} 2
:::{grid-item}
:columns: 4
**Components**: Parts required for the standard 2-homecage version (without Eco-HAB).
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame1.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Connections**: Pieces are connected using corner couplings and set screws.
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame2.png
:width: 100%
```
:::
::::


::::{grid} 2
:::{grid-item}
:columns: 4
**Base**: Build the base first.
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame3.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Vertical Pieces**: Add the vertical pieces.
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame4.png
:width: 100%
```
:::
::::


::::{grid} 2
:::{grid-item}
:columns: 4
**Camera Mount**: Slide the 3D-printed camera mount base onto an aluminum profile.
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame5.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Enclosure**: Place the 3D-printed Raspberry Pi enclosure and complete the aluminum structure.
:::
:::{grid-item}
:columns: 8
```{image} /_static/frame6.png
:width: 100%
```
:::
::::


#### Phase 2: Base Assembly

::::{grid} 2
:::{grid-item}
:columns: 4
**Acrylic Base**: Mount the 3D-printed parts onto a 3 mm matte white acrylic base. The matte finish is important to avoid reflections.
:::
:::{grid-item}
:columns: 8
```{image} /_static/base1.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**RFID Antenna Slot**: This piece has an internal slot for an antenna. The RFID module used in this build has a built-in antenna, so no external one is needed. However, if using a different RFID module or an Eco-HAB to manage multiple antennas, one can be placed between these two pieces.
:::
:::{grid-item}
:columns: 8
```{image} /_static/base2.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Bonding**: Glue the two pieces together.
:::
:::{grid-item}
:columns: 8
```{image} /_static/base3.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Parts Mounting**: Secure the 3D-printed parts onto the acrylic base using M4 screws, tightening from below.
:::
:::{grid-item}
:columns: 8
```{image} /_static/base4.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Frame Installation**: Place the assembled base onto the aluminum frame structure.
:::
:::{grid-item}
:columns: 8
```{image} /_static/base5.png
:width: 100%
```
:::
::::


#### Phase 3: RFID & Load Cell

::::{grid} 2
:::{grid-item}
:columns: 4
**Scale & RFID Modules**: Mount the scale module (load cell with 3D-printed part) and the RFID module onto the base.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid1.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Load Cell Assembly**: Attach the 3D-printed part on top of the load cell using M4 screws.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid2.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Scale Positioning**: Mount the scale onto the base using M5 screws. It must sit straight and centered, without touching any of the surrounding parts.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid3.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**RFID Wiring**: This build uses the ID-20LA RFID reader (125 kHz). Solder a 5-pin JST-PH connector following the pin order shown in the diagram. See the [specifications](https://www.id-innovations.com/ID-3%2612%2620LA(en)%20V2.01%2020200526.pdf) for the full pinout.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid4.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**RFID Installation**: Slide the RFID module into its designated slot. Secure it with a small piece of tape to prevent movement.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid5.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Final Result**: The completed assembly with both sensors in place.
:::
:::{grid-item}
:columns: 8
```{image} /_static/rfid6.png
:width: 100%
```
:::
::::

#### Phase 4: Servo Motors

::::{grid} 2
:::{grid-item}
:columns: 4
**Servo Motors Overview**: Position the servo motors and attach the doors to them.
:::
:::{grid-item}
:columns: 8
```{image} /_static/servos1.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Horn Bonding**: Glue the servo horns onto the servos.
:::
:::{grid-item}
:columns: 8
```{image} /_static/servos2.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Servo Mounting**: Secure each servo in position using at least 2 M4 screws.
:::
:::{grid-item}
:columns: 8
```{image} /_static/servos3.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Door Attachment**: Connect the doors to the servo motors.
:::
:::{grid-item}
:columns: 8
```{image} /_static/servos4.png
:width: 100%
```
:::
::::

---

### Hardware Connections

```{admonition} CRITICAL POWER & WIRING WARNING
:class: warning
Never hot-plug peripherals: ensure the main power supply is completely disconnected before plugging or unplugging any HAT, board, servo, or sensor.
```

#### Phase 1: Raspberry Pi Assembly

::::{grid} 2
:::{grid-item}
:columns: 4
**Storage**: Insert the pre-loaded microSD card into the Raspberry Pi 5 slot.
**Cooling**: Securely mount the official Active Cooler onto the processor.
**Camera Integration**: Connect the two camera ribbon cables to the Pi. Keep cables as short as possible. The corridor camera uses a standard 50 cm ribbon cable; use an extension with a dedicated FFC adapter if needed.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards1.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Enclosure Mounting**: Place the Raspberry Pi into its dedicated 3D-printed enclosure (Raspberry Box) and secure it with screws.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards2.png
:width: 100%
```
:::
::::

#### Phase 2: HAT Stacking

::::{grid} 2
:::{grid-item}
:columns: 4
**Main HAT Preparation**: Insert two 5A fuses into their designated slots on the Main HAT. Install a GPIO header extension/spacer alongside plastic standoffs to ensure proper vertical clearance and prevent short circuits.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards3.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Main HAT Mounting**: Align and carefully press the Main HAT down onto the Raspberry Pi's 40-pin GPIO header.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards4.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Audio HAT Preparation**: Install another GPIO header extension/spacer and plastic standoffs onto the Audio HAT to stack it safely above the previous layer.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards5.png
:width: 100%
```
:::
::::

::::{grid} 2
:::{grid-item}
:columns: 4
**Audio HAT Mounting**: Press the Audio HAT firmly on top of the Main HAT, completing the primary hardware stack.
:::
:::{grid-item}
:columns: 8
```{image} /_static/boards6.png
:width: 100%
```
:::
::::

#### Phase 3: Peripheral & Power Distribution

::::{grid} 2
:::{grid-item}
:columns: 4
**Corridor Board Setup**: Mount the Corridor Board in its fixed position on the physical corridor frame. Connect its local peripherals: servo motors, RFID reader, weighing scale (load cell), white LED strips, and IR illumination LEDs. Always verify wiring polarities against the board silk-screen before insertion.
:::
:::{grid-item}
:columns: 8
:::
::::
