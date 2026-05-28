## Timing & Clock Synchronization

### Absolute Time (Unix Epoch)

All timestamps across the platform conform to standard **Unix Epoch Time** — a
floating-point value representing total seconds elapsed since January 1, 1970,
00:00:00 UTC:

$$\text{Timestamp} = 1748300000.123 \longrightarrow \text{Precise calendar moment in time}$$

This format is consistent across all Linux subsystems, making it straightforward to
subtract timestamps to compute durations or compare events across independent rigs.

### Hardware Synchronization

Depending on your setup, hardware timing is managed through one of two pathways:

#### **1. Raspberry Pi only (native execution)**
Timestamps are derived directly from the Linux system clock via `time.time()`.

#### **2. Coprocessor-integrated setups (Bpod or Arduino)**
Microcontrollers maintain independent internal hardware timers. To align these with the
Raspberry Pi master clock, a synchronization handshake is performed at the start of
every trial:

1. At the moment the state machine launches a trial, two clock values are captured
   simultaneously:
   - `raspberry_timestamp`: Current Unix epoch time on the master clock.
   - `coprocessor_timestamp`: Reset to `0.0` as the microcontroller begins the
     trial loop.
2. A constant offset is computed:
   `offset = raspberry_timestamp - coprocessor_timestamp`
3. As serial data packets arrive from the microcontroller, their hardware timestamps are
   converted to absolute Unix time before being written to disk:
   `timestamp_absolute = coprocessor_timestamp + offset`

This approach preserves the sub-millisecond precision of the external hardware controller
while writing all data in master Unix Epoch time.

### Precision Limits & Clock Drift

This synchronization model assumes the computed offset remains stable throughout a trial.
In practice, physical oscillator variations can cause minor clock drift of up to
**~1 ms per minute** relative to the Raspberry Pi.

- **Short trials (< 1–2 minutes):** Drift is negligible and can be safely ignored for
  standard behavioral analysis.
- **Long trials:** In paradigms with very long trials, it is advisable to
  handle timestamps that depend on the coprocessor separately from those derived solely
  from the Raspberry Pi clock. For example in a 15 minutes trial, cumulative drift can
  introduce up to **15 ms of offset** by the end of a single trial.
