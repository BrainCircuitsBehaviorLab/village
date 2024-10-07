import time
from threading import Thread

import numpy as np
import pandas as pd

from village.classes.protocols import PyBpodProtocol
from village.devices.bpod import bpod
from village.pybpodapi.bpod.hardware.events import EventName
from village.pybpodapi.bpod.hardware.output_channels import OutputChannel

# from village.devices.camera import cam_box
from village.settings import settings
from village.time_utils import time_utils


class TaskError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class Event(EventName):
    pass


class Output(OutputChannel):
    pass


class Task:
    def __init__(self) -> None:
        self.bpod: PyBpodProtocol = bpod
        self.name: str = self.get_name()
        self.subject: str = "None"
        self.weight: float = np.nan
        self.process = Thread(target=self.run_thread, daemon=True)
        self.current_trial: int = 0
        self.current_trial_states: list = []
        self.stop_task: bool = False
        self.touch_response: list = []
        self.maximum_number_of_trials: int = -999
        self.minimum_duration: float = -999
        self.maximum_duration: float = -999
        self.gui_input: list[str] = []
        self.gui_output: list[str] = []
        self.system_name: str = settings.get("SYSTEM_NAME")
        self.df: pd.DataFrame | None = None
        self.new_df: pd.DataFrame | None = None

    def check_variables(self) -> None:
        self.maximum_number_of_trials = int(self.maximum_number_of_trials)
        if self.maximum_number_of_trials == 0:
            self.maximum_number_of_trials = 1000000
        self.minimum_duration = float(self.minimum_duration)
        self.maximum_duration = float(self.maximum_duration)
        if self.maximum_number_of_trials == -999:
            raise TaskError(
                "The variable maximum_number_of_trials is required (must be an integer)"
            )
        if self.minimum_duration == -999:
            raise TaskError(
                "The variable minimum_duration is required (must be a float)"
            )
        if self.maximum_duration == -999:
            raise TaskError(
                "The variable maximum_duration is required (must be a float)"
            )

    def test(self, subject: str = "None") -> None:
        self.subject = subject
        self.check_variables()
        self.start()
        self.create_trial()
        self.after_trial()
        self.close()

    def test_run(self, subject: str = "None") -> None:
        self.subject = subject
        self.check_variables()
        self.start()
        self.process.start()
        self.chrono = time_utils.Chrono()
        while (
            self.chrono.get_seconds() < self.maximum_duration
            and self.process.is_alive()
        ):
            time.sleep(0.1)
        self.stop_and_save_task()

    def run_thread(self) -> None:
        while self.current_trial < self.maximum_number_of_trials:
            self.bpod.create_state_machine()
            self.create_trial()
            self.bpod.send_and_run_state_machine()
            self.after_trial()
            self.register_values()
            self.current_trial += 1

    def run(self, subject: str = "None") -> None:
        self.check_variables()
        self.subject = subject
        self.start()
        while self.current_trial < self.maximum_number_of_trials:
            self.bpod.create_state_machine()
            self.create_trial()
            self.bpod.send_and_run_state_machine()
            self.after_trial()
            self.register_values()
            self.current_trial += 1
        self.close()

    # OVERWRITE THESE METHODS IN YOUR TASK
    def start(self) -> None:
        raise TaskError("The method start(self) is required")

    def create_trial(self) -> None:
        raise TaskError("The method create_trial(self) is required")

    def after_trial(self) -> None:
        raise TaskError("The method after_trial(self) is required")

    def close(self) -> None:
        raise TaskError("The method close(self) is required")

    # DO NOT OVERWRITE THESE METHODS
    def send_and_run_state(self) -> None:
        # self.sma.send(self.state)
        return

    def register_values(self) -> None:
        pass

    def stop_and_save_task(self) -> None:
        self.bpod.kill()
        self.bpod.close()
        # kill the screen
        self.process.join()
        # save the csv

    @classmethod
    def get_name(cls) -> str:
        name = cls.__name__
        if name == "Task":
            return "None"
        else:
            return name

    # def set_and_run(self, subject, subject_name, subject_weight, task_manager):

    #     self.current_trial = 0
    #     self.date = time_utils.now_string()[:10]
    #     cam_box.start_record()

    #     if task_manager is not None:

    #         self.date = task_manager.start[:10]
    #         video_directory = os.path.join(settings.VIDEOS_DIRECTORY, subject_name)

    #         if not os.path.exists(video_directory):
    #             os.mkdir(video_directory)

    #         # cam2.put_state('File' + task_manager.filename)
    #         cam3.put_state("File" + task_manager.filename)
    #         cam4.put_state("File" + task_manager.filename)

    #     else:
    #         # cam2.put_state('active')
    #         cam3.put_state("active")
    #         cam4.put_state("active")
    #         self.date = time_utils.now_string()[:10]

    #     self.process = Thread(target=self.run_thread, args=(trials,), daemon=True)
    #     self.process.start()

    # def run_thread(self, trials):
    #     utils.chrono.reset()
    #     if self.my_bpod is None:

    #         self.my_bpod = bpod.create_Bpod()

    #         if self.my_bpod is None:
    #             telegram_bot.alarm_bpod("error starting task")

    #         self.my_bpod.softcode_handler_function = softcode_handler

    #         while True:

    #             if settings.BOX_NAME == 4:
    #                 if utils.current_trials == utils.control_serials + 5:
    #                     print("alarm serial")
    #                     # telegram_bot.alarm_serials()
    #                     # utils.force_relaunch = True

    #                 if utils.current_trials == utils.control_softcodes + 5:
    #                     print("alarm softcode")
    #                     # telegram_bot.alarm_softcodes()
    #                     # utils.force_relaunch = True

    #             queues.trials.put(self.current_trial)
    #             utils.current_trials = self.current_trial
    #             self.sma = StateMachine(self.my_bpod)
    #             if self.current_trial > 0:
    #                 cam3.put_state(str(self.current_trial))
    #                 cam4.put_state(str(self.current_trial))

    #             self.my_bpod.manual_override(
    #                 Bpod.ChannelTypes.OUTPUT,
    #                 Bpod.ChannelNames.SERIAL,
    #                 channel_number=1,
    #                 value=16,
    #             )

    #             if self.current_trial < trials:
    #                 self.main_loop()
    #             else:
    #                 self.sma.add_state(
    #                     state_name="End",
    #                     state_timer=100,
    #                     state_change_conditions={Bpod.Events.Tup: "exit"},
    #                     output_actions=[],
    #                 )
    #             if len(self.sma.state_names) == 0:
    #                 self.sma.add_state(
    #                     state_name="End",
    #                     state_timer=0,
    #                     state_change_conditions={Bpod.Events.Tup: "exit"},
    #                     output_actions=[],
    #                 )
    #             self.my_bpod.send_state_machine(self.sma)
    #             self.my_bpod.run_state_machine(self.sma)
    #             self.current_trial_states = (
    #                 self.my_bpod.session.current_trial.states_durations
    #             )
    #             self.update_response()
    #             self.after_trial()
    #             self.register_values()
    #             self.current_trial += 1

    # def main_loop(self):
    #     raise NotImplementedError

    # def after_trial(self):
    #     pass

    # def configure_gui(self):
    #     pass

    # def update_response(self):
    #     self.response_x = []
    #     self.response_y = []
    #     response_list = []
    #     while True:
    #         try:
    #             response_list.append(queues.responses.get_nowait())
    #         except:
    #             break
    #     for item in response_list:
    #         try:
    #             self.response_x.append(item[0])
    #             self.response_y.append(item[1])
    #         except IndexError:
    #             pass

    #     self.response_x = ",".join(str(e) for e in self.response_x)
    #     self.response_y = ",".join(str(e) for e in self.response_y)

    # def register_value(self, key, value):
    #     self.my_bpod.register_value(key, value)

    # def register_values(self):
    #     self.my_bpod.register_value("task", self.name)
    #     self.my_bpod.register_value("subject", self.subject)
    #     self.my_bpod.register_value("subject_weight", self.subject_weight)
    #     self.my_bpod.register_value("box", self.box)
    #     self.my_bpod.register_value("date", self.date)

    #     for i in range(len(utils.task.gui_input)):
    #         name = utils.task.gui_input[i]
    #         attribute = getattr(utils.task, name)
    #         self.my_bpod.register_value(name, attribute)

    #     self.my_bpod.register_value("TRIAL", None)
