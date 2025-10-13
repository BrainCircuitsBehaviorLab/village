from village.custom_classes.task import Event, Task


class WaterCalibration(Task):
    def __init__(self) -> None:
        super().__init__()
        self.indices: list[int] = []
        self.times: list[float] = []

    def start(self) -> None:
        self.states = ["valve" + str(i + 1) for i in self.indices] + ["wait"]
        self.outputs = [
            [("PWM" + str(i + 1), 255), "Valve" + str(i + 1)] for i in self.indices
        ]

    def create_trial(self) -> None:
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

    def after_trial(self) -> None:
        pass

    def close(self) -> None:
        pass
