import numpy as np

from village.app.settings import settings
from village.classes.subject import Subject
from village.devices.bpod import bpod


class Task:
    def __init__(self) -> None:
        self.name: str = self.get_name()
        self.subject: str = "None"
        self.weight: float = np.nan
        self.system_name: str = settings.get("SYSTEM_NAME")
        self.process = None
        self.current_trial: int = 0
        self.current_trial_states: list = []
        self.stop_task: bool = False
        self.touch_response: list = []
        self.number_of_trials: int = 100
        self.minimum_duration: float = 1800
        self.maximum_duration: float = 3600
        self.gui_input: list[str] = []
        self.gui_output: list[str] = []

    def test(self, subject: Subject) -> None:
        self.subject = subject.name
        self.start()
        self.create_trial()
        self.after_trial()
        self.close()

    def test_run(self, subject: Subject) -> None:
        self.subject = subject.name
        self.start()
        while self.current_trial < self.number_of_trials:
            bpod.create_state_machine()
            self.create_trial()
            bpod.send_and_run_state_machine()
            self.after_trial()
            self.register_values()
            self.current_trial += 1

        self.close()

    # OVERWRITE THESE METHODS IN YOUR TASK
    def start(self) -> None:
        raise NotImplementedError("This method must be overridden")

    def create_trial(self) -> None:
        raise NotImplementedError("This method must be overridden")

    def after_trial(self) -> None:
        raise NotImplementedError("This method must be overridden")

    def close(self) -> None:
        raise NotImplementedError("This method must be overridden")

    # DO NOT OVERWRITE THESE METHODS
    def send_and_run_state(self) -> None:
        # self.sma.send(self.state)
        return

    def register_values(self) -> None:
        pass

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
