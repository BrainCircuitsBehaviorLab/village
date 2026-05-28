## Soundcard & Touchscreen Integration

### Soundcard Integration

The Training Village uses the **HiFiBerry DAC+ Pro** HAT for audio output. Connect it
directly on top of the Raspberry Pi or on top of the Main HAT if one is installed. Audio
playback from within tasks is handled by the Python `sounddevice` library, which accesses
the hardware through PortAudio → ALSA.

#### Why the DAC must be released from the system before use

When the DAC is set as the active audio output in the desktop environment, the operating
system holds exclusive access to the device, preventing the Training Village from using
it. Setting the profile to **Off** releases the device and makes it available for the
Training Village.


#### Configuration

1. Connect headphones or speakers to the DAC output.

2. Right-click the volume icon in the top system bar and select **Device Profiles**. The
   **RPi DAC Pro** entry should appear in the list. Select it and set the output profile
   to **Stereo Output**.

3. Play any audio to verify the DAC is working correctly.

4. Once confirmed, return to **Device Profiles**, select **RPi DAC Pro** again, and set
   the profile to **Off**. The operating system will no longer use the device, leaving it
   free for `sounddevice` to access directly.

5. Launch the Training Village and select your soundcard under
   `SETTINGS` → `SOUND SETTINGS`.

```{admonition} Note
:class: tip
This configuration step only needs to be done once. The "Off" profile selection persists
across reboots, so the DAC will remain available to the Training Village after the system
restarts.
```

#### Latency
Playing a sound has a measured latency of mean = 9.3ms and sd = 0.9 ms.

---

### Touchscreen Integration

If you plan to present visual stimuli or record touch responses, enable the screen under
`SETTINGS` → `SCREEN SETTINGS`.

#### Choosing the right screen technology

We recommend using an **infrared (IR) touch frame** rather than a capacitive touchscreen.
An IR frame works by projecting an invisible grid of IR beams across the display surface;
a touch event is registered whenever an object interrupts one of the beams. This means
the animal does not need to physically press the screen — proximity alone triggers a
response — which reduces aversion and improves task engagement for rodents.

The IR frame connects via USB and the display via the second micro-HDMI port on the
Raspberry Pi.

#### Dual-screen configuration

The system runs with two display outputs:

- **HDMI-1**: Primary display showing the Training Village GUI *(can be virtual —
  no physical monitor required)*.
- **HDMI-2**: Secondary display inside the operant box showing behavioral stimuli.

To configure this, you need to tell the system to treat both HDMI ports as active,
regardless of whether a physical monitor is connected to HDMI-1.

**Step 1 — Edit the boot configuration:**

```bash
sudo nano /boot/firmware/cmdline.txt
```

Replace:

```
vc4.force_hotplug=1 video=HDMI-A-1:1600x900@60D
```

With:

```
vc4.force_hotplug=3 video=HDMI-A-1:1600x900@60D video=HDMI-A-2:1280x720@60D
```

The `vc4.force_hotplug` flag controls which HDMI ports the system treats as connected:
`1` = HDMI-1 only, `2` = HDMI-2 only, `3` = both. The `video=HDMI-A-*` parameters set
the resolution for each port independently.

**Step 2 — Set the resolution in the desktop:**

Navigate to **Raspberry Pi menu → Preferences → Control Centre → Screens → HDMI-2**,
set the resolution to **1280×720** or lower, and apply.

#### Resolution and display latency
Keep the stimulus display at 1280×720 or below. Higher resolutions significantly
increase CPU load on the Raspberry Pi, which in turn increases stimulus presentation
latency.

The system operates at a **60 Hz refresh rate** (one frame every 16.6 ms). Because the
next frame is preloaded in the buffer while the current one is being displayed, the
latency from issuing a display command to the frame appearing on screen is typically
one full frame plus the remaining portion of the current frame. In practice, measured
latencies are **mean = 27.4 ms, SD = 7.5 ms**.
