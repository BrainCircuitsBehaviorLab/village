from typing import TYPE_CHECKING, Callable

from village.classes.null_classes import NullCalibrationBase

if TYPE_CHECKING:
    from village.custom_classes.calibration_base import CalibrationBase


class Calibrations:

    def __init__(self) -> None:
        self.bpod_water_calibration: CalibrationBase | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.sound_calibration: CalibrationBase | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.camera_calibration: CalibrationBase | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.sound_calibration_functions: list[Callable] = []
        self.sound_calibration_error: bool = False
