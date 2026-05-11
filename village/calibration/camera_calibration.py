from __future__ import annotations

from village.custom_classes.calibration_base import CalibrationBase


class CameraCalibration(CalibrationBase):
    name = "camera_calibration"

    @classmethod
    def is_active(cls) -> bool:
        return True

    def draw(self) -> None:
        pass
