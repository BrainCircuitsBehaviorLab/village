## Timing, Clocks & Latencies

### Absolute Time (Unix Epoch)

All timestamps across the platform use standard **Unix Epoch Time** — a floating-point
value representing the total seconds elapsed since January 1, 1970, 00:00:00 UTC:

$$\text{Timestamp} = 1748300000.123 \longrightarrow \text{Precise calendar moment in time}$$

This format is consistent across all Linux subsystems, making it straightforward to
subtract timestamps to compute durations or compare events across independent rigs.

### Raspberry Pi Monotonic Clock (`time_utils`)

On the Raspberry Pi, all timestamps are produced by calling a **monotonic clock**
exposed through `time_utils`:

- `time_utils.now_timestamp()` — returns a `float` Unix epoch timestamp (equivalent
  to `time.time()`, but backed by `time_utils`' monotonic clock).
- `time_utils.now()` — returns a `datetime.datetime` object (equivalent to
  `datetime.now()`, but backed by `time_utils`' monotonic clock).

**What is a monotonic clock?** Unlike the wall clock, `time.monotonic()` always
advances at a steady rate and can never jump backwards or be adjusted by NTP
corrections, manual clock changes, or DST transitions. This guarantees that
elapsed-time measurements and event ordering *within a session* remain consistent,
even if the system's wall clock is corrected while the session is running.

`village/scripts/time_utils.py` keeps two reference values, captured at the same
instant:

- `_base_wall`: a `datetime.now()` snapshot (wall-clock time).
- `_base_mono_ns`: the corresponding `time.monotonic_ns()` value.

Every call to `time_utils.now()` returns `_base_wall` advanced by however much the
monotonic clock has progressed since that snapshot:

```
now() = _base_wall + (time.monotonic_ns() - _base_mono_ns)
```

**Resynchronization:** `time_utils.sync()` re-captures `_base_wall` and
`_base_mono_ns` from the current wall clock. It is called automatically by the main
loop in the `SYNC` state, which runs between sessions (after a session ends and before
the next one can start). Any wall-clock drift or correction is therefore absorbed
between sessions and never occurs in the middle of one.

**Usage in custom tasks:** when writing task scripts that record timestamps to be
compared with the rest of the platform's data, do not call `time.time()` or
`datetime.now()` directly. Use instead:

- `time_utils.now_timestamp()` — returns a `float` Unix epoch timestamp.
- `time_utils.now()` — returns a `datetime.datetime`.

This keeps your timestamps in the same clock domain as the rest of the recorded data,
avoiding small inconsistencies caused by wall-clock corrections.

### Hardware Synchronization

Depending on your setup, hardware timing is managed through one of two pathways.

#### 1. Raspberry Pi only (native execution)

Timestamps are derived from the Raspberry Pi master clock via
`time_utils.now_timestamp()` (see [Raspberry Pi Monotonic Clock](#raspberry-pi-monotonic-clock-time-utils)
above), which tracks the Linux system clock and is resynchronized only between
sessions.

#### 2. Controller-integrated setups (Bpod or Arduino)

Microcontrollers maintain independent internal hardware timers. To align these with the
Raspberry Pi master clock, a synchronization handshake is performed at the start of
every trial:

1. When `register_start_trial` is called, two clock values are captured simultaneously.
   Bpod calls this function automatically when launching a trial state machine; for
   other controllers it must be called explicitly from the task at trial onset.
   - `raspberry_timestamp`: current Unix epoch time on the master clock.
   - `controller_timestamp`: reset to `0.0` as the microcontroller begins the trial
     loop.
2. A constant offset is computed:
   ```
   offset = raspberry_timestamp - controller_timestamp
   ```
3. As serial data packets arrive from the microcontroller, their hardware timestamps
   are converted to absolute Unix time before being written to disk:
   ```
   timestamp_absolute = controller_timestamp + offset
   ```

This approach preserves the sub-millisecond precision of the external hardware
controller while writing all data in master Unix Epoch time.

### Precision Limits & Clock Drift

This synchronization model assumes the computed offset remains stable throughout a
trial. In practice, physical oscillator variations can cause minor clock drift of up to
**~1 ms per minute** relative to the Raspberry Pi.

- **Short trials (< 1–2 minutes):** drift is negligible and can be safely ignored for
  standard behavioral analysis.
- **Long trials:** in paradigms with very long trials, it is advisable to handle
  timestamps that depend on the controller separately from those derived solely from
  the Raspberry Pi clock. For example, in a 15-minute trial, cumulative drift can
  introduce up to **15 ms of offset** by the end of a single trial.

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

- **Bpod Softcode** (USB serial, 1–255 numeric value): **mean = 2.5 ms, SD = 0.3 ms**.
- **Arduino serial message** (USB serial, 1 byte): **mean = 2.5 ms, SD = 0.3 ms**.

#### Actions

**Port LEDs or water delivery (controller)**
Effectively instantaneous — **microseconds**.

**LED strip or matrix (Raspberry Pi)**
`update_strip()` always sends the entire pixel buffer to the strip's controller chip
over SPI, regardless of how many LEDs actually changed, so its latency scales with
strip length at roughly 0.04 ms per LED at the default `SPI_SPEED_KHZ` = 800.
For a 144-LED strip or matrix: **mean = 5.8 ms, SD = 0.2 ms**.

**Sound playback (Raspberry Pi DAC Pro)**
The DAC Pro operates at 192 kHz with a buffer of 1024 samples (5.33 ms). Audio output
begins at the start of the next buffer fill cycle, so playback latency depends on how
much of the current buffer has already been consumed at the moment the play command is
issued: **mean = 5.5 ms, SD = 0.9 ms**.

**Image display on screen**
The stimulus display operates at **60 Hz** (one frame every 16.6 ms) at a resolution
of 1280×720 or below. Higher resolutions significantly increase CPU load on the
Raspberry Pi, leading to greater stimulus presentation latency. Because the next frame
is preloaded in the buffer while the current one is displayed, the latency from issuing
a display command to the frame appearing on screen spans approximately one full frame
plus the remaining portion of the current frame: **mean = 24.9 ms, SD = 7.5 ms**.

#### CPU Load and Latency

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

#### Summary Table

End-to-end latencies (mean ± SD, in ms) measured experimentally for each combination
of trigger and action. Communication cost is included where applicable (controller ↔
Raspberry Pi serial link: 2.5 ms mean; same-device triggers: 0 ms).

| Trigger | Port LED / water | LED strip / matrix (144 LEDs) | Sound | Screen |
|---|---|---|---|---|
| Controller | 0 ± 0 | 8.3 ± 0.4 | 8.0 ± 0.9 | 27.4 ± 7.5 |
| Touchscreen | 6.6 ± 2.4 | 9.9 ± 2.4 | 9.6 ± 2.6 | 29.0 ± 7.9 |
| Camera | 24.8 ± 6.3 | 28.1 ± 6.3 | 27.8 ± 6.4 | 47.2 ± 9.8 |


```{admonition} Note on Latency Measurements:
:class: tip
All latency values reported here were obtained experimentally using an oscilloscope. Visual stimulus latencies were measured with a photodiode placed on the display, while auditory stimulus latencies were measured using a direct electrical connection to the audio signal. These measurements correspond to the default system configuration described above. Any modifications to camera settings, display resolution, or other relevant hardware or software parameters may affect latency and should therefore be validated with new measurements. For experiments requiring precise temporal control, we strongly recommend measuring latencies directly within the specific experimental setup rather than relying solely on the reference values provided here.
```
