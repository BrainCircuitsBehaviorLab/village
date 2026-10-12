## Raspberry Pi Disk Image


Here you can download a disk image containing the operating system (Raspberry Pi OS Trixie, based on Debian 13) and the Training Village software pre-installed, including Python 3.13 and all required libraries, as well as the Raspberry Pi hardware configuration needed for the system to work properly.

### Requirements

- SD card of 32GB or larger (256 GB recommended)
- [Training Village Disk Image][LINK]
- [Raspberry Pi Imager][IMAGER]

### Steps

1. Download the [Training Village Disk Image][LINK]
2. Download the [Raspberry Pi Imager][IMAGER]
3. Open Raspberry Pi Imager
4. Select Raspberry Pi 5.
5. Click Choose OS → scroll down → Use custom image → select the downloaded file
6. Click Choose Storage → select your SD card
7. Click Write and wait for it to finish (Raspberry Pi Imager will verify the image automatically)
8. Insert the SD card into your Raspberry Pi and power it on.

```{admonition} Expand the partition
:class: warning
This is a custom image, cloned from an already-configured Raspberry Pi, so the
automatic first-boot partition expansion may not run again on your SD card. The
following steps expand the partition by hand, so the full capacity of your card
is available instead of being limited to the size of the card the image was
originally created on.
```

9. Open a terminal and run `sudo raspi-config`
10. Go to `Advanced Options` → `Expand Filesystem`
11. Reboot when prompted


[IMAGER]: https://www.raspberrypi.com/software/
[LINK]: https://drive.google.com/file/d/1_GPpJvMfvM43qBDeu-I1vmESrCpsJoe1/view?usp=sharing
