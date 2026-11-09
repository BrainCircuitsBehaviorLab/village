## Calibration Overview

The `CALIBRATION` screen has a dedicated panel for each calibration of the system. A
left-side menu lists every calibration relevant to your current hardware configuration;
selecting an entry opens its panel on the right. The calibrations that keep a table of
measurements (water, sound and your own calibrations) save it in a `.csv` file in
`data/<SYSTEM_NAME>/`, which can also be browsed and plotted from the `DATA` screen.
The camera calibration saves a `.json` file in the same folder, the corridor thresholds
are saved as settings, and the OptoGrid panel does not save anything.

*   **`WATER_CALIBRATION`:** Calibrates the relationship between valve opening time and the volume of water actually delivered, per behavior port, and lets you test a calibration by requesting a target volume. With Bpod it works out of the box; with any other controller, it needs a water calibration task written for that controller. See [Water Calibration](water.md).

*   **`SOUND_CALIBRATION`:** Calibrates speaker output so a requested sound level corresponds to an actual, measured volume. See [Sound Calibration](sound.md).

*   **`CAMERA_CALIBRATION`:** Generates a printable symmetric circle grid used to calibrate the lens distortion of the box camera. See [Camera Calibration](camera.md).

*   **`CORRIDOR_THRESHOLD_CALIBRATION`:** Lets you position the four corridor detection areas and tune their day/night pixel-detection thresholds while previewing the result against a recorded corridor video. See [Corridor Threshold Calibration](thresholds.md).

*   **`OPTOGRID_CALIBRATION`:** [OptoGrid](https://github.com/erlichlab/optogrid) is a wireless, head-mounted optogenetic stimulation device: a 64-µLED array over the brain, controlled over Bluetooth, with an IMU that records head movements. This panel shows a map of its LEDs to compose a selection and checks the device (battery, parameters) over Bluetooth. See [OptoGrid Calibration](optogrid.md).

Besides the built-in calibrations, you can create your own and have them appear here
alongside them — see [Custom Calibrations](../advanced_customization/calibrations.md).
