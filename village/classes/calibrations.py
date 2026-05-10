from typing import Callable

from village.custom_classes.calibration_base import CalibrationBase


class Calibrations:

    def __init__(self) -> None:
        self.bpod_water_calibration = CalibrationBase()
        self.sound_calibration = CalibrationBase()
        self.camera_calibration = CalibrationBase()
        self.sound_calibration_functions: list[Callable] = []
        self.sound_calibration_error: bool = False
