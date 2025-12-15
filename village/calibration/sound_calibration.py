import time
import traceback
from threading import Thread

from village.devices.sound_device import sound_device
from village.manager import manager
from village.scripts.log import log


class SoundCalibration:
    """Class to handle sound calibration procedures."""

    def __init__(
        self, speaker: int, gain: float, sound_index: int, duration: float
    ) -> None:
        """Initializes the SoundCalibration instance.

        Args:
            speaker (int): The speaker ID to calibrate (0 or 1).
            gain (float): The gain value to test.
            sound_index (int): Index of the sound function in the manager.
            duration (float): Duration of the calibration sound.
        """
        self.speaker = speaker
        self.gain = gain
        self.sound_index = sound_index
        self.duration = duration

    def run(self) -> None:
        """Executes the sound calibration process.

        Generates sound, loads it to the specified speaker, plays it, and handles errors.
        """
        try:
            generator = manager.sound_calibration_functions[self.sound_index]
            sound = generator(duration=self.duration, gain=self.gain)

            if self.speaker == 0:
                sound_device.load(sound, None)
            else:
                sound_device.load(None, sound)

            sound_device.play()
            time.sleep(self.duration + 1)
            sound_device.stop()
        except Exception:
            log.error("Error calibrating sound", exception=traceback.format_exc())
            manager.sound_calibration_error = True

    def run_in_thread(self, daemon: bool = True) -> None:
        """Runs the calibration process in a separate thread.

        Args:
            daemon (bool, optional): Whether to run as a daemon thread. Defaults to True.
        """
        self.process = Thread(target=self.run, daemon=daemon)
        self.process.start()
        return

    def close(self) -> None:
        """Closes the calibration instance and releases resources."""
        return

