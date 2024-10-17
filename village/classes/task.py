from pathlib import Path
from threading import Thread
from typing import Any

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
        self.current_trial: int = 0
        self.current_trial_states: list = []
        self.touch_response: list = []
        self.system_name: str = settings.get("SYSTEM_NAME")

        self.info: str = ""

        self.filename: str = ""
        self.sessions_directory: str = ""
        self.raw_session_path: str = ""
        self.session_path: str = ""
        self.session_settings_path: str = ""
        self.video_directory: str = ""
        self.video_path: str = ""
        self.video_data_path: str = ""
        self.settings: dict[str, Any] = {}

        self._process = Thread()
        self._df: pd.DataFrame | None = None
        self._new_df: pd.DataFrame | None = None
        self._force_stop: bool = False
        self._chrono = time_utils.Chrono()

    # OVERWRITE THESE METHODS IN YOUR TASKS
    def start(self) -> None:
        raise TaskError("The method start(self) is required")

    def create_trial(self) -> None:
        raise TaskError("The method create_trial(self) is required")

    def after_trial(self) -> None:
        raise TaskError("The method after_trial(self) is required")

    def close(self) -> None:
        raise TaskError("The method close(self) is required")

    # DO NOT OVERWRITE THESE METHODS
    def test(self, subject: str = "None") -> None:
        self.subject = subject
        self.start()
        self.create_trial()
        self.after_trial()
        self.close()

    def run(self) -> None:
        self.bpod.reconnect()
        self.start()
        while (
            self.current_trial < self.settings["maximum_number_of_trials"]
            and self._chrono.get_seconds() < self.settings["maximum_duration"]
            and not self._force_stop
        ):
            self.bpod.create_state_machine()
            self.create_trial()
            self.bpod.send_and_run_state_machine()
            self.after_trial()
            self.register_values()
            self.current_trial += 1

    def register_values(self) -> None:
        pass

    def disconnect_and_save(self) -> None:
        print("disconnect_and_save")
        self.bpod.stop()
        # kill the screen
        # self.process.join()
        # save the csv
        print("save the csv")
        self.bpod.close()

    @classmethod
    def get_name(cls) -> str:
        name = cls.__name__
        if name == "Task":
            return "None"
        else:
            return name

    def create_paths(self, start_time) -> None:
        self.filename = str(self.subject) + "_" + str(self.name) + "_" + start_time

        self.sessions_directory = str(
            Path(settings.get("SESSIONS_DIRECTORY"), self.subject)
        )
        self.video_directory = str(Path(settings.get("VIDEOS_DIRECTORY"), self.subject))

        self.raw_session_path = str(
            Path(self.sessions_directory, self.filename + "_RAW.csv")
        )
        self.session_path = str(Path(self.sessions_directory, self.filename + ".csv"))
        self.session_settings_path = str(
            Path(self.sessions_directory, self.filename + ".json")
        )

        self.video_path = str(Path(self.video_directory, self.filename + ".avi"))
        self.video_data_path = str(Path(self.video_directory, self.filename + ".csv"))

    # def get_properties(self) -> list[str]:
    #     used_names = [
    #         "bpod",
    #         "name",
    #         "weight",
    #         "current_trial",
    #         "current_trial_states",
    #         "touch_response",
    #         "system_name",
    #         "info",
    #         "subject",
    #         "minimum_duration",
    #         "maximum_duration",
    #         "maximum_number_of_trials",
    #         "filename",
    #         "sessions_directory",
    #         "raw_session_path",
    #         "session_path",
    #         "session_settings_path",
    #         "video_directory",
    #         "video_path",
    #         "video_data_path",
    #         "settings_path",
    #     ]
    #     properties = [
    #         prop
    #         for prop in dir(self)
    #         if not callable(getattr(self, prop))
    #         and not prop.startswith("_")
    #         and prop not in used_names
    #     ]
    #     properties = [
    #         "subject",
    #         "minimum_duration",
    #         "maximum_duration",
    #         "maximum_number_of_trials",
    #     ] + properties
    #     return properties

    # def create_json_settings_file(self) -> None:
    #     if not Path(self.subject_settings_path).exists():
    #         config = {}
    #         for name in self.get_properties():
    #             if hasattr(self, name):
    #                 value = getattr(self, name)
    #                 config[name] = value

    #         with open(self.session_settings_path, "w") as f:
    #             json.dump(settings, f)

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
