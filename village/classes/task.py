import json
import traceback
from pathlib import Path
from threading import Thread
from typing import Any

import numpy as np
import pandas as pd

from village.classes.protocols import CameraProtocol, PyBpodProtocol
from village.classes.training import Settings, Training
from village.devices.bpod import bpod
from village.devices.sound_device import sound_device
from village.log import log
from village.pybpodapi.bpod.hardware.events import EventName
from village.pybpodapi.bpod.hardware.output_channels import OutputChannel
from village.scripts import time_utils
from village.settings import settings


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
        self.current_trial: int = 1
        self.current_trial_states: list = []
        self.touch_response: list = []
        self.system_name: str = settings.get("SYSTEM_NAME")
        self.date: str = time_utils.now_string()

        self.cam_box = CameraProtocol()

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
        self.training: Training = Training()
        self.trial_data: dict = {}

        self.process = Thread()
        self.raw_df: pd.DataFrame = pd.DataFrame()
        self.session_df: pd.DataFrame = pd.DataFrame()
        self.subject_df: pd.DataFrame = pd.DataFrame()
        self.force_stop: bool = False
        self.maximum_number_of_trials: int = 100000000
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
    def run_in_thread(self, daemon=True) -> None:
        def test_run():
            self.create_paths()
            self.start()
            while self.current_trial <= self.maximum_number_of_trials:
                self.do_trial()
            self.close()
            self.disconnect_and_save("Manual")

        self.process = Thread(target=test_run, daemon=daemon)
        self.process.start()
        return

    def run(self) -> None:
        self.start()
        while (
            self.current_trial <= self.maximum_number_of_trials
            and self.chrono.get_seconds() < self.settings.maximum_duration
            and not self.force_stop
        ):
            self.do_trial(send_to_cam=True)

    def do_trial(self, send_to_cam: bool = False) -> None:
        self.bpod.create_state_machine()
        if send_to_cam:
            self.cam_box.trial = self.current_trial
        self.create_trial()
        self.bpod.send_and_run_state_machine()
        self.get_trial_data()
        self.after_trial()
        self.register_default_values()
        self.concatenate_trial_data()
        self.current_trial += 1
        return

    def get_trial_data(self) -> None:
        data = self.bpod.session.current_trial.export()
        occurrences = self.bpod.session.current_trial.events_occurrences

        self.trial_data.update(
            {
                "date": self.date,
                "trial": self.current_trial,
                "subject": self.subject,
                "task": self.name,
                "system_name": self.system_name,
                "TRIAL_START": data["Trial start timestamp"],
                "TRIAL_END": max(
                    [
                        max(timestamps)
                        for timestamps in data["Events timestamps"].values()
                    ]
                ),
            }
        )

        for event, timestamps in data["Events timestamps"].items():
            self.trial_data[event] = timestamps

        for state, intervals in data["States timestamps"].items():
            starts = [start for start, _ in intervals]
            ends = [end for _, end in intervals]
            self.trial_data[f"STATE_{state}_START"] = starts
            self.trial_data[f"STATE_{state}_END"] = ends

        self.trial_data["ordered_list_of_events"] = [msg.content for msg in occurrences]

    def concatenate_trial_data(self) -> None:
        self.row_df = pd.DataFrame([self.trial_data])
        self.session_df = pd.concat([self.session_df, self.row_df], ignore_index=True)
        self.trial_data = {}

    def register_value(self, name: str, value: Any) -> None:
        self.bpod.register_value(name, value)
        self.trial_data[name] = value

    def register_default_values(self) -> None:
        self.bpod.register_value("task", self.name)
        self.bpod.register_value("subject", self.subject)
        self.bpod.register_value("system_name", self.system_name)
        self.bpod.register_value("date", self.date)

        # # get all the attributes in self.settings and register them
        # for name in vars(self.settings):
        #     attribute = getattr(self.settings, name)
        #     self.bpod.register_value(name, attribute)

        self.bpod.register_value("TRIAL", None)

    def disconnect_and_save(self, run_mode: str) -> tuple[bool, float, int, int, str]:
        save: bool = False
        duration: float = 0.0
        trials: int = 0
        water: int = 0
        settings_str: str = ""
        self.close()
        sound_device.stop()
        self.bpod.stop()
        self.cam_box.stop_record()
        # TODO kill the screen
        if self.subject != "None":
            try:
                duration, trials, water = self.save_csv(run_mode=run_mode)
                settings_str = self.save_json(run_mode)
                save = True
            except Exception:
                log.alarm(
                    "Error saving the task: " + self.name,
                    subject=self.subject,
                    exception=traceback.format_exc(),
                )
            if save:
                try:
                    self.training.df = self.subject_df
                    self.training.subject = self.subject
                    self.training.last_task = self.name
                    self.training.settings = self.settings
                    self.training.update_training_settings()
                except Exception:
                    save = False
                    log.alarm(
                        "Error updating the training settings for task: " + self.name,
                        subject=self.subject,
                        exception=traceback.format_exc(),
                    )
        self.bpod.close()
        return save, duration, trials, water, settings_str

    def save_json(self, run_mode: str) -> str:

        dictionary: dict[str, Any] = {}

        default_properties_to_save = ["minimum_duration", "maximum_duration"]
        default_properties_to_not_save = [
            "next_task",
            "refractary_period",
            "observations",
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

        dictionary["run_mode"] = run_mode
        dictionary["observations"] = self.settings.observations
        json_string = json.dumps(dictionary)

        with open(self.session_settings_path, "w") as f:
            f.write(json_string)

        return json_string

    def save_csv(self, run_mode: str) -> tuple[float, int, int]:

        duration: float = 0.0
        trials: int = 0
        water: int = 0

        self.raw_df = pd.read_csv(self.rt_session_path, sep=";")

        if self.raw_df.shape[0] > 100000:
            log.alarm(
                "The session file is very large, probably due to"
                + " overdetections in some of the ports",
                subject=self.subject,
            )

        trials = self.raw_df["TRIAL"].iloc[-1]

        if trials > 0:
            non_nan_values = self.raw_df["START"].dropna()

            if not non_nan_values.empty:
                duration = float(non_nan_values.iloc[-1] - non_nan_values.iloc[0])
                duration = round(duration, 4)

            self.raw_df.to_csv(self.raw_session_path, index=None, header=True, sep=";")

            trials = self.session_df.shape[0]

            try:
                water = int(self.session_df["water"].sum())
            except Exception:
                water = 0

            if water == 0:
                log.alarm(
                    "No water was drunk in task: " + self.name, subject=self.subject
                )

            self.session_df["run_mode"] = [run_mode] * self.session_df.shape[0]
            self.session_df.to_csv(self.session_path, header=True, index=False, sep=";")

            try:
                self.subject_df = pd.read_csv(
                    self.subject_path, sep=";", low_memory=False
                )

                self.session_df["session"] = [
                    (int(self.subject_df["session"].iloc[-1]) + 1)
                ] * self.session_df.shape[0]
                self.subject_df = pd.concat(
                    [self.subject_df, self.session_df], sort=True
                )
            except FileNotFoundError:
                self.session_df["session"] = [1] * self.session_df.shape[0]
                self.subject_df = self.session_df

            priority_columns = [
                "session",
                "date",
                "trial",
                "subject",
                "task",
                "system_name",
                "run_mode",
            ]
            reordered_columns = priority_columns + [
                col for col in self.subject_df.columns if col not in priority_columns
            ]
            self.subject_df = self.subject_df[reordered_columns]

            self.subject_df.to_csv(self.subject_path, header=True, index=False, sep=";")

            def safe_to_numeric(series) -> Any:
                try:
                    return pd.to_numeric(series)
                except Exception:
                    return series

            self.subject_df = self.subject_df.apply(safe_to_numeric)
        else:
            log.alarm(
                "No trials were recorded in task: " + self.name, subject=self.subject
            )

        return duration, trials, water

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:

        def make_list(x) -> Any | float | str:
            if x.size <= 1:
                return x
            elif x.isnull().all():
                return np.nan
            else:
                return ",".join([str(x.iloc[i]) for i in range(len(x))])

        df0 = df
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
            and (item[1].startswith("Tup") or item[1].startswith("_Transition"))
        ]
        df4.drop(columns=columns_to_drop, inplace=True)

        columns_to_drop2 = [
            col
            for col in df4.columns
            if isinstance(col, str)
            and (col.startswith("Tup") or col.startswith("_Transition"))
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
        start_time = time_utils.now()
        self.date = time_utils.string_from_date(start_time)
        start_time_str = time_utils.filename_string_from_date(start_time)

        self.filename = str(self.subject) + "_" + str(self.name) + "_" + start_time_str
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

        self.video_path = str(Path(self.video_directory, self.filename + ".mp4"))
        self.video_data_path = str(Path(self.video_directory, self.filename + ".csv"))
        self.subject_path = str(Path(self.sessions_directory, self.subject + ".csv"))
