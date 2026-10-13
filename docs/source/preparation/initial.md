## Initial Setup

### Preliminary Steps
If you purchased a Training Village from us, the system arrives fully pre-assembled. However, should you ever need to assemble or adjust any components yourself, the process is straightforward: follow the [Assembly Guide][INSTRUCTIONS].

We provide the Raspberry Pi along with an SD card that already contains the operating system (Raspberry Pi OS) and all required software pre-installed. If you ever need to write this image onto a new SD card yourself, see [Raspberry Pi Disk Image][IMAGE] for the image and step-by-step instructions.

```{admonition} Build-It-Yourself
:class: note
If you prefer to build the Training Village yourself, start by reviewing the complete list of required parts and the plans for all 3D-printable pieces in [List of Parts & Design Files][PLANS]. Once you have your own Raspberry Pi, you can either copy the [Raspberry Pi Disk Image][IMAGE] onto its SD card or [install everything from scratch][SOFTWARE].
```

---


### Hardware Connections & First Boot

```{admonition} Never hot-plug
:class: warning
Make all the connections with both power supplies unplugged. Never plug or unplug a board, cable or peripheral while the system is powered.
```

The system uses two power supplies, both labeled in the picture below:

- The **Raspberry Pi power supply** (the official 27 W USB-C supply) powers the Raspberry Pi itself.
- The **5V power supply** (5 V, 3 A, connected to the Main HAT) powers the satellite boards and what is connected to them: servo motors, lighting, LEDs...

1. Connect the Corridor Board to the Main HAT with its two cables: the Ethernet cable (data) and the DC barrel jack cable (5 V power). It is vital to use the correct ports, as the Main HAT features two sets of connectors: one labeled **Corridor** and one labeled **Box**. If your configuration uses the Box Board (for operant box lighting or other peripherals), connect its cables to the **Box** ports at this time.
2. If your experimental paradigm integrates a Bpod (or any other external behavioral controller), connect its USB cable to the bottom USB 3.0 port (the blue port closest to the Raspberry Pi's native Ethernet jack).
3. To complete the initial setup, configure the internet connection, and enable remote management, you will temporarily need **local access** to the system. Connect a keyboard, a mouse, a monitor and, if you use a wired connection, a network cable to the Raspberry Pi. Connect the monitor to the first micro-HDMI port (**screen 1** in the picture); the second one is for the screen inside the operant box, if you use it (see [Screen & Touchscreen](../devices/screen.md)).
4. Connect the **5V power supply** to the power input barrel jack located on the Main HAT. Using a 3 A power source is mandatory to ensure there is enough current to reliably power all visible and IR illumination LEDs simultaneously.
5. Finally, connect the **Raspberry Pi power supply** to the Raspberry Pi's USB-C connector; the Raspberry Pi 5 will boot up automatically.

```{figure} /_static/connections.webp
:class: zoomable
:alt: Connections

The connectors of the Main HAT (left) and of the Raspberry Pi (right). Click to enlarge.
```

---

### Setting Up the OS

1. Go to `Preferences` -> `Control Centre` and select the tab `Localisation`.
2. Configure your country, timezone, keyboard layout, and language preferences.
3. Connect to the internet: select your Wi-Fi network from the network icon in the top bar, or check that the network cable is connected.
4. Go to `Preferences` -> `Control Centre` and select the tab `System`. By default, the pre-configured system image uses:
   * **Username:** `pi`
   * **Password:** `training_village`
5. Leave the username as `pi`, but **change the password** to a secure one of your choice.


[INSTRUCTIONS]: /resources/hardware.md
[PLANS]: /resources/list_of_parts.md
[IMAGE]: /resources/image.md
[SOFTWARE]: /resources/software_installation.md
