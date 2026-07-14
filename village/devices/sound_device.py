import os
import queue
import threading
import traceback
from math import gcd
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import resample_poly

from village.classes.enums import Active
from village.classes.null_classes import NullSoundDevice
from village.scripts.error_queue import error_queue
from village.scripts.log import log
from village.settings import settings


def get_sound_devices() -> list[str]:
    """Retrieves a list of available sound device names.

    Returns:
        list[str]: A list of device names.
    """
    devices = sd.query_devices()
    devices_str = [d["name"] for d in devices]
    return devices_str


class SoundDevice:
    """Handles audio playback using sounddevice.

    Attributes:
        samplerate (int): Audio sample rate.
        channels (int): Number of audio channels.
        latency (str): Latency setting for sounddevice.
        index (int): Index of the used sound device.
        error (str): Error message.
        stream (sd.OutputStream): The active audio stream (internal).
        sound (np.ndarray): The current sound buffer.
        command_queue (queue.Queue): Queue for processing audio commands in a thread.
        thread (threading.Thread): Background thread for audio processing.
        thread_running (bool): Flag to control the background thread.
    """

    def __init__(self) -> None:
        """Initializes the SoundDevice with settings."""
        self.samplerate = int(settings.get("SAMPLERATE"))
        self.channels = 2
        self.latency = "high"
        devices = get_sound_devices()
        device = settings.get("SOUND_DEVICE")
        self.index = devices.index(device) if device in devices else 0
        self.error = ""

        device_info = sd.query_devices(self.index, "output")
        print(
            f"Sound device default latencies: "
            f"low={device_info['default_low_output_latency']}, "
            f"high={device_info['default_high_output_latency']}"
        )

        sd.default.device = device
        sd.default.samplerate = self.samplerate
        sd.default.channels = self.channels
        sd.default.latency = self.latency

        self.stream = None
        self.sound: np.ndarray[np.float32] = np.empty(0, dtype=np.float32)

        self.command_queue: queue.Queue[tuple] = queue.Queue()

        self.thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.thread_running = True
        self.thread.start()

    def load(self, left: Any, right: Any) -> None:
        """Loads sound data into the playback queue.

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

        self.command_queue.put(("load", new_sound))

    def load_wav(self, file: str) -> None:
        """Loads a WAV file into the playback queue.

        Args:
            file (str): Filename of the WAV file in the media directory.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If sample rate mismatches or channel count is unsupported.
        """
        media_directory = settings.get("MEDIA_DIRECTORY")
        path = os.path.join(media_directory, file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist.")

        samplerate, data = wavfile.read(path)
        if samplerate != self.samplerate:
            raise ValueError(
                f"Expected samplerate {self.samplerate}, but got {samplerate}."
            )

        # Normalize to float32 in range [-1.0, 1.0] if needed
        if data.dtype != np.float32:
            if np.issubdtype(data.dtype, np.integer):
                max_val = np.iinfo(data.dtype).max
                data = data.astype(np.float32) / max_val
            else:
                data = data.astype(np.float32)

        if data.ndim == 1:
            left = right = data
        elif data.shape[1] == 2:
            left, right = data[:, 0], data[:, 1]
        else:
            raise ValueError("Unsupported number of channels in WAV file.")

        self.load(left, right)

    def play(self) -> None:
        """Triggers playback of the loaded sound."""
        self.command_queue.put(("play", None))

    def stop(self) -> None:
        """Stops playback."""
        self.command_queue.put(("stop", None))

    def _audio_worker(self) -> None:
        """Worker function for the audio thread to handle stream operations."""
        current_sound = np.empty(0, dtype=np.float32)
        stream = sd.OutputStream(dtype="float32")

        try:
            while self.thread_running:
                try:
                    command, data = self.command_queue.get(timeout=1.0)

                    if command == "load":
                        try:
                            stream.close()
                        except Exception:
                            pass
                        current_sound = data
                        stream = sd.OutputStream(dtype="float32")
                        stream.start()

                        period_ms = (
                            1000 * (stream.blocksize / self.samplerate)
                            if stream.blocksize
                            else 0
                        )
                        log.info(
                            f"Samplerate = {self.samplerate}"
                            f"granted latency={stream.latency:.4f}s, "
                            f"blocksize={stream.blocksize} ({period_ms:.2f} ms/period)"
                        )

                    elif command == "play":
                        if current_sound.size != 0:
                            stream.write(current_sound)

                    elif command == "stop":
                        try:
                            stream.stop()
                        except Exception:
                            pass

                    elif command == "shutdown":
                        break

                except queue.Empty:
                    continue

        except Exception:
            try:
                print("exception")
                error_queue.put_nowait(("sound", traceback.format_exc()))
            except queue.Full:
                print("error queue full, cannot log audio error")
                pass

        finally:
            if stream is not None:
                stream.close()

    def shutdown(self) -> None:
        """Shuts down the audio thread and stream."""
        if self.thread_running:
            self.thread_running = False
            self.command_queue.put(("shutdown", None))
            self.thread.join(timeout=2.0)

    def __del__(self) -> None:
        """Destructor to ensure shutdown."""
        self.shutdown()

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

    @staticmethod
    def create_sound_vec(left: np.ndarray, right: np.ndarray) -> np.ndarray[np.float32]:
        """Interleaves left and right channels into a stereo array.

        Args:
            left (np.ndarray): Left channel data.
            right (np.ndarray): Right channel data.

        Returns:
            np.ndarray[np.float32]: Interleaved stereo data.
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
