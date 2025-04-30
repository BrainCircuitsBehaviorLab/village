import time
import traceback
from threading import Thread

from village.devices.sound_device import sound_device
from village.log import log
from village.manager import manager


class SoundCalibration:
    def __init__(
        self, speaker: int, gain: float, sound_index: int, duration: float
    ) -> None:
        self.speaker = speaker
        self.gain = gain
        self.sound_index = sound_index
        self.duration = duration

    def run(self) -> None:
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

    def run_in_thread(self, daemon=True) -> None:
        self.process = Thread(target=self.run, daemon=daemon)
        self.process.start()
        return

    def close(self) -> None:
        return
