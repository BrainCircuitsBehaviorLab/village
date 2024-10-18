import json
import traceback
from pathlib import Path
from threading import Thread
from typing import Any

import numpy as np
import pandas as pd

from village.classes.protocols import PyBpodProtocol
from village.classes.training import Settings
from village.devices.bpod import bpod
from village.log import log
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
        self.date: str = time_utils.now_string()

        self.info: str = ""

        self.filename: str = ""
        self.sessions_directory: str = ""
        self.raw_session_path: str = ""
        self.session_path: str = ""
        self.session_settings_path: str = ""
        self.video_directory: str = ""
        self.video_path: str = ""
        self.video_data_path: str = ""
        self.subject_path: str = ""
        self.rt_session_path: str = ""
        self.settings: Settings = Settings()

        self.process = Thread()
        self.df: pd.DataFrame = pd.DataFrame()
        self.new_df: pd.DataFrame = pd.DataFrame()
        self.df_all: pd.DataFrame = pd.DataFrame()
        self.force_stop: bool = False
        self.chrono = time_utils.Chrono()

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
        self.create_paths()
        self.bpod.reconnect()
        self.start()
        while (
            self.current_trial < self.settings.maximum_number_of_trials
            and self.chrono.get_seconds() < self.settings.maximum_duration
            and not self.force_stop
        ):
            self.bpod.create_state_machine()
            self.create_trial()
            self.bpod.send_and_run_state_machine()
            self.after_trial()
            self.register_values()
            self.current_trial += 1

    def register_values(self) -> None:
        self.bpod.register_value("task", self.name)
        self.bpod.register_value("subject", self.subject)
        self.bpod.register_value("system_name", self.system_name)
        self.bpod.register_value("date", self.date)

        # get all the attributes in self.settings and register them
        for name in vars(self.settings):
            attribute = getattr(self.settings, name)
            self.bpod.register_value(name, attribute)

        self.bpod.register_value("TRIAL", None)

    def disconnect_and_save(self) -> None:
        self.bpod.stop()
        # TODO kill the screen
        if self.subject != "None":
            try:
                self.save_csv()
                self.save_json()
                # TODO self.save_video()
            except Exception:
                log.alarm(
                    "Error saving the task: " + self.name,
                    subject=self.subject,
                    exception=traceback.format_exc(),
                )
        self.bpod.close()

    def save_json(self) -> None:

        dictionary: dict[str, Any] = {}

        default_properties_to_save = [
            "minimum_duration",
            "maximum_duration",
            "maximum_number_of_trials",
        ]
        default_properties_to_not_save = [
            "next_task",
            "refractary_period",
        ]
        default_properties = default_properties_to_save + default_properties_to_not_save
        extra_properties = [
            prop for prop in vars(self.settings) if prop not in default_properties
        ]
        properties = default_properties_to_save + extra_properties

        for name in properties:
            if hasattr(self.settings, name):
                value = getattr(self.settings, name)
                dictionary[name] = value

        with open(self.session_settings_path, "w") as f:
            json.dump(dictionary, f)

    def save_csv(self) -> None:

        self.df = pd.read_csv(self.rt_session_path, sep=";")

        if self.df.shape[0] > 100000:
            log.alarm(
                """
                      The session file is too big, probably due to
                      overdetections in some of the ports""",
                subject=self.subject,
            )

        if self.df["TRIAL"].iloc[-1] > 1:
            self.df.to_csv(self.raw_session_path, index=None, header=True, sep=";")

            self.new_df = self.transform_df()

            try:
                water = int(self.new_df["water"].iloc[-1])
            except Exception:
                water = 0

            if water == 0:
                log.alarm(
                    "No water was drunk in task: " + self.name, subject=self.subject
                )

            self.new_df.to_csv(self.session_path, header=True, index=False, sep=";")

            try:
                self.df_all = pd.read_csv(self.subject_path, sep=";")

                self.new_df["session"] = [
                    (int(self.df_all["session"].iloc[-1]) + 1)
                ] * self.new_df.shape[0]
                self.df_all = pd.concat([self.df_all, self.new_df], sort=True)
            except FileNotFoundError:
                self.new_df.insert(loc=0, column="session", value=1)
                self.df_all = self.new_df

            self.df_all.to_csv(self.session_path, header=True, index=False, sep=";")

            def safe_to_numeric(series) -> Any:
                try:
                    return pd.to_numeric(series)
                except ValueError:
                    return series

            self.df_all = self.df_all.apply(safe_to_numeric)
        else:
            log.alarm(
                "No trials were recorded in task: " + self.name, subject=self.subject
            )

    def transform_df(self) -> pd.DataFrame:

        def make_list(x) -> Any | float | str:
            if x.size <= 1:
                return x
            elif x.isnull().all():
                return np.nan
            else:
                return ";".join([str(x.iloc[i]) for i in range(len(x))])

        df0 = self.df
        df0["idx"] = range(1, len(df0) + 1)
        df1 = df0.set_index("idx")
        df2 = df1.pivot_table(
            index="TRIAL", columns="MSG", values=["START", "END"], aggfunc=make_list
        )

        df3 = df1.pivot_table(
            index="TRIAL",
            columns="MSG",
            values="VALUE",
            aggfunc=lambda x: x if x.size == 1 else x.iloc[0],
        )
        df4 = pd.concat([df2, df3], axis=1, sort=False)

        columns_to_drop = [
            item
            for item in df4.columns
            if type(item) == tuple
            and (
                item[1].startswith("_Tup")
                or item[1].startswith("_Transition")
                or item[1].startswith("_Global")
                or item[1].startswith("_Condition")
            )
        ]
        df4.drop(columns=columns_to_drop, inplace=True)

        columns_to_drop2 = [
            col
            for col in df4.columns
            if isinstance(col, str)
            and (
                col.startswith("_Tup")
                or col.startswith("_Transition")
                or col.startswith("_Global")
                or col.startswith("_Condition")
            )
        ]
        df4.drop(columns=columns_to_drop2, inplace=True)

        df4.columns = [
            item[1] + "_" + item[0] if type(item) == tuple else item
            for item in df4.columns
        ]

        df4.replace("", np.nan, inplace=True)
        df4.dropna(subset=["TRIAL_END"], inplace=True)
        df4["trial"] = range(1, len(df4) + 1)

        list_of_columns = df4.columns

        start_list = [item for item in list_of_columns if item.endswith("_START")]
        end_list = [item for item in list_of_columns if item.endswith("_END")]
        other_list = [
            item
            for item in list_of_columns
            if item not in start_list and item not in end_list
        ]

        states_list = []
        for item in start_list:
            states_list.append(item)
            for item2 in end_list:
                if item2.startswith(item[:-5]):
                    states_list.append(item2)

        new_list = [
            "date",
            "trial",
            "subject",
            "task",
            "system_name",
            "TRIAL_START",
            "TRIAL_END",
        ]
        new_list += states_list + other_list
        new_list = pd.Series(new_list).drop_duplicates().tolist()

        df4 = df4[new_list]

        return df4

    @classmethod
    def get_name(cls) -> str:
        name = cls.__name__
        if name == "Task":
            return "None"
        else:
            return name

    def create_paths(self) -> None:
        self.date = time_utils.now_string()
        start_time = time_utils.now_string_for_filename()
        self.filename = str(self.subject) + "_" + str(self.name) + "_" + start_time
        self.rt_session_path = str(
            Path(settings.get("SESSIONS_DIRECTORY"), "session.csv")
        )

        directory = Path(settings.get("SESSIONS_DIRECTORY"), self.subject)
        if self.subject != "None":
            directory.mkdir(parents=True, exist_ok=True)
        self.sessions_directory = str(directory)

        directory = Path(settings.get("VIDEOS_DIRECTORY"), self.subject)
        if self.subject != "None":
            directory.mkdir(parents=True, exist_ok=True)
        self.video_directory = str(directory)

        self.raw_session_path = str(
            Path(self.sessions_directory, self.filename + "_RAW.csv")
        )
        self.session_path = str(Path(self.sessions_directory, self.filename + ".csv"))
        self.session_settings_path = str(
            Path(self.sessions_directory, self.filename + ".json")
        )

        self.video_path = str(Path(self.video_directory, self.filename + ".avi"))
        self.video_data_path = str(Path(self.video_directory, self.filename + ".csv"))
        self.subject_path = str(Path(self.sessions_directory, self.subject + ".csv"))

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
