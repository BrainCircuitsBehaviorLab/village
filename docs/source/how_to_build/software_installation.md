# Software Installation

You can download a working ISO image containing the operating system (Raspberry Pi OS) and a pre-installed version of all the necessary libraries and Python code here (link).
Follow the instructions in this page in case you prefer to install everything manually.

## What you need

- Raspberry Pi 5 - 8GB
- Fan
- Micro SD 128GB
- Keyboard
- Mouse
- Screen
- Micro HDMI to HDMI cable
- Power supply for Raspberry Pi
- Ethernet cable (optional)

## Launch Raspberry Pi OS for the first time

1. Connect a keyboard, mouse, and screen to the Raspberry Pi.
2. Connect the Ethernet cable if you are going to use an Ethernet connection.
3. If your SD card has the OS preinstalled, jump to step 4.
4. If your SD card is empty, follow these instructions to download the OS and copy it to the SD: [Raspberry Pi Software](https://www.raspberrypi.com/software/)
5. Insert the SD card and start the Raspberry Pi.
6. Select your country and keyboard language and choose English as the general language.
7. Select the user (pi) and password (you know it).
8. Select your Wi-Fi or Ethernet connection.
9. Choose your preferred web browser (Chromium).
10. Select "Yes" when asked to update software (if you have your internet connection ready).

## Sound settings

- `sudo apt-get install pulseaudio`  I think this one is not necessary
- `sudo apt-get install libportaudio2`

## Screen settings and I2C communication

- `sudo raspi-config`
  - Go to **Display Options** and disable blanking.

  Optional if you have a touch screen: IS THIS TRUE?
  - Go to **Advanced Options** and select X11 (instead of Wayland).

  - Go to **Interface Options** and enable I2C.

  Modifying options in raspi-config usually is the same that modifying or adding lines to **/boot/firmware/config.txt**

### If you are using one screen only

- `sudo nano /boot/firmware/cmdline.txt`
  - Add the text: `vc4.fvc4.force_hotplug=1`

### If you are using 2 screens

- `sudo nano /boot/firmware/cmdline.txt`
  - Add the text: `vc4.fvc4.force_hotplug=3` (1 for using the first HDMI, 2 for using the second one, and 3 to use both of them).

## Updating the system and installing software

Update software, instructions from [here](https://www.raspberrypi.com/documentation/computers/os.html):

```bash
sudo apt update
sudo apt full-upgrade
```

Install OpenCV (library to manage video):

```bash
sudo apt install -y python3-opencv
sudo apt install -y opencv-data
```

Install VS Code (optional):

```bash
sudo apt install code
```

- Enable auto-login by clicking on **Preferences** -> **Raspberry Pi Configuration** -> **Auto login**.
- Add CPU monitors to the toolbar: Right-click on the toolbar, select **Add/Remove Panel Items**, and click **Add**. Select **CPU Temperature Monitor** and **CPU Usage monitor**.
- Change the resolution of the screen (or screens) to 1280 x 720: **Preferences** -> **Screen Configuration**.

## PyQT5 multimedia

```bash
sudo apt install python3-pyqt5.qtmultimedia
sudo apt install libqt5multimedia5-plugins
```

## Setting .env environment

Create a .env environment with all the packages installed in the general Python:

```bash
python -m venv --system-site-packages ~/.env
```

Activate it:

```bash
source ~/.env/bin/activate
```

Install needed libraries with pip:

```bash
pip install python-dateutil
pip install setuptools_scm
pip install sounddevice
pip install python-telegram-bot
pip install scipy
```

## Accessing the pins by hardware (for servos) and using pin uart to communicate

We need to change an option to be able to access the pins by hardware (faster and less jittery than accessing them by software):

modify the **/boot/firmware/config.txt** file to include

```
[all]
dtoverlay=pwm-2chan,pin=12,pin2=13,func=4,func2=4
enable_uart=1
```

## Configure remote access

### Option 1: with RealVNC

From your Raspberry Pi:

1. Go to the website and create an account: [RealVNC](https://www.realvnc.com/es/)
2. Subscribe to Lite access (free access): [Lite Access](https://www.realvnc.com/es/connect/plan/lite/). Follow instructions [here](https://help.realvnc.com/hc/en-us/articles/360029619052-Activating-a-RealVNC-Connect-Lite-subscription) if you go around in a loop.
3. Open the RealVNC server on the Raspberry Pi (it is automatically installed when you install Raspberry Pi OS) and configure it for your team.
4. Go to **Device Access** on the RealVNC webpage and add your current device.
5. Back in the RealVNC window, you should see a code that allows remote connections from other networks and an IP number that allows connection from the same network.

From your external computer or phone:

1. Log in to the RealVNC webpage using your credentials.
2. Install and open RealVNC Viewer on your external computer or phone.
3. Connect to the Raspberry Pi using the RealVNC server's code if you are connecting from another network or the IP if you are connecting from the same network.

### Option 2 (things are very slow with this): with raspi-connect

1. Follow these instructions:
<https://www.raspberrypi.com/news/raspberry-pi-connect/>

## Udev rules

Go to the rules folder:

```bash
cd /etc/udev/rules.d
```

Create a new rule file named `99-usb.rules`:

```bash
sudo nano 99-usb.rules
```

Add the following line to create a symbolic link to the bpod, changing "1-1:1.0" with the real port. You can use `dmesg` to check the ports:

```
KERNEL=="ttyACM*",KERNELS=="1-1:1.0",SYMLINK+="Bpod"
```

```
sudo udevadm trigger
```

## I2C

- We connect the temperature sensor and the scale to the I2C pins
- We need to know the address of each of the sensors
- For the temperature sensor is 0x45 (DFRobot HX711)
- For the weight sensor is 0x64 (CQRobot SHT31)
- The addresses can change to discover them:
- 1 - connect the devices to the raspberry
- 2 - install the tools for detection:
`sudo apt-get install -y i2c-tools`
- 3 - run the tools:
`i2cdetect -y 1`

## Create a telegram bot

- Text **@BotFather** in the search tab and select this bot.
- Text: **/newbot** and send.
- Follow Botfather instructions. Write down the token. Never share the token in github.
- Open a chat with your new bot and activate it by sending: **/start**.

### Check the token of an existing bot

- Go to the **@BotFather** chat and send **/token**.

### Make the bot triggers the alarms

- Create a chat with the bot and other participants (the bot must be admin: go to the group → edit → administrators). All the participants of this group will receive the alarms from the bot and will be able to send commands to it.
- Start a conversation with **@username_to_id_bot** to obtain your ID, the chat ID and the ID of all the other users.
- Copy the token, the chat ID and the allowed users IDs in academy settings (TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM USERS)

## Install village

- Make sure you are in .env environment (see above)
- Clone the repo anywhere you want. In the terminal, type:
```git clone https://github.com/BrainCircuitsBehaviorLab/village.git```
- Navigate to folder ```village``` and type ```pip install -e .```

PUT THIS IN USAGE.MD OR SOMETHING LIKE THAT

- Run the ```main.py``` file: ```python village/main.py```

Feel free to adjust the formatting or content as needed!
