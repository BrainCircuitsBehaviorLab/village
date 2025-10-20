import os
import queue
import threading
import traceback
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from village.classes.abstract_classes import SoundDeviceBase
from village.classes.enums import Active
from village.scripts.error_queue import error_queue
from village.scripts.log import log
from village.settings import settings


def get_sound_devices() -> list[str]:
    devices = sd.query_devices()
    devices_str = [d["name"] for d in devices]
    return devices_str


class SoundDevice(SoundDeviceBase):
    def __init__(self) -> None:
        self.samplerate = int(settings.get("SAMPLERATE"))
        self.channels = 2
        self.latency = "high"
        devices = get_sound_devices()
        device = settings.get("SOUND_DEVICE")
        self.index = devices.index(device) if device in devices else 0
        self.error = ""

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
        self.command_queue.put(("play", None))

    def stop(self) -> None:
        self.command_queue.put(("stop", None))

    def _audio_worker(self) -> None:
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
                print("ha habido una exception!!!!")
                error_queue.put_nowait(("sound", traceback.format_exc()))
            except queue.Full:
                print("error queue full, cannot log audio error")
                pass

        finally:
            if stream is not None:
                stream.close()

    def shutdown(self) -> None:
        if self.thread_running:
            self.thread_running = False
            self.command_queue.put(("shutdown", None))
            self.thread.join(timeout=2.0)

    def __del__(self) -> None:
        self.shutdown()

    @staticmethod
    def create_sound_vec(left: np.ndarray, right: np.ndarray) -> np.ndarray[np.float32]:
        sound = np.array([left, right])
        return np.ascontiguousarray(sound.T, dtype=np.float32)


def get_sound_device() -> SoundDeviceBase:
    if settings.get("USE_SOUNDCARD") == Active.OFF:
        return SoundDeviceBase()
    else:
        try:
            sound_device = SoundDevice()
            log.info("Sound device successfully initialized")
            return sound_device
        except Exception:
            log.error(
                "Could not initialize sound device", exception=traceback.format_exc()
            )
            return SoundDeviceBase()


sound_device = get_sound_device()
