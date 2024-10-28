## Software Installation

You can download a ready-to-use ISO image containing the operating system (Raspberry Pi OS) along with all necessary libraries and Python code pre-installed [here][ISO].

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
2. Connect the Ethernet cable if you are going to use an Ethernet connection.
3. If your SD card has the OS preinstalled, jump to step 4.
4. If your SD card is empty, follow these instructions to download the OS and copy it to the SD: [Raspberry Pi OS][Pi OS]
5. Insert the SD card and start the Raspberry Pi.
6. Select your country and keyboard language and choose English as the general language.
7. Type `raspberry` as the username and choose the password you want.
8. Select your Wi-Fi or Ethernet connection.
9. Choose your preferred web browser (Chromium).
10. Select "Yes" when asked to update software (if you have your internet connection ready).


### Updating the System

1. Make sure you have internet connection and then update the software. [Detailed instructions][UPDATE].

```
sudo apt update
sudo apt full-upgrade
```


### Installing Needed Libraries
1. Install OpenCV (library to manage video):

```
sudo apt install -y python3-opencv
sudo apt install -y opencv-data
```

2. Install sound libraries: TODO check if pulseaudio is really needed.

```
sudo apt-get install pulseaudio
sudo apt-get install libportaudio2
```

3. Install PyQT5 multimedia

```
sudo apt install python3-pyqt5.qtmultimedia
sudo apt install libqt5multimedia5-plugins
```

4. Install VS Code (optional):

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

3. Install needed libraries with pip:

```
pip install python-dateutil
pip install setuptools_scm
pip install sounddevice
pip install python-telegram-bot
pip install scipy
```

### Changing Preferences
1. Enable auto-login by clicking on **Preferences** -> **Raspberry Pi Configuration** -> **Auto login**.
2. Add CPU monitors to the toolbar: Right-click on the toolbar, select **Add/Remove Panel Items**, and click **Add**. Select **CPU Temperature Monitor** and **CPU Usage monitor**.

### Screen Settings
1. Run the raspi-config.

```
sudo raspi-config
```
2. Go to **Display Options** and disable blanking.
3. Go to **Advanced Options** and select X11 (instead of Wayland).

Then, you need to configure the system to recognize a screen even if none is physically connected, so the software renders properly when accessed remotely. If you want to use an additional screen to present stimuli in the behavioral box, you need to set the system to work with two screens.

4. Modify the file: `/boot/firmware/cmdline.txt`

```
sudo nano /boot/firmware/cmdline.txt
```
5. Add the following text: `vc4.fvc4.force_hotplug=1` if you are using only one screen,
 or `vc4.fvc4.force_hotplug=3` if you are using two screens.

Explanation of values: (1 makes the system operate as if a screen is connected to HDMI 1). (2 makes the system operate as if a screen is connected to HDMI 2). (3 makes the system operate as if screens are connected to both HDMI 1 and HDMI 2).

6. Change the resolution of the screen (or screens) to 1280 x 720: **Preferences** ->
 **Screen Configuration**.


### I2C Communication

The temperature sensor and the weight sensor are connected to the I2C pins of the Raspberry.
1. First, activate the I2C communication:

```
sudo raspi-config
```
2. Go to **Interface Options** and enable I2C.

The system is configured to work with address = 0x45 for the temperature sensor (DFRobot HX711) and address = 0x64 for the weight sensor (CQRobot SHT31). If you are using different models or if the devices are not recognized, follow these steps to verify that the addresses are correct:

3. Connect the devices to the raspberry.
4. Install the detection tools:
```
sudo apt-get install -y i2c-tools
```
5. Run the tools:
```
i2cdetect -y 1
```
6. Change the addresses in the python code by modifying the corresponding settings in
`village/settings.py` (extra_settings).


### Accessing Pins via Hardware (for Servos) and Using UART Pin for Communication

To access the pins via hardware (faster and less jittery than software access), and to allow the use of the UART Pin for communication with the sensors you need to change two settings:

1. Edit the `/boot/firmware/config.txt` file to include the following:


```
[all]
dtoverlay=pwm-2chan,pin=12,pin2=13,func=4,func2=4
enable_uart=1
```



### Udev Rules for Consistent USB Device Naming

When you connect your Bpod device to the Raspberry Pi, it’s assigned a file path in `/dev/`, typically named `ttyACM0`. However, this name may vary (ttyACM1, ttyACM2, etc.), especially if you have other USB devices connected. To ensure a consistent and recognizable name, you can create a symbolic link to your Bpod device.

1. Navigate to the Udev rules folder where custom rules are stored:
```bash
cd /etc/udev/rules.d
```
2. Create a new rule file named `99-usb.rules`:
```bash
sudo nano 99-usb.rules
```
3. In the new rule file, add the following line to create a symbolic link named `Bpod` for any device that matches the pattern `ttyACM*`. This will allow any device named ttyACM* (where * can be any number) to be consistently linked, provided it’s connected
to a specific USB port (in this case, the port associated with `KERNELS==3-1:1.0`).

```
KERNEL=="ttyACM*",KERNELS=="3-1:1.0",SYMLINK+="Bpod"
```

Note: The USB port identifier (KERNELS=="3-1:1.0") may vary depending on the physical USB port you are using. For reference, the 3-1:1.0 port on the Raspberry Pi is usually the USB port next to the Ethernet connection. To confirm the exact port identifier, you can use the command `dmesg` after connecting the device.

4. Activate the new rule by triggering the Udev process:

```
sudo udevadm trigger
```
Now, whenever the Bpod device is connected to the specified USB port, it will consistently appear with the symbolic link `/dev/Bpod`, regardless of its dynamic ttyACM* designation.


### Install village

1. Make sure you are in .env environment (see above)
2. Clone the repo inside your `/home/raspberry/` directory. In the terminal, type: `git clone https://github.com/BrainCircuitsBehaviorLab/village.git`
3. Navigate to folder `village` and type `pip install -e .`
4. You’re ready to start the system by simply running the `main.py` file. Just execute: `python /home/raspberry/village/village/main.py`





[Pi OS]: https://www.raspberrypi.com/software/
[ISO]: /TODO-LINK.md
[UPDATE]: https://www.raspberrypi.com/documentation/computers/os.html
