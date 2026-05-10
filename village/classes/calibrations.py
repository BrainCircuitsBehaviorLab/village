from typing import Callable

from village.calibration.bpod_water_calibration import BpodWaterCalibration
from village.calibration.camera_calibration import CameraCalibration
from village.calibration.sound_calibration import SoundCalibration


class Calibrations:

    def __init__(self) -> None:
        self.bpod_water_calibration = BpodWaterCalibration()
        self.sound_calibration = SoundCalibration()
        self.camera_calibration = CameraCalibration()
        self.sound_calibration_functions: list[Callable] = []
        self.sound_calibration_error: bool = False
