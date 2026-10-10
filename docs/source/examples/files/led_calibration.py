import numpy as np

from village.classes.enums import ControllerEnum
from village.custom_classes.calibration_base import CalibrationBase
from village.custom_classes.calibration_task_base import CalibrationTaskBase
from village.custom_classes.task_base import BpodEvent
from village.scripts.time_utils import time_utils
from village.settings import settings

LED_ON_SECONDS = 20


class LedCalibrationTask(CalibrationTaskBase):
    """Turns on the LED of one Bpod port at a given intensity for a few
    seconds (one trial with a single state), so it can be measured.

    As a CalibrationTaskBase, it does not appear in the TASKS tab: it is
    launched from the LED CALIBRATION panel.
    """

    def __init__(self, port: int, intensity: int) -> None:
        super().__init__()
        self.port = port
        self.intensity = intensity

    def create_trial(self) -> None:
        self.bpod.add_state(
            state_name="led_on",
            state_timer=LED_ON_SECONDS,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[("PWM" + str(self.port), self.intensity)],
        )


class LedCalibration(CalibrationBase):
    """Relates the port LED intensity (0-255) to the light it gives, measured
    with a light meter, so a task can ask for a brightness in lux instead of
    an intensity value.

    How to calibrate, in the LED CALIBRATION panel of the CALIBRATION tab:
    write the port and the intensity and press TURN ON (the LED stays on for
    LED_ON_SECONDS, only with Bpod), measure the light with a light meter
    where the animal's head would be, write the lux and press ADD. Repeat for
    a few intensities (e.g. 25, 50, 100, 150, 200, 255) and for every port
    you use. Every row is saved in led_calibration.csv, in the system
    directory.

    How to use it in a task:

        intensity = self.calibrations.led_calibration.get_led_intensity(
            port=2, lux=40
        )
    """

    def __init__(self) -> None:
        super().__init__()
        # name: of the attribute in self.calibrations, and of the csv file.
        name = "led_calibration"
        columns = ["date", "port", "led_intensity", "lux"]
        types = [str, int, int, float]
        self.create_data_collection(name=name, columns=columns, types=types)
        self.led_on = False

    @classmethod
    def is_active(cls) -> bool:
        # Show the panel always. Return False to hide it, e.g. when a setting
        # says that the box has no LEDs.
        return True

    def draw(self) -> None:
        """Draws the panel. Rows and columns are those of a 44 x 172 grid."""
        self.layout.create_and_add_label(
            "LED CALIBRATION: intensity (0-255) -> light measured (lux)",
            0,
            0,
            80,
            2,
            "black",
        )
        self.layout.create_and_add_label("Port", 3, 0, 10, 2, "black")
        self.port_edit = self.layout.create_and_add_line_edit(
            "1", 3, 10, 10, 2, lambda text: None
        )
        self.layout.create_and_add_label("Intensity", 6, 0, 10, 2, "black")
        self.intensity_edit = self.layout.create_and_add_line_edit(
            "255", 6, 10, 10, 2, lambda text: None
        )
        self.layout.create_and_add_label("Lux", 9, 0, 10, 2, "black")
        self.lux_edit = self.layout.create_and_add_line_edit(
            "", 9, 10, 10, 2, lambda text: None
        )
        self.layout.create_and_add_button(
            "TURN ON", 6, 22, 14, 2, self.turn_on, "Turn on the LED to measure it"
        )
        self.layout.create_and_add_button(
            "TURN OFF", 6, 38, 14, 2, self.stop_task, "Turn off the LED"
        )
        self.layout.create_and_add_button(
            "ADD", 12, 0, 20, 2, self.add_measurement, "Save this measurement"
        )
        self.status = self.layout.create_and_add_label("", 15, 0, 80, 2, "black")
        self.table = self.layout.create_and_add_label(
            "", 18, 0, 80, 24, "black", bold=False
        )
        self.update_table()

    def read_port_and_intensity(self) -> tuple[int, int] | None:
        try:
            port = int(self.port_edit.text())
            intensity = int(self.intensity_edit.text())
            if not 0 <= intensity <= 255:
                raise ValueError
        except ValueError:
            self.status.setText("Port: integer. Intensity: 0-255.")
            return None
        return port, intensity

    def turn_on(self) -> None:
        if settings.get("BEHAVIOR_CONTROLLER") != ControllerEnum.BPOD:
            self.status.setText("Turning on the LED from here needs Bpod.")
            return
        values = self.read_port_and_intensity()
        if values is None:
            return
        port, intensity = values
        if self.run_task(LedCalibrationTask(port, intensity)):
            self.led_on = True
            self.status.setText(f"LED of port {port} on at {intensity}...")
        else:
            self.status.setText("Wait until the running task finishes.")

    def update_gui(self) -> None:
        """Called periodically: notices when the LED task has finished."""
        if self.led_on and not self.task_running():
            self.led_on = False
            self.status.setText("LED off. Write the lux measured and press ADD.")

    def add_measurement(self) -> None:
        values = self.read_port_and_intensity()
        if values is None:
            return
        port, intensity = values
        try:
            lux = float(self.lux_edit.text())
            if lux < 0:
                raise ValueError
        except ValueError:
            self.status.setText("Lux: a number, 0 or more.")
            return
        self.add_entry([time_utils.now_string(), port, intensity, lux])
        self.status.setText(f"Saved: port {port}, intensity {intensity}, {lux} lux")
        self.lux_edit.setText("")
        self.update_table()

    def update_table(self) -> None:
        df = self.last_measurements()
        lines = ["port   intensity   lux"]
        for row in df.itertuples():
            lines.append(f"{row.port:>4}   {row.led_intensity:>9}   {row.lux:g}")
        self.table.setText("\n".join(lines))

    def last_measurements(self):
        """The calibration in use: for each port and intensity, the last
        measurement (an intensity measured again replaces the old value)."""
        df = self.df.drop_duplicates(["port", "led_intensity"], keep="last")
        return df.sort_values(["port", "led_intensity"])

    def get_led_intensity(self, port: int, lux: float) -> int:
        """Returns the intensity (0-255) that gives `lux` in `port`,
        interpolating between the measured points."""
        df = self.last_measurements()
        df = df[df["port"] == port].sort_values("lux")
        if len(df) < 2 or not df["lux"].min() <= lux <= df["lux"].max():
            raise ValueError(
                f"LED CALIBRATION: cannot give {lux} lux in port {port}. "
                "Measure at least two intensities in that port, around that value."
            )
        return int(round(np.interp(lux, df["lux"], df["led_intensity"])))
