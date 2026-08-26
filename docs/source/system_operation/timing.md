## Timing, Clocks & Latencies

### Absolute Time (Unix Epoch)

All timestamps across the platform use standard **Unix Epoch Time** — a floating-point
value representing the total seconds elapsed since January 1, 1970, 00:00:00 UTC:

$$\text{Timestamp} = 1748300000.123 \longrightarrow \text{Precise calendar moment in time}$$


### Raspberry Pi Monotonic Clock (`time_utils`)

On the Raspberry Pi, all timestamps must use the synchronized **monotonic clock**
exposed through `time_utils`:

- `time_utils.now_timestamp()` — returns a `float` Unix epoch timestamp (replaces `time.time()`).
- `time_utils.now()` — returns a `datetime.datetime` object (replaces `datetime.now()`).


```{admonition} Important:
:class: warning
Do not use `time.time()` or `datetime.now()`. Always use `time_utils.now_timestamp()` and `time_utils.now()`.
```

```{admonition} What is a monotonic clock?
:class: tip
Unlike the system wall clock, a monotonic clock guarantees that time always advances steadily and never jumps forward or steps backward. Wall clocks are prone to sudden time shifts caused by:
Network Time Protocol (NTP): Automated network syncs that correct internal clock drift.
Daylight Saving Time (DST) & timezone changes: Seasonal or location-based hour shifts.
Leap seconds: Occasional single-second adjustments to match Earth's astronomical rotation.
Manual modifications: Manual date/time changes made by a user or system script.
By avoiding these external adjustments, a monotonic clock ensures that event ordering and elapsed-time calculations remain strictly consistent throughout a session.
Any necessary resynchronization with the wall clock only occurs between sessions during the SYNC state. For implementation details, see `village/scripts/time_utils.py`.
```

### Hardware Synchronization

Depending on your setup, hardware timing is managed through one of two pathways.

#### 1. Raspberry Pi only (native execution)

Timestamps are derived from the Raspberry Pi master clock via
`time_utils.now_timestamp()` (see [Raspberry Pi Monotonic Clock](#raspberry-pi-monotonic-clock-time-utils)
above), which tracks the Linux system clock and is resynchronized only between
sessions.

#### 2. Controller-integrated setups (Bpod or Arduino)

External microcontrollers maintain independent internal hardware timers. To align these with the
Raspberry Pi master clock, a synchronization handshake is performed at the start of
every single trial:

1. **Trial Start Handshake**: When `register_start_trial` is executed at trial onset, both clocks are read at the exact same moment:
   - `raspberry_timestamp`: master Unix timestamp on the Raspberry Pi.
   - `controller_timestamp`: microcontroller hardware timer (reset to 0.0).
2. **Offset Calculation**: A constant offset is established for that specific trial:
   ```
   offset = raspberry_timestamp - controller_timestamp
   ```
3. **Data Logging**: All subsequent hardware events arriving during that trial are mapped to master Unix time:
   ```
   timestamp_absolute = controller_timestamp + offset
   ```

This approach preserves the sub-millisecond precision of the external hardware
controller while writing all data in master Unix Epoch time.


```{admonition} Precision Limits & Clock Drift:
:class: warning
This mechanism assumes the clock offset remains constant within the duration of a trial. However, physical hardware oscillators run at slightly different speeds, causing a small drift of roughly **~1 ms per minute** between the microcontroller and the Raspberry Pi.

- **Short trials (< 1–2 minutes):** drift is negligible (< 2ms) and can be safely ignored for
  standard behavioral analysis.
- **Long trials:** in paradigms with very long trials, it is advisable to handle
  timestamps that depend on the controller separately from those derived solely from
  the Raspberry Pi clock. Because clocks are only synchronized once at the beginning of the trial, a drift of ~1 ms per minute accumulates continuously. By minute 15, events logged directly by the Raspberry Pi (e.g., camera frames or host logs) and events logged via the microcontroller (e.g., licks or valve triggers) may have a ~15 ms discrepancy relative to each other.
  ```

---

### Latency Reference

This section describes the latency of each component in the system. The total latency
of any event is the sum of three terms:

```
total latency = trigger latency + communication latency + action latency
```

#### Triggers

**Controller trigger (Bpod / Arduino)**
Port pokes, photogate detections, and state-machine transitions handled entirely within
the microcontroller complete in **microseconds** — effectively instantaneous.

**Touchscreen trigger**
The touchscreen communicates with the Raspberry Pi over USB using the HID protocol.
When a physical touch occurs, the touchscreen controller samples the contact,
packages it as a HID input report, and transmits it over USB. The USB host controller
polls HID devices at a fixed interval — typically every 8 ms (125 Hz polling rate) —
so the report can wait up to one full polling interval before being read. The Linux
kernel then delivers the event through the `evdev` subsystem, which adds negligible
overhead. The dominant source of latency is therefore the USB polling interval itself,
which explains the measured **mean = 4.1 ms, SD = 2.4 ms**.

**Camera trigger**
When a frame is captured by the camera sensor, it passes through the internal
picamera2 pipeline before being handed to the callback, where the detection algorithm runs. The total camera trigger latency is **mean = 22.3 ms, SD = 6.3 ms**.

#### Communication

If both the trigger and the resulting action execute on the same device, communication
cost is zero. When a trigger on one device causes an action on the other, the serial
link introduces additional latency:

- **Bpod Softcode** (USB serial, 1–255 numeric value): **mean = 1.2 ms, SD = 0.3 ms**.
- **Arduino serial message** (USB serial, 1 byte): **mean = 1.2 ms, SD = 0.3 ms**.


```{admonition} Latency Warning for Bpod 2.0 to 2.4 (Teensy 3.6 Hardware)
:class: warning
**Affected models:** This only applies to Bpods built on a **Teensy 3.6** (state machine hardware **r2.0 to r2.4**). Older models (Bpod 0.5 – 1.0) and newer Teensy 4.x boards (Bpod 2.5 / 2+) are not affected.

**The issue:** By default, unmodified firmware on these versions flushes outgoing USB serial data with a **5 ms** timeout. This adds **4 ms of latency to every single Bpod->Raspberry Pi communication** compared to the 1 ms performance benchmark shown above.

**The fix:** To reduce this timeout to **1 ms**, you need to edit a Teensy 3.x USB driver file and flash the modified firmware. Follow the step-by-step guide in [Speeding Up Bpod Communication][BPOD_FW].
```

#### Actions

**Port LEDs or water delivery (controller)**
Effectively instantaneous — **microseconds**.

**LED strip or matrix (Raspberry Pi)**
`update_strip()` always sends the entire pixel buffer to the strip's controller chip
over SPI, regardless of how many LEDs actually changed, so its latency scales with
strip length at roughly 0.04 ms per LED at the default `SPI_SPEED_KHZ` = 800.
For a 144-LED strip or matrix: **mean = 5.8 ms, SD = 0.2 ms**.

**Sound playback (Raspberry Pi DAC Pro)**
The slow part — decoding and staging the audio — happens in `load()`, ahead of time.
`play()` itself is fast, since it just wakes the primed PCM: measured at the default
`SAMPLERATE` (96 kHz), **mean = 3.2 ms, SD = 0.6 ms**.

**Image display on screen**
The stimulus display operates at **60 Hz** (one frame every 16.6 ms) at a resolution
of 1280×720 or below. Higher resolutions significantly increase CPU load on the
Raspberry Pi, leading to greater stimulus presentation latency. Because the next frame
is preloaded in the buffer while the current one is displayed, the latency from issuing
a display command to the frame appearing on screen spans approximately one full frame
plus the remaining portion of the current frame: **mean = 24.9 ms, SD = 7.5 ms**.


```{admonition} CPU Load and Latency:
:class: tip
Communication and action latencies are both sensitive to CPU load. The platform
implements several measures to keep CPU usage low during sessions:

- Expensive background processes are suspended during sessions (e.g. the Python
  garbage collector, system update checks) and re-enabled when the system returns to
  the `WAIT` state.
- Cameras are configured at 640×480 / 30 fps (operant box) and 10 fps (corridor)
  by default. If these values are increased, latencies should be re-measured
  experimentally to confirm they remain within acceptable bounds.
- Unused features can be disabled to reduce CPU load. For example, if position
  tracking is not required to trigger events, it can be turned off during sessions and
  performed offline afterwards.
  ```

#### Summary Table

End-to-end latencies (mean ± SD, in ms) measured experimentally for each combination
of trigger and action. Each value is the sum of the three latency factors described
above:
```
total latency = trigger latency + communication latency + action latency
```


| Trigger | Port LED / water | LED strip / matrix (144 LEDs) | Sound | Screen |
|---|---|---|---|---|
| Controller | 0 ± 0 | 7.0 ± 0.4 | 4.4 ± 0.9 | 26.1 ± 7.5 |
| Touchscreen | 5.3 ± 2.4 | 9.9 ± 2.4 | 7.3 ± 2.6 | 29.0 ± 7.9 |
| Camera | 23.5 ± 6.3 | 28.1 ± 6.3 | 25.5 ± 6.4 | 47.2 ± 9.8 |

#### Summary Table (unmodified firmware, Bpod 2.0 to 2.4)

If you haven't applied the firmware fix, every Bpod->Raspberry Pi communication
costs an extra **~4 ms** (5 ms flush timeout instead of 1 ms). This only changes the
`Controller` row, since that's the only one where the Bpod is the trigger reporting the
event to the Raspberry Pi.

| Trigger | Port LED / water | LED strip / matrix (144 LEDs) | Sound | Screen |
|---|---|---|---|---|
| Controller | 0 ± 0 | 11.0 ± 0.4 | 8.4 ± 0.9 | 30.1 ± 7.5 |


```{admonition} Note on Latency Measurements:
:class: tip
All latency values reported here were obtained experimentally using an oscilloscope. Visual stimulus latencies were measured with a photodiode placed on the display, while auditory stimulus latencies were measured using a direct electrical connection to the audio signal. These measurements correspond to the default system configuration described above. Any modifications to camera settings, display resolution, or other relevant hardware or software parameters may affect latency and should therefore be validated with new measurements. For experiments requiring precise temporal control, we strongly recommend measuring latencies directly within the specific experimental setup rather than relying solely on the reference values provided here.
```

[BPOD_FW]: /resources/bpod_firmware.md
