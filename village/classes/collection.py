import os
import sys
import traceback
from pathlib import Path
from typing import Any, Type, Union

import numpy as np
import pandas as pd

from village.classes.protocols import EventProtocol
from village.classes.training import Training
from village.log import log
from village.scripts import time_utils
from village.settings import settings


class Collection(EventProtocol):
    def __init__(self, name: str, columns: list[str], types: list[Type]) -> None:
        self.name: str = name
        self.columns: list[str] = columns
        self.types: list[Type] = types
        self.dict = {col: t for col, t in zip(self.columns, self.types)}
        self.path: Path = Path(settings.get("DATA_DIRECTORY")) / (name + ".csv")

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as file:
                columns_str: str = ";".join(self.columns) + "\n"
                file.write(columns_str)
        try:
            self.df = pd.read_csv(self.path, dtype=self.dict, sep=";")
        except Exception:
            log.error(
                "error reading from: " + str(self.path),
                exception=traceback.format_exc(),
            )
            sys.exit()

    def add_entry(self, entry: list) -> None:
        entry_str = [
            "" if isinstance(e, float) and np.isnan(e) else str(e) for e in entry
        ]
        new_row = pd.DataFrame([entry_str], columns=self.columns)
        new_row = self.convert_df_to_types(new_row)
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        columns_str: str = ";".join(entry_str) + "\n"
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(columns_str)
        self.check_split_csv()

    @staticmethod
    def convert_with_default(value, target_type: Any) -> Any:
        try:
            return target_type(value)
        except (ValueError, TypeError):
            if target_type == int or target_type == float:
                return 0
            elif target_type == bool:
                return False
            elif target_type == str:
                return ""
            else:
                return value

    def convert_df_to_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col, type in zip(df.columns, self.types):
            df[col] = df[col].apply(lambda x: self.convert_with_default(x, type))
        return df

    def check_split_csv(self) -> None:
        if len(self.df) > 11000:
            first_100000: pd.DataFrame = self.df.head(10000)
            date_str: str = time_utils.now_string_for_filename()
            new_filename: str = self.name + "_" + date_str + ".csv"
            directory: str = settings.get("DATA_DIRECTORY")
            new_path: str = os.path.join(directory, new_filename)
            first_100000.to_csv(new_path, index=False, sep=";")

            last: pd.DataFrame = self.df.tail(len(self.df) - 10000)
            last.to_csv(self.path, index=False, sep=";")

            self.df = last

    def get_last_entry(self, column: str, value: str) -> Union[pd.Series, None]:
        column_df: pd.DataFrame = self.df[self.df[column].astype(str) == value]
        if not column_df.empty:
            return column_df.iloc[-1]
        return None

    def get_first_entry(self, column: str, value: str) -> Union[pd.Series, None]:
        column_df: pd.DataFrame = self.df[self.df[column].astype(str) == value]
        if not column_df.empty:
            return column_df.iloc[0]
        return None

    def change_last_entry(self, column: str, value: Any) -> None:
        last_entry = self.df.iloc[-1]
        last_entry[column] = value
        self.df.iloc[-1] = last_entry
        self.save_from_df()

    def log(self, date: str, type: str, subject: str, description: str) -> None:
        if self.columns == ["date", "type", "subject", "description"]:
            entry = [date, type, subject, description]
            self.add_entry(entry)

    def get_valve_time(self, port: int, water: float) -> float:
        try:
            calibration_df = self.df[self.df["port_number"] == port]
            max_calibration = calibration_df["calibration_number"].max()
            calibration_df = calibration_df[
                calibration_df["calibration_number"] == max_calibration
            ]

            x = calibration_df["time(s)"].values
            y = calibration_df["water_delivered(ul)"].values

            if len(x) == 2:
                coeffs = np.polyfit(x, y, 1)
                a = 0
                b, c = coeffs
            else:
                coeffs = np.polyfit(x, y, 2)
                a, b, c = coeffs

            coeffs_for_root = [a, b, c - water]
            roots = np.roots(coeffs_for_root)

            valid_roots = [root for root in roots if np.isreal(root) and root >= 0]

            if valid_roots:
                return round(float(np.min(valid_roots)), 4)
            else:
                raise Exception
        except Exception:
            text = f"""
            \n\n\t--> WATER CALIBRATION PROBLEM !!!!!!\n
            It is not possible to provide a valid time value
            for a water delivery of {water} ul for the port {port}.\n
            1. Make sure you have calibrated the valves/pumps you are using.\n
            2. Make sure the water you want to give is within calibration range.\n
            3. Ultimately, check water_calibration.csv in 'data'.\n
            """
            raise ValueError(text)

    def get_sound_gain(self, speaker: int, dB: float, freq: int = 0) -> float:
        try:
            calibration_df = self.df[self.df["speaker"] == speaker]
            calibration_df = calibration_df[calibration_df["frequency"] == freq]
            max_calibration = calibration_df["calibration_number"].max()
            calibration_df = calibration_df[
                calibration_df["calibration_number"] == max_calibration
            ]

            x = calibration_df["gain"].values
            y = calibration_df["dB_obtained"].values

            if len(x) == 2:
                coeffs = np.polyfit(x, y, 1)
                a = 0
                b, c = coeffs
            else:
                coeffs = np.polyfit(x, y, 2)
                a, b, c = coeffs

            coeffs_for_root = [a, b, c - dB]
            roots = np.roots(coeffs_for_root)

            valid_roots = [root for root in roots if np.isreal(root) and root >= 0]

            if valid_roots:
                return round(float(np.min(valid_roots)), 4)
            else:
                raise Exception
        except Exception:
            text = f"""
            \n\n\t--> SOUND CALIBRATION PROBLEM !!!!!!\n
            It is not possible to provide a valid gain value
            for a target dB of {dB} for the speaker {speaker} and frequency {freq}.\n
            1. Make sure you have calibrated the frequencies you are using.\n
            2. Make sure the dB you want to obtain is within calibration range.\n
            3. Ultimately, check sound_calibration.csv in 'data'.\n
            """
            raise ValueError(text)

    def save_from_df(self, training: Training = Training()) -> None:
        new_df = self.df_from_df(self.df, training)
        new_df.to_csv(self.path, index=False, sep=";")
        self.df = new_df

    def df_from_df(self, df: pd.DataFrame, training: Training) -> pd.DataFrame:
        new_df = self.convert_df_to_types(df)

        if "next_session_time" in new_df.columns:
            new_df["next_session_time"] = pd.to_datetime(
                new_df["next_session_time"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
            )
            new_df["next_session_time"] = new_df["next_session_time"].fillna(
                time_utils.now()
            )

        for col in new_df.columns:
            if new_df[col].dtype == "datetime64[ns]":
                new_df[col] = new_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        if "active" in new_df.columns:
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            def convert_active(value) -> str:
                value = value.strip()
                if value in ("ON", "On", "on"):
                    return "ON"
                else:
                    days = [day.strip() for day in value.split("-")]
                    if all(day in weekdays for day in days):
                        return "-".join(days)
                    else:
                        return "OFF"

            new_df["active"] = new_df["active"].apply(convert_active)

        if "next_settings" in new_df.columns:
            new_df["next_settings"] = new_df["next_settings"].apply(
                training.get_jsonstring_from_jsonstring
            )

        return new_df
