# Sound generators for this project. Two kinds of functions live here:
#
# 1. Generic generators (tone_generator, whitenoise_generator) that take
#    whatever arguments they need and can be called from anywhere, e.g. from
#    direct_functions.py or a task or touchscreen trigger, camera trigger, etc.
# 2. Calibration-sound wrappers (whitenoise, tone_600, tone_1000, ...) that
#    thinly wrap a generic generator, fixing every argument except duration
#    and gain (Sound Calibration always calls them with just those two).
#    They are listed in sound_calibration_functions below, which fills the
#    SOUND dropdown in the Sound Calibration panel. A wrapper's __name__ is
#    stored as the sound's identity in the calibration data (sound_name) and
#    in get_sound_gain(..., sound_name=...) calls elsewhere in the project --
#    rename a wrapper here and every reference to its old name has to be
#    updated too, or the calibration lookup silently stops matching.
#
# gain here is a raw signal amplitude in [0, 1], not dB -- the dB <-> gain
# conversion is what the calibration curve is for (see get_sound_gain).

import numpy as np

from village.devices.sound_device import sound_device


# generators of sounds, must return numpy arrays
def tone_generator(
    duration: float,
    gain: float,
    frequency: int,
) -> np.ndarray:
    """
    Generate a single tone
    Args:
        duration (float): Duration (seconds)
        gain (float): Tone amplitude
        frequency (int): Tone frequency
    Returns:
        np.ndarray: Generated sound
    """

    samplerate = sound_device.samplerate

    time = np.linspace(0, duration, int(samplerate * duration))
    # If no frequency specified, return zero array
    if frequency == 0:
        return np.zeros_like(time)
    # Generate tone
    tone = gain * np.sin(2 * np.pi * frequency * time)
    return tone


def whitenoise_generator(
    duration: float,
    gain: float,
) -> np.ndarray:
    """
    Generate white noise
    Args:
        duration (float): Duration (seconds)
        gain (float): Noise amplitude
    Returns:
        np.ndarray: Generated sound
    """

    samplerate = sound_device.samplerate

    # Generate noise
    noise = gain * np.random.uniform(-1, 1, int(samplerate * duration))
    return noise


# Calibration sounds. Each one must take exactly (duration, gain) -- that's
# the signature the Sound Calibration panel calls them with -- so any extra
# parameter of the underlying generator (like tone_generator's frequency) is
# pinned to a fixed value here.
def whitenoise(duration: float, gain: float) -> np.ndarray:
    return whitenoise_generator(duration=duration, gain=gain)


def tone_600(duration: float, gain: float) -> np.ndarray:
    return tone_generator(duration=duration, gain=gain, frequency=600)


def tone_1000(duration: float, gain: float) -> np.ndarray:
    return tone_generator(duration=duration, gain=gain, frequency=1000)


def tone_5000(duration: float, gain: float) -> np.ndarray:
    return tone_generator(duration=duration, gain=gain, frequency=5000)


def tone_10000(duration: float, gain: float) -> np.ndarray:
    return tone_generator(duration=duration, gain=gain, frequency=10000)


def tone_20000(duration: float, gain: float) -> np.ndarray:
    return tone_generator(duration=duration, gain=gain, frequency=20000)


# Order here is the order the SOUND dropdown shows them in, in both the
# Calibrating and Testing sections of the Sound Calibration panel.
sound_calibration_functions = [
    whitenoise,
    tone_600,
    tone_1000,
    tone_5000,
    tone_10000,
    tone_20000,
]
