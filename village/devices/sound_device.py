from multiprocessing import Process, Value
from typing import Any

import numpy as np
import sounddevice as sd

from village.manager import manager
from village.settings import settings


class SoundDevice:
    def __init__(self, samplerate, channels=2, latency="high") -> None:
        self.samplerate = samplerate
        self.channels = channels
        self.latency = latency
        devices = manager.get_sound_devices()
        device = settings.get("SOUND_DEVICE")
        self.index = devices.index(device) if device in devices else 0

        sd.default.device = device
        sd.default.samplerate = samplerate
        sd.default.channels = channels
        sd.default.latency = latency

        self.stream = sd.OutputStream(dtype="float32")
        self.stream.close()
        self.sound: np.ndarray[np.float32] = np.empty(0, dtype=np.float32)
        self.playing = Value("i", 0)
        self.process = Process(target=self._play_sound_background, daemon=True)

    def load(self, v1, v2=None) -> None:
        if v2 is None:
            v2 = v1
        if len(v1) != len(v2):
            raise ValueError(
                "Sound: The length of the vectors v1 and v2 has to be the same."
            )
        try:
            self.stop()
        except AttributeError:
            pass

        self.sound = self.create_sound_vec(v1, v2)
        self.stream.close()
        self.stream = sd.OutputStream(dtype="float32")
        self.stream.start()
        self.playing.value = 0  # type: ignore
        self.process = Process(target=self._play_sound_background, daemon=True)
        self.process.start()

    def play(self) -> None:
        if self.sound.size == 0:
            raise ValueError("SoundR: No sound loaded. Please, use the method load().")
        self.playing.value = 1  # type: ignore

    def stop(self) -> None:
        try:
            if self.playing.value == 1:  # type: ignore
                self.playing.value = 2  # type: ignore
                self.stream.close()
                self.process.terminate()
            elif self.playing.value == 0:  # type: ignore
                self.playing.value = 2  # type: ignore
        except AttributeError:
            print("It is not possible to stop. No process is running.")

    def _play_sound_background(self) -> None:
        while True:
            if self.playing.value == 1:  # type: ignore
                if self.sound.size == 0:
                    print("Error: no sound is loaded.")
                    self.playing.value = 2  # type: ignore
                    break
                else:
                    self.stream.write(self.sound)
                    self.playing.value = 2  # type: ignore
                    break
            elif self.playing.value == 2:  # type: ignore
                break

    @staticmethod
    def create_sound_vec(v1, v2) -> np.ndarray[np.float32]:
        sound = np.array([v1, v2])  # left and right channel
        return np.ascontiguousarray(sound.T, dtype=np.float32)


def tone_generator(
    duration: float,
    amplitude: float,
    frequency: float,
    ramp_time: float,
    samplerate: int,
) -> np.ndarray[Any, np.dtype[np.floating[Any]]]:
    """
    Generate a single tone with ramping
    Args:
        duration (float): Duration (seconds)
        ramp_time (float): Ramp up/down time (seconds)
        amplitude (float): Tone amplitude
        frequency (float): Tone frequency
        samplerate (int): Samplerate must match the sound device samplerate
    Returns:
        np.ndarray: Generated tone
    """

    time = np.linspace(0, duration, int(samplerate * duration))
    # If no frequency specified, return zero array
    if frequency == 0:
        return np.zeros_like(time)
    # Generate tone
    tone = amplitude * np.sin(2 * np.pi * frequency * time)
    # Calculate ramp points
    sample_rate = 1 / (time[1] - time[0])
    ramp_points = int(ramp_time * sample_rate)
    # Create ramp arrays
    if ramp_points > 0:
        ramp_up = np.linspace(0, 1, ramp_points)
        ramp_down = np.linspace(1, 0, ramp_points)
        # Apply ramps
        tone[:ramp_points] *= ramp_up
        tone[-ramp_points:] *= ramp_down
    return tone


def whitenoise_generator(
    duration: float,
    amplitude: float,
    samplerate: int,
) -> np.ndarray[Any, np.dtype[np.floating[Any]]]:
    """
    Generate white noise with ramping
    Args:
        duration (float): Duration (seconds)
        amplitude (float): Noise amplitude
        samplerate (int): Samplerate must match the sound device samplerate
    """
    noise = amplitude * np.random.uniform(-1, 1, int(samplerate * duration))
    return noise


samplerate = 192000

# duration = 3
# ramp = 0.005
# amplitude = 0.01
# frequency = 6000


sound_device = SoundDevice(samplerate=samplerate)

# sound = tone_generator(duration, amplitude, frequency, ramp, samplerate)
# # sound = whitenoise_generator(duration, amplitude, samplerate)
# sound_device.load(sound)
# sound_device.play()
# import time
# time.sleep(duration + 1)
