## Configure remote access

First, we need to set up the system’s internet connection. The easiest way to do this is to connect the Raspberry Pi to a keyboard, mouse, screen, and Ethernet cable (if you are using a wired connection) before powering it on for the first time. For performance reasons, the screen resolution is forcibly set to 1280x720, regardless of the display you use.

Once the operating system boots up, simply configure the internet connection. [Help][HELP].

Now we’ll set up remote access using [**RealVNC**][REAL]. Follow these steps:

From your Raspberry Pi:
1.	Go to the [**Lite Access Subscription Page**][LITE] of RealVNC and create an account (free for non-commercial use). Follow these [detailed instructions][INSTRUCTIONS] if you encounter any issues.
2.	Open the **RealVNC Server** on the Raspberry Pi (it is installed automatically with Raspberry Pi OS) and configure it for your team.
3.	Go to the **Device Access** section on the RealVNC webpage and add your current device.
4.	In the RealVNC window, you will see a code that allows remote connections from other networks and an IP address for connections from the same network.

From your external computer or phone:
1.	Log in to the RealVNC webpage with your credentials.
2.	Install and open **RealVNC Viewer** on your external computer or phone.
3.	Connect to the Raspberry Pi using the RealVNC server’s code if connecting from a different network, or the IP address if connecting from the same network.

There is also an alternative option for remote connection using **raspi-connect**; however, we currently do not recommend it due to some issues we encountered during testing, and suboptimal performance.

[HELP]: https://projects.raspberrypi.org/en/projects/raspberry-pi-using/3
[REAL]: https://www.realvnc.com/en/
[LITE]: https://www.realvnc.com/en/connect/plan/lite/
[INSTRUCTIONS]: https://help.realvnc.com/hc/en-us/articles/360029619052-Activating-a-RealVNC-Connect-Lite-subscription

<br>
