from village.custom_classes.task_base import BpodEvent, TaskBase


class WaterCalibrationTaskBase(TaskBase):
    """Task that runs the sequence behind the Water Calibration panel
    (village/calibration/water_calibration.py): open each of a set of
    valves for its own given time, repeated a number of times, so the
    experimenter can weigh what came out and build a time->volume curve.

    This default implementation drives a Bpod state machine, and is used
    automatically whenever the project's controller is Bpod. For any other
    controller, subclass this in your project's code directory and
    override start()/create_trial()/after_trial()/close() to run the same
    sequence on your own hardware -- e.g. for an Arduino, create_trial()
    would send the valve-open/close commands over serial and wait out each
    time instead of building Bpod states. The __init__ signature below
    (indices, times, maximum_number_of_trials) must stay the same, since
    the calibration panel constructs your class with exactly these
    keyword arguments.

    Args:
        indices (list[int]): 0-based indices of the ports being
            calibrated/tested this run.
        times (list[float]): one valve-open time (seconds) per entry in
            indices, same order.
        maximum_number_of_trials (int): number of times to repeat the
            whole sequence (one repeat = one trial).
    """

    def __init__(
        self,
        indices: list[int],
        times: list[float],
        maximum_number_of_trials: int,
    ) -> None:
        super().__init__()
        self.indices = indices
        self.times = times
        self.maximum_number_of_trials = maximum_number_of_trials

    def start(self) -> None:
        self.states = ["valve" + str(i + 1) for i in self.indices] + ["exit"]
        self.wait_states = ["wait" + str(i + 1) for i in self.indices] + ["exit"]
        self.outputs = [
            [("PWM" + str(i + 1), 255), "Valve" + str(i + 1)] for i in self.indices
        ]

    def create_trial(self) -> None:
        for i in range(len(self.states) - 1):
            self.bpod.add_state(
                state_name=self.states[i],
                state_timer=self.times[i],
                state_change_conditions={BpodEvent.Tup: self.wait_states[i]},
                output_actions=self.outputs[i],
            )
            self.bpod.add_state(
                state_name=self.wait_states[i],
                state_timer=0.1,
                state_change_conditions={BpodEvent.Tup: self.states[i + 1]},
                output_actions=[],
            )

    def after_trial(self) -> None:
        pass

    def close(self) -> None:
        pass
