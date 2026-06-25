## Sound Integration

The Training Village uses the **HiFiBerry DAC+ Pro** HAT for audio output. Connect it
directly on top of the Raspberry Pi or on top of the Main HAT if one is installed. Audio
playback from within tasks is handled by the Python `sounddevice` library, which accesses
the hardware through PortAudio → ALSA.


### Configuration

1. Connect headphones or speakers to the DAC output.

2. Right-click the volume icon in the top system bar and select **Device Profiles**. The
   **RPi DAC Pro** entry should appear in the list. Select it and set the output profile
   to **Stereo Output**.

3. Play any audio to verify the DAC is working correctly.

4. Once confirmed, return to **Device Profiles**, select **RPi DAC Pro** again, and set
   the profile to **Off**. The operating system will no longer use the device, leaving it
   free for `sounddevice` to access directly.

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

The playback cycle always follows the same order:

1. **`load`** — decodes the audio and stages it in the buffer. Puede ser un proceso largo (dependiendo de la longitud del audio, cientos de ms) por lo que es conveniente hacerlo en el inter-trial interval.
2. **`play`** — starts playback of whatever is currently in the buffer. Esto es mucho mas rapido, latencias medidas por debajo de 10ms.
3. **`stop`** — interrupts playback mid-sound.

After calling `stop`, the buffer is no longer valid and a new `load` is required
before the next `play`.

```python
from village.devices.sound_device import sound_device

# Option 1 — play a WAV file from the media directory
left, right = sound_device.get_sound_from_wav("tone.wav")
sound_device.load(left, right)
sound_device.play()

# To play the same sound again, load must be called again
sound_device.stop()
left, right = sound_device.get_sound_from_wav("tone.wav")
sound_device.load(left, right)
sound_device.play()

# Option 2 — generate a tone with numpy and play it
import numpy as np

samplerate = 192000          # must match SAMPLERATE setting
duration   = 0.5             # seconds
frequency  = 4000            # Hz
t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
tone = np.sin(2 * np.pi * frequency * t).astype(np.float32)

sound_device.load(tone, tone)   # identical left and right channels → mono
sound_device.play()
```

`get_sound_from_wav` validates that the WAV sample rate matches `SAMPLERATE` and
returns both channels as `float32` arrays in the range `[-1.0, 1.0]`.

### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `get_sound_from_wav(file)` | `file`: filename | Reads a WAV from `MEDIA_DIRECTORY`, returns `(left, right)` arrays. |
| `load(left, right)` | numpy arrays, equal length | Stages stereo audio for playback. Pass `None` for a silent channel. |
| `play()` | — | Triggers playback of the loaded sound. |
| `stop()` | — | Interrupts playback. |
