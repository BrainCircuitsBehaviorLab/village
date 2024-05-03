## Install Package for Windows
1. Download the latest installer (.msi) from [here](https://github.com/dorssel/usbipd-win/releases/tag/v4.0.0).

## Install Packages for WSL2/Ubuntu
1. Sync time between WSL2 and Windows. This is required to avoid any SSL errors.
   ```
   sudo hwclock -s
   ```
2. Update packages and sources.
   ```
   sudo apt update
   ```
3. Install required packages as documented [here](https://github.com/dorssel/usbipd-win).
   ```
   sudo apt install linux-tools-generic hwdata
   sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20
   ```

## Attach the Device to WSL2
1. Connect a USB device to be forwarded to WSL2.
2. Ensure that WSL2 is up and running.
3. Get the busid of the device by running `usbipd list` in Windows PowerShell (admin).
4. Bind the device in Windows PowerShell (admin). This is required only once for a device.
   ```
   usbipd bind --busid=2-2
   ```
5. Attach the device to WSL2 in Windows PowerShell (admin). This is required every time the device reconnects.
   ```
   usbipd attach --wsl --busid=1-2
   ```
6. Now in WSL2, run `lsusb`. The device should show up.
   ```
   $ lsusb
   Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
   Bus 001 Device 003: ID 0483:374e STMicroelectronics STLINK-V3
   ```

## Setting Up Permissions for USB Debugging in WSL2
### Setup udev rules
1. Setup OpenOCD udev rules.
   ```
   curl -fsSL https://raw.githubusercontent.com/openocd-org/openocd/master/contrib/60-openocd.rules | sudo tee /etc/udev/rules.d/60-openocd.rules
   ```
2. Restart udev service.
   ```
   sudo service udev restart
   ```
3. Add user to `plugdev` group.
   ```
   sudo usermod -aG plugdev $USER
   ```
4. Verify whether the current user was added.
   ```
   groups `whoami`
   ```
5. Now reconnect the device and attach it to WSL2 as stated above.
6. Verify if rules are set.
   - Find device ID.
     ```
     $ lsusb
     Bus 001 Device 006: ID 0483:374e STMicroelectronics STLINK-V3
     Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
     ```
   - Check device permissions and user group. Use the syntax `ls -l /dev/bus/usb/<Bus>/<Device>`.
     ```
     $ ls -l /dev/bus/usb/001/006
     crw-rw-rw- 1 root plugdev 189, 5 Dec 27 14:14 /dev/bus/usb/001/006
     ```
7. Ensure that the device is accessible by `plugdev` group and also has read and write permissions.

## Now the device should be accessible by WSL2 applications.

## References
- [OpenOCD udev rules](https://github.com/arduino/OpenOCD/blob/master/contrib/60-openocd.rules)
- [PlatformIO udev rules](https://docs.platformio.org/en/stable/core/installation/udev-rules.html)
- [Embedded Trainings](https://embedded-trainings.ferrous-systems.com/installation#linux-only-usb)
