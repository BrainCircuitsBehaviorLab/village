from multiprocessing import Process, Value
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.signal import firwin, lfilter

from village.manager import manager
from village.settings import settings


class SoundDevice:
    def __init__(self, samplerate=192000, channels=2, latency="low") -> None:
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
            self.stopSound()
        except AttributeError:
            pass

        self.sound = self.create_sound_vec(v1, v2)
        self.stream.close()
        self.stream = sd.OutputStream(dtype="float32")
        self.stream.start()
        self.playing.value = 0  # type: ignore
        self.process = Process(target=self._play_sound_background, daemon=True)
        self.process.start()

    def playSound(self) -> None:
        if self.sound.size == 0:
            raise ValueError("SoundR: No sound loaded. Please, use the method load().")
        self.playing.value = 1  # type: ignore

    def stopSound(self) -> None:
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


def whiteNoiseGen(
    amp,
    band_freq_bottom,
    band_freq_top,
    duration,
    samplerate=192000,
    filter_len=10000,
    randgen=None,
) -> Any:
    """whiteNoiseGen(amp, band_fs_bot, band_fs_top):
    beware this is not actually whitenoise
    amp: float, amplitude
    band_freq_bottom: int, bottom freq of the band
    band_freq_top: int, top freq
    duration: secs
    samplerate: must match the sound device samplerate
    filter_len: filter len, def 10k
    *** if this takes too long try shortening filter_len or using a lower samplerate***
    randgen: np.random.RandomState instance to sample from

    returns: sound vector (np.array)
    """
    mean = 0
    std = 1
    if randgen is None:
        randgen = np.random

    if (
        isinstance(amp, float)
        and isinstance(band_freq_top, int)
        and isinstance(band_freq_bottom, int)
        and band_freq_bottom < band_freq_top
    ):
        band_fs = [band_freq_bottom, band_freq_top]
        white_noise = amp * randgen.normal(
            mean, std, size=int(samplerate * (duration + 1))
        )
        band_pass = firwin(
            filter_len,
            [band_fs[0] / (samplerate * 0.5), band_fs[1] / (samplerate * 0.5)],
            pass_zero=False,
        )
        band_noise = lfilter(band_pass, 1, white_noise)
        s1 = band_noise[samplerate : int(samplerate * (duration + 1))]
        return s1  # use np.zeros(s1.size) to get equal-size empty vec.
    else:
        raise ValueError("whiteNoiseGen needs (float, int, int, num,) as arguments")


soundDevice = SoundDevice()

input("soundDevice created")

sound = whiteNoiseGen(0.5, 1000, 2000, 1)

input("white noise created")

soundDevice.load(sound)

input("sound loaded")

soundDevice.playSound()

input("sound played")
