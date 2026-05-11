## Manual Software Installation

You can download a ready-to-use disk image containing the operating system (Raspberry Pi OS) along with all necessary libraries and Python code pre-installed [here][IMAGE].

Follow the instructions on this page if you prefer a manual installation. The process can be challenging, so proceed only if you have a basic understanding of Linux distributions and are comfortable using the terminal.

### What You Need

- Raspberry Pi 5 - 8GB
- Fan
- Micro SD 128GB
- Keyboard
- Mouse
- Screen
- Micro HDMI to HDMI cable
- Power supply for Raspberry Pi
- 2 Raspberry Pi Camera Module 3 Wide Noir
- Ethernet cable (optional)
- Raspberry Pi Dac Pro (optional)
- 2 servo motors
- RFID sensor
- Weight sensor
- Temperature sensor

### Launch Raspberry Pi OS for the First Time

1. Connect a keyboard, mouse, and screen to the Raspberry Pi.
2. Connect the fan.
3. Connect the Ethernet cable if you are going to use an Ethernet connection.
4. If your SD card has the OS preinstalled, jump to step 4.
5. If your SD card is empty, follow these instructions to download the OS and copy it to the SD: [Raspberry Pi OS][OS]. Don't customize it, we will do it later.
6. Insert the SD card and start the Raspberry Pi.
7. Select your country and keyboard language and choose English as the general language.
8. Type `pi` as the username and choose the password you want.
9. Select your Wi-Fi or Ethernet connection.
10. Choose your preferred web browser (Chromium).
11. Select "Yes" when asked to update software (if you have your internet connection ready).

### Updating the System

1. Make sure you have internet connection and then update the software. [Detailed instructions][UPDATE].

```
sudo apt update
sudo apt full-upgrade
```

### Installing Needed Libraries
0. The OS comes with python 3.13 pre-installed.

1. Install OpenCV (the library used for video processing).

```
sudo apt install -y python3-opencv
sudo apt install -y opencv-data
```

2. Install sound library.

```
sudo apt-get install libportaudio2
```

3. Install PyQT5 multimedia

```
sudo apt install python-pyqt5
sudo apt install python3-pyqt5.qtmultimedia
sudo apt install libqt5multimedia5-plugins
```

4. Install VS Code:

```
sudo apt install code
```

### Creating a Python Environment and Installing pip Libraries

1. Create a `.env` environment that includes all the packages installed in the global
Python environment:

```
python -m venv --system-site-packages ~/.env
```

2. Activate it:

```
source ~/.env/bin/activate
```

3. Install the required libraries with pip.

```
pip install python-dateutil
pip install setuptools_scm
pip install sounddevice
pip install python-telegram-bot
pip install scipy
pip install gpiod
pip install fire
pip install pyserial
pip install pandas
pip install seaborn
pip install calplot
pip install PCA9685-smbus2
```

### Screen Settings

1. Run the `raspi-config`.

```
sudo raspi-config
```

2. Go to `Advanced Options` and select X11 (instead of Wayland).

Then, you need to configure the system to recognize a screen even if none is physically connected, so the software renders properly when accessed remotely. If you want to use an additional screen to present stimuli in the behavioral box, you need to set the system to work with two screens.

3. Modify the file: `/boot/firmware/cmdline.txt`

```
sudo nano /boot/firmware/cmdline.txt
```

4. Add the following text: `vc4.force_hotplug=1 video=HDMI-A-1:1600x900@60D` if you are using only one screen, or `vc4.force_hotplug=3 video=HDMI-A-1:1600x900@60D video=HDMI-A-2:1280x720@60D` if you are using two screens.

Explanation of values: (=1 makes the system operate as if a screen is connected to HDMI 1). (=2 makes the system operate as if a screen is connected to HDMI 2). (=3 makes the system operate as if screens are connected to both HDMI 1 and HDMI 2). HDMI-A-1 and HDMI-A-2 are used to specify the desired resolution.

5. After every reboot, the system will recognize two screens at the specified resolution. You can change the screen resolution (or resolutions) at any time in: `Preferences` ->
 `Screen Configuration`.

6. Reboot the system to use X11.


### Changing Preferences

1. Enable auto-login by clicking on `Preferences` -> `Control Centre` -> `System` -> `Auto login`.
2. Enable the following interfaces: SPI, I2C, Serial Port. The rest of the options should be disabled. By clicking on `Preferences` -> `Control Centre` -> `Interfaces` .
3. Set Screen Blanking OFF and On-screen keyboard DISABLED by clicking on `Preferences` -> `Control Centre` -> `Display`.
4. Add CPU monitors to the toolbar: Right-click on the toolbar, select `Add/Remove Panel Items`, and click `Add`. Select `CPU Temperature Monitor` and `CPU Usage monitor`.



### Accessing UART Pin for Communication

To allow the use of the UART Pin for communication with the sensors you need to edit the file `/boot/firmware/config.txt`:

1. Edit with ` sudo nano /boot/firmware/config.txt` to include the following:

```
[all]
enable_uart=1
```

### Udev Rules for Consistent USB Device Naming

When you connect your Bpod device to the Raspberry Pi, it’s assigned a file path in `/dev/`, typically named `ttyACM0`. However, this name may vary (ttyACM1, ttyACM2, etc.), especially if you have other USB devices connected. To ensure a consistent and recognizable name, you can create a symbolic link to your Bpod device.

1. Navigate to the Udev rules folder where custom rules are stored:

```
cd /etc/udev/rules.d
```

2. Create a new rule file named `99-usb.rules`:

```
sudo nano 99-usb.rules
```

3. In the new rule file, add the following line to create a symbolic link named `controller` for any device that matches the pattern `ttyACM*`. This will allow any device named ttyACM*(where* can be any number) to be consistently linked, provided it’s connected
to a specific USB port (in this case, the port associated with `KERNELS==3-1:1.0`).

```
KERNEL=="ttyACM*",KERNELS=="3-1:1.0",SYMLINK+="controller"
```

Note: The USB port identifier (KERNELS=="3-1:1.0") may vary depending on the physical USB port you are using. For reference, the 3-1:1.0 port on the Raspberry Pi is usually the USB port next to the Ethernet connection. To confirm the exact port identifier, you can use the command `dmesg` after connecting the device.

4. Activate the new rule by triggering the Udev process:

```
sudo udevadm trigger
```

Now, whenever the Bpod device is connected to the specified USB port, it will consistently appear with the symbolic link `/dev/Bpod`, regardless of its dynamic ttyACM* designation.

### Grant Permissions for Maximum Process Priority

To allow your Python script to run with the highest priority, you need to grant special permissions to the Python interpreter. Replace python3.13 with the actual Python version you are using if it’s different.
```
sudo setcap cap_sys_nice=eip /usr/bin/python3.13
```
This command gives Python permission to change its own scheduling priority without needing to run as root.

### Adjust Memory and Disk Cache Behavior

1. Open the system configuration file:
```
sudo nano /etc/sysctl.conf
```
2. Add the following lines at the end of the file, then save and exit:
```
vm.swappiness=10
vm.vfs_cache_pressure=50
```
These settings prioritize the use of RAM over disk cache whenever possible, in order to achieve better performance.

3. Apply the changes immediately (without rebooting):
```
sudo sysctl -p
```

### Optional: Increase SPI buffer size for LED strip

1. Modify the file: `/boot/firmware/cmdline.txt`

```
sudo nano /boot/firmware/cmdline.txt
```

2. Add the following text on the same line (e.g. after the vc4 edit done previously): ` spidev.bufsiz=32768`.


### Install Training Village

1. Make sure you are in .env environment.

```
source ~/.env/bin/activate
```

2. Go to your `/home/pi/` directory.

```
cd
```

3. Clone the repository.

```
git clone https://github.com/BrainCircuitsBehaviorLab/village.git
```

4. Navigate to folder `village`.

```
cd village
```

5. Install the repository.

```
pip install -e .
```

6. You’re ready to start the system by simply running the `main.py` file.

```
python /home/pi/village/village/main.py
```

### Create an Alias and Run the Training Village

1. Edit the .bashrc file:

```
nano ~/.bashrc
```

2. Add the following line to create an alias:

```
alias village='/home/pi/.env/bin/python /home/pi/village/village/main.py'
```

3. Reload the .bahsrc:

```
source ~/.bashrc
```

4. Run Training village:

```
village
```

[OS]: https://www.raspberrypi.com/software/
[IMAGE]: image.md
[UPDATE]: https://www.raspberrypi.com/documentation/computers/os.html

<br>
