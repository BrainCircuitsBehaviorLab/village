## Assembly & Initial Setup

### Preliminary Steps
If you purchased a Training Village from us, the system arrives fully pre-assembled. However, should you ever need to assemble or adjust any components yourself, the process is straightforward and only requires an Allen key and a screwdriver. The setup can be easily managed by following these [instructions][INSTRUCTIONS].

We provide the Raspberry Pi along with an SD card that contains both the operating system (Raspberry Pi OS) and all required software pre-installed.

```{admonition} Build-It-Yourself
:class: note
If you prefer to build the Training Village yourself, start by reviewing the complete list of required parts and the plans for all 3D-printable pieces [here][PLANS]. Once you have your own Raspberry Pi, you can either [download][IMAGE] an image of the SD card to copy onto your device or [install everything from scratch][SOFTWARE].
```

---


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

![Boards7](/_static/boards7.png)


#### Phase 3: Peripheral & Power Distribution
**Corridor Board Setup**: Mount the Corridor Board in its fixed position on the physical corridor frame. Connect its local peripherals: servo motors, RFID reader, weighing scale (load cell), white LED strips, and IR illumination LEDs. Always double-check wiring polarities against the board silk-screen before insertion.

**Infrastructure Cabling**: Connect the Corridor Board to the Raspberry Pi assembly using a standard Ethernet cable. **It is vital to plug this into the correct port**, as the Main HAT features two distinct Ethernet ports: one labeled **Corridor** and one labeled **Box**. If your configuration utilizes the Box Board (for operant box lighting or other peripherals), connect it to the "Box" port at this time.

**Behavioral Controller (Optional)**: If your experimental paradigm integrates a Bpod (or any other external behavioral controller), connect its USB cable to the bottom USB 3.0 port (the blue port closest to the Raspberry Pi's native Ethernet jack).

**System Power**: Connect your dedicated 5V, 3A power supply directly to the power input barrel jack located on the Main HAT. Using a 3A power source is mandatory to ensure there is enough current to reliably power all visible and IR illumination LEDs simultaneously.

### First Boot & OS Configuration

To complete the initial setup, configure the internet connection, and enable remote management, you will temporarily need **local access** to the system.

The easiest way to do this is to connect a keyboard, mouse, monitor (via micro-HDMI), and a local network cable (if using a wired connection) to the Raspberry Pi **before** plugging it into a power outlet. Once these peripherals are secure, connect the main power supply; the Raspberry Pi 5 will boot up automatically.

#### Setting Up the OS:
1. On the first boot, follow the on-screen welcome wizard to configure your country, timezone, keyboard layout, and language preferences.
2. Update the system credentials when prompted. By default, the pre-configured system image uses:
   * **Username:** `pi`
   * **Password:** `training_village`
3. Leave the username as `pi`, but **change the password** to a secure one of your choice.
4. Once the setup wizard completes, configure your internet connection via the Wi-Fi icon in the top-right corner (or leave it on Ethernet).


<br><br><br>


[INSTRUCTIONS]: /resources/hardware.md
[PLANS]: /resources/list_of_parts.md
[IMAGE]: /resources/image.md
[SOFTWARE]: /resources/software_installation.md
