from collections.abc import Callable
from typing import TYPE_CHECKING

from village.classes.null_classes import NullCalibrationBase

if TYPE_CHECKING:
    from village.calibration.bpod_water_calibration import BpodWaterCalibration
    from village.calibration.camera_calibration import CameraCalibration
    from village.calibration.corridor_threshold_calibration import (
        CorridorThresholdCalibration,
    )
    from village.calibration.optogrid_calibration import OptoGridCalibration
    from village.calibration.sound_calibration import SoundCalibration


class Calibrations:

    def __init__(self) -> None:
        self.bpod_water_calibration: BpodWaterCalibration | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.sound_calibration: SoundCalibration | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.camera_calibration: CameraCalibration | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.corridor_threshold_calibration: (
            CorridorThresholdCalibration | NullCalibrationBase
        ) = NullCalibrationBase()
        self.optogrid_calibration: OptoGridCalibration | NullCalibrationBase = (
            NullCalibrationBase()
        )
        self.sound_calibration_functions: list[Callable] = []
        self.sound_calibration_error: bool = False
