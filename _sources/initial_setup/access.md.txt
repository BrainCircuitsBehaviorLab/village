## Remote Access Setup

Before configuring remote access, verify that your Raspberry Pi is connected to the internet. If you need assistance with network configuration, please refer to the official [Raspberry Pi Guide][HELP].

While any remote desktop client providing a full graphical user interface can be used, we recommend one of the two options below for seamless integration with the Training Village (TV) system.

---

### Option 1: Using AnyDesk

AnyDesk is highly reliable, easy to deploy, and its free tier is fully sufficient for lab operations.

#### From your Raspberry Pi 5:
1. Open the web browser on your Raspberry Pi, go to the AnyDesk download page, and download the **Raspberry Pi / Debian (64-bit / ARM64)** `.deb` package.
2. Install the downloaded package by double-clicking it or using the terminal.
3. Launch AnyDesk and write down the unique **AnyDesk Address** assigned to your device.
4. Navigate to *Settings → Access*, then look for **Unattended Access**. Check the option to enable it and set a secure password. This allows authorized lab members to connect remotely at any time without needing someone to manually accept the incoming request on the Pi.

#### From your external computer or smartphone:
1. Download and install AnyDesk on your external workstation, laptop, or mobile phone.
2. Launch the application, type the Raspberry Pi’s unique AnyDesk Address into the connection bar, and enter your preset unattended access password when prompted.

```{tip}
You can rename and save this connection to your favorites for quick access.
```

---

### Option 2: Using RealVNC

RealVNC is an excellent choice because the server software comes pre-installed by default on Raspberry Pi OS. You will need to create an account, but the free **Lite** tier is ideal for managing a standalone system.

#### From your Raspberry Pi 5:
1. Navigate to the [RealVNC Lite Access Subscription Page][LITE] and create a free account (eligible for non-commercial/research use). If you encounter any verification issues, follow these [detailed instructions][INSTRUCTIONS].
2. Open the **RealVNC Server** application on your Raspberry Pi (accessible via the desktop taskbar or the main application menu).
3. Sign in to the server window using your newly created credentials to link the Raspberry Pi to your team’s account.
4. Once linked, the RealVNC window will display a cloud connectivity code (allowing you to connect from outside the university/institution network) as well as a local IP address (for faster connections when your laptop is on the same local network).

#### From your external computer or smartphone:
1. Install and open **RealVNC Viewer** on your external computer, laptop, or smartphone.
2. Log in with your team's RealVNC credentials.
3. Select your Raspberry Pi directly from your team's cloud device list. Alternatively, if you are working on the same local network, you can connect instantly by typing the Raspberry Pi's local IP address directly into the search bar.

---


```{warning}
While [Raspberry Pi Connect][RASPI] is a popular built-in option for remote connections, it is **incompatible** with the Training Village system.
Our system explicitly runs on an **X11 display server** instead of Wayland (which is required by Raspberry Pi Connect). Forcing an X11 architecture is mandatory for our ecosystem because it provides superior, low-level frame rendering when utilizing a touchscreen to present visual stimuli in the experiments.
```

---

```{tip}
Once remote access is successfully configured, we highly recommend disconnecting the keyboard, mouse, and monitor, and completing the remaining setup steps remotely.
```

<br><br><br>

[HELP]: https://projects.raspberrypi.org/en/projects/raspberry-pi-using/3
[REAL]: https://www.realvnc.com/en/
[LITE]: https://www.realvnc.com/en/connect/plan/lite/
[INSTRUCTIONS]: https://help.realvnc.com/hc/en-us/articles/360029619052-Activating-a-RealVNC-Connect-Lite-subscription
[ANYDESK]: https://anydesk.com/en/downloads/raspberry-pi
[RASPI]: https://www.raspberrypi.com/software/connect/
