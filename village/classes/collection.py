import os
import sys
import traceback
from pathlib import Path

import pandas as pd

from village.classes.protocols import LogProtocol
from village.settings import settings
from village.utils import utils


class Collection(LogProtocol):
    def __init__(self, name: str, columns: list[str]) -> None:
        self.name: str = name
        self.columns: list[str] = columns
        self.path: Path = Path(settings.get("DATA_DIRECTORY")) / (name + ".csv")

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as file:
                columns_str: str = ",".join(self.columns) + "\n"
                file.write(columns_str)
        try:
            self.df = pd.read_csv(self.path)
        except Exception:
            utils.log(
                "error reading from: " + str(self.path),
                exception=traceback.format_exc(),
            )
            sys.exit()

    def add_entry(self, entry: list[str]) -> None:
        new_row = pd.DataFrame([entry], columns=self.columns)
        self.df = pd.concat([self.df, new_row], ignore_index=True)

        columns_str: str = ",".join(entry) + "\n"

        with open(self.path, "a", encoding="utf-8") as file:
            file.write(columns_str)

        self.check_split_csv()

    def check_split_csv(self) -> None:
        if len(self.df) > 110000:
            first_100000: pd.DataFrame = self.df.head(100000)
            date_str: str = utils.now_string_for_filename()
            new_filename: str = self.name + "_" + date_str + ".csv"
            directory: str = settings.get("DATA_DIRECTORY")
            new_path: str = os.path.join(directory, new_filename)
            first_100000.to_csv(new_path, index=False)

            last: pd.DataFrame = self.df.tail(len(self.df) - 100000)
            last.to_csv(self.path, index=False)

            self.df = last

    def get_last_entry(self, column: str, value: str) -> pd.Series | None:
        column_df: pd.DataFrame = self.df[self.df[column].astype(str) == value]
        if not column_df.empty:
            return column_df.iloc[-1]
        return None

    def get_first_entry(self, column: str, value: str) -> pd.Series | None:
        column_df: pd.DataFrame = self.df[self.df[column].astype(str) == value]
        if not column_df.empty:
            return column_df.iloc[0]
        return None

    def log(self, date: str, type: str, subject: str, description: str) -> None:
        if self.columns == ["date", "type", "subject", "description"]:
            entry = [date, type, subject, description]
            self.add_entry(entry)

    def get_valve_time(self, port: int, volume: str) -> float:
        # TODO
        return 0.01
