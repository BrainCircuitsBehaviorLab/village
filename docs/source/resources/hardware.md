## System Assembly Guide






### Hardware Connections

```{admonition} CRITICAL POWER & WIRING WARNING
:class:warning
Never hot-plug peripherals: Ensure the main power supply is completely disconnected before plugging or unplugging any HAT, board, servo, or sensor.
```

#### Phase 1: Core Raspberry Pi Assembly
**Storage & Cooling**: Insert the pre-loaded microSD card into the Raspberry Pi 5 slot. Securely mount the official Active Cooler onto the Raspberry Pi processor.
**Camera Integration**: Connect the two camera ribbon cables to the Pi. For optimal signal integrity, keep these cables as short as possible. The corridor camera uses a standard 50 cm ribbon cable. If 50 cm is not long enough to reach your operant box camera mount, use a ribbon cable extension paired with a dedicated FFC adapter.

![Boards1](/_static/boards1.png)

**Enclosure Mounting**: Place the Raspberry Pi into its dedicated 3D-printed enclosure (Raspberry Box) and secure it with screws.

![Boards2](/_static/boards2.png)

#### Phase 2: HAT Stacking Architecture
**Main HAT Preparation**: Insert two 5A fuses into their designated slots on the Main HAT. To ensure proper vertical clearance and prevent short circuits between components, install a GPIO header extension/spacer alongside plastic standoffs on the board.

![Boards3](/_static/boards3.png)

**Main HAT Mounting**: Align and carefully press the Main HAT down onto the Raspberry Pi’s 40-pin GPIO header.

![Boards4](/_static/boards4.png)

**Audio HAT Preparation**: Install another GPIO header extension/spacer and plastic standoffs onto the Audio HAT to stack it safely above the previous layer.

![Boards5](/_static/boards5.png)

**Audio HAT Mounting**: Press the Audio HAT firmly on top of the Main HAT, completing the primary hardware stack.

![Boards6](/_static/boards6.png)


#### Phase 3: Peripheral & Power Distribution
**Corridor Board Setup**: Mount the Corridor Board in its fixed position on the physical corridor frame. Connect its local peripherals: servo motors, RFID reader, weighing scale (load cell), white LED strips, and IR illumination LEDs. Always double-check wiring polarities against the board silk-screen before insertion.
