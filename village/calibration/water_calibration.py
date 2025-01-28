from village.classes.task import Event, Task


class WaterCalibration(Task):
    def __init__(self) -> None:
        super().__init__()

        self.info = """

        Water Calibration Task
        -------------------

        Deliver water to each valve for a specified time.
        """
        self.indices: list[int] = []
        self.times: list[float] = []

    def start(self):
        self.states = ["valve" + str(i + 1) for i in self.indices] + ["wait"]
        self.outputs = [
            [("PWM" + str(i + 1), 255), "Valve" + str(i + 1)] for i in self.indices
        ]

    def create_trial(self):

        for i in range(len(self.states) - 1):
            self.bpod.add_state(
                state_name=self.states[i],
                state_timer=self.times[i],
                state_change_conditions={Event.Tup: self.states[i + 1]},
                output_actions=self.outputs[i],
            )

        self.bpod.add_state(
            state_name="wait",
            state_timer=0.1,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        pass

    def close(self):
        pass


if __name__ == "__main__":

    task = WaterCalibration()

    task.indices = [0]
    task.times = [100 / 1000]
    task.maximum_number_of_trials = 100
    task.settings.maximum_duration = 1000

    task.run()
    task.bpod.close()
