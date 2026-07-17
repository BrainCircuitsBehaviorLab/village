## Sound Integration

The Training Village uses the **Raspberry DAC Pro** HAT for audio output. Connect it
directly on top of the Raspberry Pi or on top of the Main HAT if one is installed. Audio
playback from within tasks is handled by the Python `pyalsaaudio` library, which talks to
ALSA directly, without going through PortAudio.


### Configuration

1. Connect headphones or speakers to the DAC output.

2. Right-click the volume icon in the top system bar and select **Device Profiles**. The
   **RPi DAC Pro** entry should appear in the list. Select it and set the output profile
   to **Stereo Output**.

3. Play any audio to verify the DAC is working correctly.

4. Once confirmed, return to **Device Profiles**, select **RPi DAC Pro** again, and set
   the profile to **Off**. The operating system will no longer use the device, leaving it
   free for `pyalsaaudio` to access directly.

```{admonition} Why the DAC must be released from the system before use
:class: warning
When the DAC is set as the active audio output in the desktop environment, the operating
system holds exclusive access to the device, preventing the Training Village from using
it. Setting the profile to **Off** releases the device and makes it available for the
Training Village.

5. Launch the Training Village and select your soundcard under
   `SETTINGS` → `SOUND SETTINGS`.

```{admonition} Note
:class: tip
This configuration step only needs to be done once. The "Off" profile selection persists
across reboots, so the DAC will remain available to the Training Village after the system
restarts.
```

### Using the sound device in tasks

Audio files are read from the project's **media directory**:
`/village_projects/<project_name>/media`. This path is configured in
`SETTINGS` → `DIRECTORY SETTINGS` as `MEDIA_DIRECTORY`. Place WAV files there and
reference them by filename only (no path needed).

Every sound must be loaded before it is played — never call `play` twice in a
row without a `load` in between. `stop` is optional, only needed to cut a sound
short before it finishes on its own.

1. **`load`** — decodes the audio and stages it in the buffer. This can be a slow operation (hundreds of ms depending on audio length), so it is best called during the inter-trial interval.
2. **`play`** — starts playback of whatever is currently in the buffer. This is much faster — measured latencies are below 5 ms. Calling `play` again while a sound is still playing is ignored, so it must always be preceded by its own `load`.
3. **`stop`** *(optional)* — interrupts playback mid-sound.

After calling `stop`, the buffer is no longer valid and a new `load` is required
before the next `play`.

```{admonition} Fade-in / fade-out ramp
:class: tip
If the `SOUND_RAMP_MS` setting (`SETTINGS` → `SOUND SETTINGS`) is set to a value other
than zero, a raised-cosine ramp of that duration is applied automatically to every sound:
at its start, at its end, and whenever `stop` cuts playback short. This smooths out the
abrupt amplitude changes that would otherwise cause audible clicks. Setting it to `0`
disables the ramp entirely.
```

```python
from village.devices.sound_device import sound_device

# Option 1 — play a WAV file from the media directory
gain = 0.5   # volume, from 0.0 (silent) to 1.0 (full scale)
left, right = sound_device.get_sound_from_wav("tone.wav", gain)
sound_device.load(left, right)
sound_device.play()

# To play the same sound again, load must be called again
left, right = sound_device.get_sound_from_wav("tone.wav", gain)
sound_device.load(left, right)
sound_device.play()

# Option 2 — generate a tone with numpy and play it
import numpy as np

samplerate = 192000          # must match SAMPLERATE setting
duration   = 0.5             # seconds
frequency  = 4000            # Hz

# volume calibrated so the tone measures 70 dB from speaker 1
gain = self.calibrations.sound_calibration.get_sound_gain(
    speaker=1, dB=70.0, sound_name="tone"
)

t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
tone = (gain * np.sin(2 * np.pi * frequency * t)).astype(np.float32)

sound_device.load(tone, tone)   # identical left and right channels → mono
sound_device.play()
```

`get_sound_from_wav` resamples the audio if the WAV's sample rate does not match
`SAMPLERATE`, and returns both channels as `float32` arrays in the range `[-1.0, 1.0]`,
scaled by `gain`.

```{admonition} Prefer a matching sample rate
:class: warning
Resampling is a fallback, not something to rely on. It costs extra time on every
`get_sound_from_wav` call and can degrade audio quality. Whenever possible, save your
WAV files at the same sample rate as the `SAMPLERATE` setting so no resampling is needed.
```

### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `get_sound_from_wav(file, gain)` | `file`: filename, `gain`: volume, `0.0`–`1.0` | Reads a WAV from `MEDIA_DIRECTORY`, applies `gain`, returns `(left, right)` arrays. |
| `load(left, right)` | numpy arrays, equal length | Stages stereo audio for playback. Pass `None` for a silent channel. |
| `play()` | — | Triggers playback of the loaded sound. |
| `stop()` | — | Interrupts playback. |
