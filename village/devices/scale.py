import struct
import time
import traceback

import numpy as np
import smbus2

from village.classes.enums import Active
from village.classes.null_classes import NullScale
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import settings

scale_corridor_enabled: bool = settings.get("USE_CORRIDOR") == Active.ON
scale_box_enabled: bool = (
    settings.get("USE_BOX_BOARD") == Active.ON
    and settings.get("SCALE_BOX") == Active.ON
)


class Scale(NullScale):
    """Interface for an I2C scale sensor.

    Args:
        address (str): The I2C address of the scale as a hex string (e.g., "0x2A").
        min_threshold (float): The minimum weight threshold for valid measurements.
        max_threshold (float): The maximum weight threshold for valid measurements.
        calibration_key (str): The setting key holding this scale's calibration
            factor. Each physical scale needs its own key so calibrating one
            does not overwrite another's calibration.
        weight_to_calibrate_key (str): The setting key holding the known weight
            last used to calibrate this scale.

    Attributes:
        I2C_ADDR (int): The I2C address of the scale.
        REG_DATA_GET_RAM_DATA (int): Register address for getting raw data.
        bus (int): The I2C bus number.
        calibration (float): Calibration factor.
        calibration_key (str): The setting key this scale's calibration is stored under.
        weight_to_calibrate_key (str): The setting key this scale's last
            calibration weight is stored under.
        offset (float): Tare offset.
        i2cbus (smbus2.SMBus): The I2C bus connection.
        error (str): Error message if any.
        error_message_timer (time_utils.Timer): Timer to limit error logging frequency.
        alarm_timer (time_utils.Timer): Timer for non-responsive alarms.
        min (float): Minimum weight threshold.
        max (float): Maximum weight threshold.
    """

    def __init__(
        self,
        address: str,
        min_threshold: float,
        max_threshold: float,
        calibration_key: str = "SCALE_CALIBRATION_VALUE",
        weight_to_calibrate_key: str = "SCALE_WEIGHT_TO_CALIBRATE",
    ) -> None:
        """Initializes the Scale.

        Args:
            address (str): The I2C address as a hex string (e.g., "0x2A").
            min_threshold (float): The minimum weight threshold.
            max_threshold (float): The maximum weight threshold.
            calibration_key (str): The setting key holding this scale's
                calibration factor.
            weight_to_calibrate_key (str): The setting key holding the known
                weight last used to calibrate this scale.
        """
        self.min = min_threshold
        self.max = max_threshold
        self.I2C_ADDR = int(address, 16)
        self.REG_DATA_GET_RAM_DATA = 0x00  # Get sensor raw data
        self.bus = 1
        self.calibration_key = calibration_key
        self.weight_to_calibrate_key = weight_to_calibrate_key
        self.calibration: float = float(settings.get(self.calibration_key))
        self.offset = 0.0
        self.i2cbus = smbus2.SMBus(self.bus)
        self.error = ""
        self.error_message_timer = time_utils.Timer(3600)
        self.i2cbus.write_i2c_block_data(self.I2C_ADDR, 0x01, [0x8C, 0x03])
        self.alarm_timer = time_utils.Timer(3600)
        self.weights_list: list[float] = []
        self.tare()

    # @time_utils.measure_time
    def tare(self) -> None:
        """Tares the scale (sets the current weight as zero)."""
        self.weights_list = []
        try:
            self.offset = self.get_value()
            log.info("The scale has been tared.")
        except Exception:
            log.error("Error taring scale", exception=traceback.format_exc())

    def calibrate(self, weight: float) -> None:
        """Calibrates the scale with a known weight.

        Args:
            weight (float): The known weight in grams used for calibration.
        """
        self.weights_list = []
        try:
            raw_value: float = self.get_value()
            new_calibration = (raw_value - self.offset) / weight
            self.calibration = new_calibration
            settings.set(self.calibration_key, new_calibration)
            settings.set(self.weight_to_calibrate_key, weight)
        except Exception:
            log.error("Error calibrating scale", exception=traceback.format_exc())

    def get_value(self, samples: int = 5, interval_s: float = 0.005) -> int:
        """Reads raw values from the scale.

        Args:
            samples (int): Number of samples to read.
            interval_s (float): Delay between samples in seconds.

        Returns:
            int: The mean of the raw values.
        """
        values: list[int] = []
        for i in range(samples):
            try:
                data = self.i2cbus.read_i2c_block_data(
                    self.I2C_ADDR, self.REG_DATA_GET_RAM_DATA, 2
                )
                v = struct.unpack(">h", bytes(data))[0]
                values.append(v)
            except Exception:
                pass
            if interval_s > 0 and i < samples - 1:
                time.sleep(interval_s)
        if not values:
            if self.alarm_timer.has_elapsed():
                log.alarm("Scale not responding, please check the connection.")
            return 0
        mean = int(np.mean(values))
        return mean

    def get_weight(self) -> float:
        """Gets the current weight in grams.

        Returns:
            float: The weight in grams.
        """
        try:
            value = (self.get_value() - self.offset) / self.calibration
        except Exception:
            if self.error_message_timer.has_elapsed():
                log.error("Error getting weight", exception=traceback.format_exc())
            value = 0.0

        if self.min < value < self.max:
            self.weights_list.append(value)
            if len(self.weights_list) > 8:
                self.weights_list.pop(0)
        else:
            self.weights_list = []
        return round(value, 2)

    def real_weight_inference(self) -> tuple[bool, float]:
        """Determines if a sequence of weight measurements represents a stable weight.

        Conditions to call it a real weight:
        - standard deviation of the last 5 measurements is
            smaller than 10% of the minimum threshold

        Returns:
            tuple[bool, float]: (True, median_weight) if stable, else (False, 0.0).
        """

        if len(self.weights_list) < 8:
            return (False, 0.0)

        median_weight = round(np.median(self.weights_list[-5:]), 2)
        std_weight = np.std(self.weights_list[-5:])

        if std_weight < 0.1 * self.min:
            self.weights_list = []
            return (True, median_weight)
        else:
            return (False, 0.0)


def get_scale(
    address: str,
    min_threshold: float,
    max_threshold: float,
    enabled: bool,
    calibration_key: str = "SCALE_CALIBRATION_VALUE",
    weight_to_calibrate_key: str = "SCALE_WEIGHT_TO_CALIBRATE",
) -> Scale | NullScale:
    """Factory function to initialize the Scale.

    Args:
        address (str): The I2C address of the scale.
        min_threshold (float): The minimum weight threshold for valid measurements.
        max_threshold (float): The maximum weight threshold for valid measurements.
        enabled (bool): Whether this scale is physically present and should be
            initialized at all.
        calibration_key (str): The setting key holding this scale's
            calibration factor.
        weight_to_calibrate_key (str): The setting key holding the known
            weight last used to calibrate this scale.

    Returns:
        Scale | NullScale: An initialized Scale instance or a null scale if
        disabled or on failure.
    """
    if not enabled:
        scale = NullScale()
        scale.error = ""
        return scale
    try:
        scale = Scale(
            address=address,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            calibration_key=calibration_key,
            weight_to_calibrate_key=weight_to_calibrate_key,
        )
        return scale
    except Exception:
        null_scale = NullScale()
        null_scale.error = log.clean_text(
            traceback.format_exc(), "Could not initialize scale"
        )
        return null_scale


scale = get_scale(
    settings.get("SCALE_ADDRESS"),
    float(settings.get("MIN_WEIGHT_THRESHOLD")),
    float(settings.get("MAX_WEIGHT_THRESHOLD")),
    enabled=scale_corridor_enabled,
)

# Thresholds are set directly here rather than read from settings -- adjust
# them by hand for the box scale's actual weight range.
scale_box = get_scale(
    settings.get("SCALE_BOX_ADDRESS"),
    0.0,
    100000.0,
    enabled=scale_box_enabled,
    calibration_key="SCALE_BOX_CALIBRATION_VALUE",
    weight_to_calibrate_key="SCALE_BOX_WEIGHT_TO_CALIBRATE",
)
