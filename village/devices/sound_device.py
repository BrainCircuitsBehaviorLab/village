from multiprocessing import Process, Value
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.signal import firwin, lfilter  # filters

from village.app.settings import settings
from village.app.utils import utils


class SoundDevice:
    def __init__(self, sampleRate=44100, channelsOut=2, latency="low") -> None:
        self.sampleRate = sampleRate
        self.channelsOut = channelsOut
        self.latency = latency
        devices = utils.get_sound_devices()
        device = settings.get("SOUND_DEVICE")
        self.index = devices.index(device) if device in devices else 0

        sd.default.device = device
        sd.default.samplerate = sampleRate
        sd.default.latency = latency
        sd.default.channels = channelsOut

        self._Stream = sd.OutputStream(dtype="float32")
        self._Stream.close()
        self._sound: np.ndarray[np.float32] = np.empty(0, dtype=np.float32)
        self._playing = Value("i", 0)
        self._p = Process(target=self._play_sound_background)
        self._p.daemon = True

    def load(self, v1, v2=None) -> None:
        """Load audio"""
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
        sound = self._create_sound_vec(v1, v2)
        self._Stream.close()
        self._Stream = sd.OutputStream(dtype="float32")
        self._Stream.start()
        self._sound = sound
        self._playing.value = 0  # type: ignore
        self._p = Process(target=self._play_sound_background)
        self._p.daemon = True
        self._p.start()
        print("SoundR: Loaded.")

    def playSound(self) -> None:
        if self._sound == []:
            raise ValueError("SoundR: No sound loaded. Please, use the method load().")
        self._playing.value = 1  # type: ignore

    def stopSound(self) -> None:
        try:
            if self._playing.value == 1:  # type: ignore
                self._playing.value = 2  # type: ignore
                self._Stream.close()
                self._p.terminate()
                print("SoundR: Stop.")
            elif self._playing.value == 0:  # type: ignore
                self._playing.value = 2  # type: ignore
        except AttributeError:
            print("SoundR: it is not possible to stop. No process is running.")

    def _play_sound_background(self) -> None:
        while True:
            if self._playing.value == 1:  # type: ignore
                print("SoundR: Play.")
                if self._sound == []:
                    print("Error: no sound is loaded.")
                    self._playing.value = 2  # type: ignore
                    break
                else:
                    self._Stream.write(self._sound)
                    self._playing.value = 2  # type: ignore
                    break
            elif self._playing.value == 2:  # type: ignore
                break

    @staticmethod
    def _create_sound_vec(v1, v2) -> np.ndarray[np.float32]:
        sound = np.array([v1, v2])  # left and right channel
        return np.ascontiguousarray(sound.T, dtype=np.float32)


def whiteNoiseGen(
    amp, band_fs_bot, band_fs_top, duration, FsOut=192000, Fn=10000, randgen=None
) -> Any:
    """whiteNoiseGen(amp, band_fs_bot, band_fs_top):
    beware this is not actually whitenoise
    amp: float, amplitude
    band_fs_bot: int, bottom freq of the band
    band_fs_top: int, top freq
    duration: secs
    FsOut: SoundCard samplingrate to use (192k, 96k, 48k...)
    Fn: filter len, def 10k
    *** if this takes too long try shortening Fn or using a lower FsOut ***
    adding some values here. Not meant to change them usually.
    randgen: np.random.RandomState instance to sample from

    returns: sound vector (np.array)
    """
    mean = 0
    std = 1
    if randgen is None:
        randgen = np.random

    if (
        isinstance(amp, float)
        and isinstance(band_fs_top, int)
        and isinstance(band_fs_bot, int)
        and band_fs_bot < band_fs_top
    ):
        band_fs = [band_fs_bot, band_fs_top]
        white_noise = amp * randgen.normal(mean, std, size=int(FsOut * (duration + 1)))
        band_pass = firwin(
            Fn,
            [band_fs[0] / (FsOut * 0.5), band_fs[1] / (FsOut * 0.5)],
            pass_zero=False,
        )
        band_noise = lfilter(band_pass, 1, white_noise)
        s1 = band_noise[FsOut : int(FsOut * (duration + 1))]
        return s1  # use np.zeros(s1.size) to get equal-size empty vec.
    else:
        raise ValueError("whiteNoiseGen needs (float, int, int, num,) as arguments")


sound_device = SoundDevice()
