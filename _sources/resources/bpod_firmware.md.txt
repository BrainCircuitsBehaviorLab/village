## Custom Bpod Firmware

This guide is only needed if the default Bpod communication latency (see
[Timing, Clocks & Latencies][TIMING]) is not good enough for your experiment — most
setups can safely skip it.

By default, some Bpod firmware versions flush outgoing USB serial data with a **5 ms** timeout, introducing up to 5 ms of communication latency. This only applies to Bpod state machines built on the **Teensy 3.6** (hardware versions **Bpod 2.0 to 2.4**).
* Older models (Bpod 0.5–1.0): Do not use Teensy microcontrollers.
* Newer models (Bpod 2.5 / 2+): Use the Teensy 4.x platform and are not affected by this issue.

Lowering the timeout to **1 ms** noticeably reduces Bpod Softcode communication latency
(see the [Timing, Clocks & Latencies][TIMING] section). On this Raspberry Pi, the
one-line edit the fix requires has already been made to the Teensy core library (see
the note at the end of this guide) — you still need to follow the steps below to build
and upload the firmware so the fix actually reaches your Bpod.

### 1. Open the firmware sketch

On the Raspberry Pi, you will find a local copy of the original Bpod 2.0 (v23) firmware (unmodified from Sanworks' GitHub). Open it using the pre-installed Arduino IDE 1.8:

```
/home/pi/Bpod_StateMachine_Firmware-23/Preconfigured/v23/StateMachine-Bpod2_0/StateMachine-Bpod2_0.ino
```

Teensy board support is also already installed on the Pi
(<https://www.pjrc.com/teensy/td_download.html>).

### 2. Select the board, USB type, and port

From the **Tools** menu:

- **Board** → Teensy 3.6
- **USB Type** → Dual Serial
- **Port** → the Bpod's serial port (on Linux this typically appears as /dev/ttyACM0 or /dev/ttyACM1; if you are unsure, unplug the USB cable and check which port disappears).

### 3. Upload

Click the upload button (the right-pointing arrow). A successful upload prints "Done
uploading" with a "Verify successful" message in the output window.

````{admonition} Where the speed fix actually lives
:class: note
The [firmware sketch][FW_REPO] itself is untouched — the fix is a one-line edit to the
Teensy core library, not the sketch:

```
~/arduino-1.8.19/hardware/teensy/avr/cores/teensy3/usb_serial.c
```

Default Teensy core installations ship with:

```c
#define TRANSMIT_FLUSH_TIMEOUT  5  /* in milliseconds */
```

On this Raspberry Pi, that line has already been changed to:

```c
#define TRANSMIT_FLUSH_TIMEOUT  1  /* in milliseconds */
```

````

[TIMING]: /system_operation/timing.md
[FW_REPO]: https://github.com/sanworks/Bpod_StateMachine_Firmware
