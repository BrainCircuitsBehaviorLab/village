## Speeding Up Bpod Communication (Custom Firmware)

By default, some Bpod (Teensy) firmware versions flush outgoing USB serial data with a
**5 ms** timeout. This only applies to Bpods built on a **Teensy 3.6** (state machine
hardware **r2.0 to r2.4**). Older models (Bpod 0.5 – 1.0) and newer Teensy 4.x boards
(Bpod 2.5 / 2+) are not affected by this issue.

Lowering the timeout to **1 ms** noticeably reduces Bpod Softcode communication latency
(see the [Timing, Clocks & Latencies][TIMING] section). This Raspberry Pi already has
the fix applied — flashing the sketch below already produces a 1 ms Bpod, no extra
edits needed. See the note at the end of this guide for where the fix actually lives.

### 1. Open the firmware sketch

On the Raspberry Pi, open the stock Bpod 2.0 (v23) sketch — unmodified, straight from
Sanworks' GitHub — using the Arduino IDE 1.8 already installed on the Pi:

```
/home/pi/Bpod_StateMachine_Firmware-23/Preconfigured/v23/StateMachine-Bpod2_0/StateMachine-Bpod2_0.ino
```

Teensy board support is also already installed on the Pi
(<https://www.pjrc.com/teensy/td_download.html>).

### 2. Select the board, USB type, and port

From the **Tools** menu:

- **Board** → Teensy 3.6
- **USB Type** → Dual Serial
- **Port** → the Bpod's serial port (on Linux it looks like `/dev/ttySX`; if you're not
  sure which one it is, unplug the Bpod and see which entry disappears)

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

Stock Teensy cores ship with:

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
