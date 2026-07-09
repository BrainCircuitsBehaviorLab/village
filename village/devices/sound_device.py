import os
import traceback
from math import gcd
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import resample_poly

from village.classes.enums import Active
from village.classes.null_classes import NullSoundDevice
from village.scripts.log import log
from village.settings import settings


def get_sound_devices() -> list[str]:
    """Retrieves a list of available sound device names.

    Returns:
        list[str]: A list of device names, or ["No device"] if none are found.
    """
    devices = sd.query_devices()
    devices_str = [d["name"] for d in devices]
    return devices_str if devices_str else ["No device"]


class SoundDevice:
    """Handles audio playback using a callback-based sounddevice OutputStream.

    The stream runs permanently. load() prepares audio data, play() triggers
    playback from the start, and stop() halts it within one callback cycle
    (~blocksize/samplerate seconds).
    """

    def __init__(self) -> None:
        self.samplerate = int(settings.get("SAMPLERATE"))
        self.channels = 2
        _blocksize_map = {44100: 256, 48000: 256, 96000: 512, 192000: 1024}
        self.blocksize = _blocksize_map.get(self.samplerate, 1024)
        devices = get_sound_devices()
        device = settings.get("SOUND_DEVICE")
        self.index = devices.index(device) if device in devices else 0
        self.error = ""

        self._audio_data: np.ndarray = np.zeros((self.blocksize, 2), dtype=np.float32)
        self._pos: int = 0
        self._playing: bool = False

        device_info = sd.query_devices(self.index, "output")
        print(
            f"Sound device default latencies: "
            f"low={device_info['default_low_output_latency']}, "
            f"high={device_info['default_high_output_latency']}"
        )

        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.blocksize,
            latency="low",
            device=device,
            callback=self._callback,
        )
        self.stream.start()

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ) -> None:
        if not self._playing:
            outdata[:] = 0
            return

        pos = self._pos
        data = self._audio_data
        remaining = len(data) - pos

        if remaining <= 0:
            outdata[:] = 0
            self._playing = False
            return

        n = min(frames, remaining)
        outdata[:n] = data[pos : pos + n]
        if n < frames:
            outdata[n:] = 0
            self._playing = False
        self._pos = pos + n

    def load(self, left: Any, right: Any) -> None:
        """Prepares audio data for playback.

        Args:
            left (Any): Left channel data (array-like).
            right (Any): Right channel data (array-like).

        Raises:
            ValueError: If inputs are invalid or lengths differ.
        """
        if left is None and right is not None:
            left = np.zeros(len(right))
        elif right is None and left is not None:
            right = np.zeros(len(left))
        elif left is None and right is None:
            raise ValueError("Sound error: Both vectors left and right are None.")

        if len(left) != len(right):
            raise ValueError(
                "Sound error: Left and right vectors must have same length."
            )

        new_sound = self.create_sound_vec(left, right)
        self._playing = False
        self._audio_data = new_sound
        self._pos = 0

    def get_sound_from_wav(
        self, file: str, gain: float
    ) -> tuple[np.ndarray, np.ndarray]:
        media_directory = settings.get("MEDIA_DIRECTORY")
        path = os.path.join(media_directory, file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist.")

        samplerate, data = wavfile.read(path)
        if np.issubdtype(data.dtype, np.integer):
            max_val = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / max_val
        elif data.dtype != np.float32:
            data = data.astype(np.float32)

        if samplerate != self.samplerate:
            g = gcd(samplerate, self.samplerate)
            data = resample_poly(data, self.samplerate // g, samplerate // g, axis=0)
            data = data.astype(np.float32)

        if data.ndim == 1:
            left = right = data
        elif data.shape[1] == 2:
            left, right = data[:, 0], data[:, 1]
        else:
            raise ValueError("Unsupported number of channels in WAV file.")

        if gain != 1.0:
            if not 0.0 <= gain <= 1.0:
                raise ValueError(f"gain must be between 0 and 1, got {gain}.")
            left = left * gain
            right = right * gain

        return left, right

    def play(self) -> None:
        """Starts playback from the beginning of the loaded sound."""
        self._pos = 0
        self._playing = True

    def stop(self) -> None:
        """Stops playback. Takes effect within one callback cycle (~5ms)."""
        self._playing = False

    def shutdown(self) -> None:
        """Stops and closes the audio stream."""
        self._playing = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def __del__(self) -> None:
        self.shutdown()

    @staticmethod
    def create_sound_vec(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Interleaves left and right channels into a stereo array.

        Args:
            left (np.ndarray): Left channel data.
            right (np.ndarray): Right channel data.

        Returns:
            np.ndarray: Interleaved stereo float32 array of shape (N, 2).
        """
        sound = np.array([left, right])
        return np.ascontiguousarray(sound.T, dtype=np.float32)


def get_sound_device() -> SoundDevice | NullSoundDevice:
    """Factory function to initialize the SoundDevice.

    Returns:
        SoundDevice | NullSoundDevice: An initialized SoundDevice or
        NullSoundDevice if disabled or initialization fails.
    """
    if settings.get("USE_SOUNDCARD") == Active.OFF:
        return NullSoundDevice()
    else:
        try:
            sound_device = SoundDevice()
            log.info("Sound device successfully initialized")
            return sound_device
        except Exception:
            log.error(
                "Could not initialize sound device", exception=traceback.format_exc()
            )
            return NullSoundDevice()


sound_device = get_sound_device()
