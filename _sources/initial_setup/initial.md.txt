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

Before powering on the system, ensure all hardware components are properly assembled.

1. **Core Unit Assembly:** Insert the microSD card (pre-loaded with the operating system and required software) into the Raspberry Pi 5 slot. Securely mount the heat sink onto the Raspberry Pi processor.
2. **Camera Installation:** Connect the two camera ribbon cables to the Pi. For optimal signal integrity, keep these cables as short as possible. The corridor camera uses a standard 50 cm ribbon cable. If 50 cm is not long enough to reach your operant box camera mount, use a ribbon cable extension paired with a dedicated FFC adapter.
3. **Main HAT Installation:** Place the **Main HAT** onto the Raspberry Pi 5 GPIO pins. Use a GPIO header extension/spacer to increase the vertical clearance between the Pi and the HAT. **Crucial:** Ensure the Main HAT has two **5A fuses** installed before proceeding.
4. **Audio HAT Stack:** Mount the **Audio HAT** directly on top of the Main HAT. No additional spacer or vertical adapter is required for this layer.
5. **System Placement:** Carefully place the fully stacked Raspberry Pi assembly and the cameras into their designated physical positions on the corridor structure.
6. **Corridor Board Configuration:** Mount the Corridor Board in its position on the corridor and connect all of its local peripherals: servo motors, RFID reader, weighing scale, white LED strips, and IR LEDs. **Always double-check correct wiring polarities** before plugging them in.
7. **Satellite-to-Hub Wiring:** Connect the Corridor Board to the Raspberry Pi assembly using a standard Ethernet cable. **It is vital to plug this into the correct port**, as the Main HAT features two distinct Ethernet ports: one labeled **Corridor** and one labeled **Box**. If your configuration utilizes the Box Board (for operant box lighting or other peripherals), connect it to the "Box" port at this time.
8. **Behavioral Controller:** If you are using a Bpod (or any other external behavioral controller), connect it to the **bottom USB port** closest to the Raspberry Pi's onboard Ethernet port.
9. **System Power:** Connect a high-quality **5V, 3A power supply** directly to the power input on the Raspberry Pi's **Main HAT**. Using a 3A power source is mandatory to ensure there is enough current to reliably power all visible and IR illumination LEDs simultaneously.

![Connections](/_static/connections.png)

---

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

With the local setup complete and the system online, you can proceed to the next section to configure your preferred [Remote Access Method](#remote-access-setup).


<br>


[INSTRUCTIONS]: /resources/hardware.md
[PLANS]: /resources/list_of_parts.md
[IMAGE]: /resources/image.md
[SOFTWARE]: /resources/software_installation.md
