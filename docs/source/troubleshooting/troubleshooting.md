## General Troubleshooting Guide

### Camera Issues (Connection Error or Malfunctioning)

1. **Verify Physical Connections:** Ensure both camera ribbon cables are firmly seated in the Raspberry Pi 5 MIPI CSI slots and that the locking clips are engaged.
2. **Check Camera Indices:** Open the application GUI, navigate to `SETTINGS` → `CAMERA SETTINGS`, and verify that your camera indices are properly assigned (typically one is `0` and the other is `1`).
   * `CAM_CORRIDOR_INDEX`: `0` or `1`
   * `CAM_BOX_INDEX`: `0` or `1`
3. **Reboot:** If you swapped indices or re-seated the cables, restart the system to allow the OS to re-initialize the video devices.

---

### Controller Issues (Bpod or Arduino Connection Error)

1. **Verify Physical Port:** Ensure your behavioral controller is plugged into the **bottom USB 3.0 port** (the blue port closest to the Raspberry Pi’s onboard Ethernet connector).
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
| **`IR_LIGHT_CORRIDOR_INDEX`**| `7` | Pin channel for Infrared LED arrays |
| **`SCALE_ADDRESS`** | `0x48` | Onboard scale/load cell amplifier address |
| **`TEMP_SENSOR_ADDRESS`** | `0x44` | Ambient temperature sensor address |
| **`CHIP_BOX_ADDRESS`** | `0x6a` | Main I2C chip address on the Box Board |
| **`MOTOR1_BOX_INDEX`** | `4` | Pin channel for Box Module Servo 1 |
| **`MOTOR2_BOX_INDEX`** | `5` | Pin channel for Box Module Servo 2 |
| **`VISIBLE_LIGHT_BOX_INDEX`** | `6` | Pin channel for Box Visible light |
| **`IR_LIGHT_BOX_INDEX`** | `7` | Pin channel for Box IR light |
