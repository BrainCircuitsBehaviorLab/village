## Troubleshooting Guide

The Training Village is a multi-component system where hardware, software, and behavior intersect. Minor miscalibrations or component failures can lead to sub-optimal performance. Typically, small issues may arise during the first few days of deployment as the animals habituate and the sensors are fine-tuned.

When a system anomaly is detected, an automated alert is instantly dispatched via Telegram. It is crucial to respond promptly to these alarms by logging in remotely to investigate exactamente cual fue la causa del error, mirando los videos del corridor y la operant box. Una puerta que no cierra bien o un fallo de iluminacion puede producir diferentes tipos de errores, WRONG RFID DETECTION, que haya 2 animales dentro de la operant box, que el sistema crea que hay un animal en la operant box pero no haya ninguno, que el sistema crea que no hay ningun animal en la operant box pero en realidad haya uno.


The Training Village is a multi-component system where hardware, software, and behavior intersect. Minor miscalibrations or component failures can lead to suboptimal performance. Typically, small issues may arise during the first few days of deployment as the animals habituate and the sensors are fine-tuned.

When a system anomaly is detected, an automated alert is instantly dispatched via Telegram. It is crucial to respond promptly by logging in remotely to investigate the root cause of the error, reviewing the corridor and operant box video recordings. For example: a door that does not close properly or a lighting failure can produce several types of errors: incorrect RFID detection, two animals simultaneously entering the operant box, the system registering an animal as present when the box is empty, or the system failing to detect an animal that is actually inside.


---

### Illumination & Tracking Issues

Many gating or tracking failures are not caused by software bugs, but by physical lighting conditions.

#### Symptom: Double Entries or Wrong RFID detections
If you notice that two animals are entering the operant box simultaneously, or that a gate closes while an animal is still in the corridor, the cause is usually **optical reflections**.
* **The Cause:** The computer vision algorithm relies on a clean binarized pixel count. If there are glare reflections on the clear acrylic corridor ceiling, the camera can become "blind" to those reflection zones. For example, if a second animal is standing directly under a heavy glare reflection, its pixels will not be counted. The system will assume the corridor is empty and mistakenly open the gate for an RFID-tagged animal, leading to double entries or wrong rfid detections.
* **The Solution:** Adjust the physical positioning or angles of your external room lights. Ensure the corridor is shielded from direct overhead glare. While the camera automatically adjusts its exposure between day (`VISIBLE`) and night (`IR`) modes to keep images consistent, it cannot filter out localized mirror-like reflections on plastic surfaces.

#### Symptom: Broken Video-Tracking inside the Operant Box
If the advanced center-of-mass tracking (`findContours`) is dropping or jumping erratically inside the behavioral arena, inspect the box illumination profile.
* **The Cause:** The operant box tracking requires highly uniform illumination (either visible or IR, depending on your paradigm).
* **The Solution:** Ensure the LED strips inside the box are clean and fully functional. **Never open the operant box door while a behavioral session is actively running**, as the sudden influx of external room light will completely disrupt the binarization thresholds and crash the real-time tracking tracking loop.

---

### Camera Issues (Connection Error or Malfunctioning)

1. **Verify Physical Connections:** Ensure both camera ribbon cables are firmly seated in the Raspberry Pi 5 MIPI CSI slots and that the white locking clips are fully engaged.
2. **Check Camera Indices:** Open the application GUI, navigate to `SETTINGS` → `CAMERA SETTINGS`, and verify that your camera indices are properly assigned (typically one is `0` and the other is `1`).
   * `CAM_CORRIDOR_INDEX`: `0` or `1`
   * `CAM_BOX_INDEX`: `0` or `1`
3. **Reboot:** If you swapped indices or re-seated the cables, restart the system to allow the OS to re-initialize the video devices.

---

### Controller Issues (Bpod or Arduino Connection Error)

1. **Verify Physical Port:** Ensure your behavioral controller is plugged into the **bottom USB 3.0 port** (the bottom blue port closest to the Raspberry Pi’s onboard Ethernet connector).
2. **Verify App Settings:** Navigate to `SETTINGS` → `CONTROLLER SETTINGS` in the GUI. Ensure your specific controller type is selected and the device path is set exactly to `/dev/controller`.
3. **Check System Devices:** Open a terminal and check if Linux detects the hardware as a raw serial interface by running:
```
ls /dev/ttyACM* /dev/ttyUSB*
```
4. **Isolate Hardware**: If no device appears in step 3, try replacing the USB cable. Use a shorter, high-quality, shielded USB cable to prevent electromagnetic interference.
5. **Verify Symbolic Link**: Check if the automated udev rule successfully generated your symlink by running:
```
ls -l /dev/controller
```
6. **Fix Missing Symlink:** If the raw device (`ttyACM*` or `ttyUSB*`) appears but `/dev/controller` is missing, inspect the system logs by typing `dmesg` to find the exact port configuration, then review your rule file at `/etc/udev/rules.d/99-usb.rules`.

```{admonition} Understanding Symlinks, udev Rules & /dev/controller
:class: tip
A **symlink** (short for symbolic link) is a software shortcut in Linux that transparently redirects one file path to another.

* **Why it is necessary:** When you connect a serial device (like a Bpod or Arduino) to the Raspberry Pi, Linux dynamically assigns it a generic node path like `/dev/ttyACM0` or `/dev/ttyUSB0`. However, if the device is unplugged, if the Pi reboots, or if another USB peripheral is connected, Linux might randomly reassign that hardware to `/dev/ttyACM1`. If the Training Village software were hardcoded to look for a static name like `ttyACM0`, the connection would instantly break.
* **The Automated Solution (`udev` rules):** To prevent this, Linux uses a background device manager called `udev`. The Training Village comes pre-configured with a custom rule file (located at `/etc/udev/rules.d/99-usb.rules`) containing the following instruction: `SUBSYSTEM=="tty", KERNELS=="3-1:1.0", SYMLINK+="controller"`

* **How this udev rule works:** `SUBSYSTEM=="tty"`: Filters the incoming hardware events and tells Linux to only trigger this rule if the connected device is a serial/terminal interface (like a USB microcontroller). `KERNELS=="3-1:1.0"`: instead of looking at what device is plugged in, it looks at where it is plugged in. `3-1:1.0` corresponds to the exact physical address of the bottom USB port adjacent to the Raspberry Pi 5 Ethernet jack. `SYMLINK+="controller"`: If a serial device matches the criteria above, udev automatically creates a permanent, unchangeable symbolic link shortcut named /dev/controller pointing straight to it.

Thanks to this rule, no matter what microcontroller you plug into that specific bottom port, and regardless of the generic name Linux gives it internally, the Training Village software can always find your behavioral controller seamlessly.

```

---

### Peripheral Issues (Sensors, Motors, Lights, or Satellite Boards)

1. **Verify Software Activation:** Open the GUI and ensure the specific satellite board you are trying to communicate with is enabled under `SETTINGS` → `MAIN SETTINGS`. Toggle `USE_CORRIDOR` or `USE_BOX_BOARD` to **`ON`** depending on your active setup.
2. **Verify Satellite Connections:** Check that the failing component (servo, LED strip, RFID antenna) is securely connected to the correct ports on the Corridor Board or Box Board with the correct wiring polarity.
3. **Check Hub-to-Satellite Cables:** Ensure the Ethernet cables linking the Corridor Board and Box Board are plugged into their respective dedicated ports on the Main HAT.
4. **Check HAT Seating:** Ensure the Main HAT is fully pressed down and evenly seated onto the Raspberry Pi 5 GPIO header extension pins.
5. **Test Power Lines:** Verify that the Main HAT is receiving a stable **5V (3A)** from the main power supply. A drop in voltage can cause I2C chips, scales, or servos to drop off the bus randomly.
6. **Verify I2C & Register Addresses:** Ensure the software is pointing to the correct I2C addresses and chip register pins. If your hardware profile has been modified, cross-reference your configuration under `SETTINGS` → `DEVICE ADDRESSES`:

| Device Parameter | Default Value / Address | Description |
| :--- | :--- | :--- |
| **`CHIP_CORRIDOR_ADDRESS`** | `0x55` | Main I2C chip address on the Corridor Board |
| **`MOTOR1_CORRIDOR_INDEX`** | `4` | Pin channel for Corridor Door 1 Servo |
| **`MOTOR2_CORRIDOR_INDEX`** | `5` | Pin channel for Corridor Door 2 Servo |
| **`VISIBLE_LIGHT_CORRIDOR_INDEX`** | `6` | Pin channel for White LED illumination strip |
| **`IR_LIGHT_CORRIDOR_INDEX`**| `0` | Pin channel for Infrared LED arrays |
| **`SCALE_ADDRESS`** | `0x48` | Onboard scale/load cell amplifier address |
| **`TEMP_SENSOR_ADDRESS`** | `0x44` | Ambient temperature sensor address |
| **`CHIP_BOX_ADDRESS`** | `0x6a` | Main I2C chip address on the Box Board |
| **`MOTOR1_BOX_INDEX`** | `4` | Pin channel for Box Module Servo 1 |
| **`MOTOR2_BOX_INDEX`** | `5` | Pin channel for Box Module Servo 2 |
| **`VISIBLE_LIGHT_BOX_INDEX`** | `6` | Pin channel for Box Visible light |
| **`IR_LIGHT_BOX_INDEX`** | `0` | Pin channel for Box IR light |


---

### Data Synchronization Issues

If you suspect a transfer issue, you can inspect the detailed synchronization logs generated by the system. The log files are stored locally in the following directory:

`/home/pi/village_projects/YOUR_PROJECT/data/YOUR_SYSTEM/rsync_logs`

If the synchronization routine fails repeatedly, the system will broadcast an automated warning to your team's Telegram channel:

**Alarm**: No data sync in the last 24h

**Meaning**: No data has been successfully backed up to the external server or hard drive during the last 24 hours.

**Action Required**: Review the logs inside the rsync_logs folder to identify the specific transfer error, and verify your network connectivity or remote storage availability.
