import threading
import time
import traceback
from typing import Any

import numpy as np
import sounddevice as sd

from village.classes.enums import Active
from village.classes.protocols import SoundDeviceProtocol
from village.log import log
from village.settings import settings


def get_sound_devices() -> list[str]:
    devices = sd.query_devices()
    devices_str = [d["name"] for d in devices]
    return devices_str


class SoundDevice(SoundDeviceProtocol):
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

        self.stream = sd.OutputStream(dtype="float32")
        self.stream.close()
        self.sound: np.ndarray[np.float32] = np.empty(0, dtype=np.float32)
        self.playing = 0  # 0 = not playing, 1 = play, 2 = stop
        self.thread = threading.Thread(target=self._play_sound_background, daemon=True)
        self.thread_running = False
        self.lock = threading.Lock()

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

        self.stop()
        self.sound = self.create_sound_vec(left, right)
        self.stream.close()
        self.stream = sd.OutputStream(dtype="float32")
        self.stream.start()
        self.playing = 0
        self.thread = threading.Thread(target=self._play_sound_background, daemon=True)
        self.thread_running = True
        self.thread.start()

    def play(self) -> None:
        if self.sound.size == 0:
            raise ValueError("SoundR: No sound loaded. Please, use the method load().")
        self.playing = 1

    def stop(self) -> None:
        if self.thread.is_alive():
            self.playing = 2
            self.thread.join(timeout=1.0)
            self.stream.close()
            self.thread_running = False

    def _play_sound_background(self) -> None:
        while self.thread_running:
            if self.playing == 0:
                time.sleep(0.001)
            elif self.playing == 1:
                if self.sound.size == 0:
                    print("Error: no sound is loaded.")
                    self.playing = 2
                    break
                else:
                    self.stream.write(self.sound)
                    self.playing = 2
                    break
            elif self.playing == 2:
                break

    @staticmethod
    def create_sound_vec(left: np.ndarray, right: np.ndarray) -> np.ndarray[np.float32]:
        sound = np.array([left, right])
        return np.ascontiguousarray(sound.T, dtype=np.float32)


def get_sound_device() -> SoundDeviceProtocol:
    if settings.get("USE_SOUNDCARD") == Active.OFF:
        return SoundDeviceProtocol()
    else:
        try:
            sound_device = SoundDevice()
            log.info("Sound device successfully initialized")
            return sound_device
        except Exception:
            log.error(
                "Could not initialize sound device", exception=traceback.format_exc()
            )
            return SoundDeviceProtocol()


sound_device = get_sound_device()
