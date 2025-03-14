import logging
import os
import shutil
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QLayout

from village.log import log
from village.scripts import time_utils
from village.settings import settings


def change_directory_settings(new_path: str) -> None:
    settings.set("PROJECT_DIRECTORY", new_path)
    settings.set("DATA_DIRECTORY", str(Path(new_path, "data")))
    settings.set("SESSIONS_DIRECTORY", str(Path(new_path, "data", "sessions")))
    settings.set("VIDEOS_DIRECTORY", str(Path(new_path, "data", "videos")))
    settings.set("CODE_DIRECTORY", str(Path(new_path, "code")))


def create_directories() -> None:
    directory = Path(settings.get("PROJECT_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("DATA_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("SESSIONS_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("VIDEOS_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("CODE_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)


def create_directories_from_path(p: str) -> bool:
    try:
        path = Path(p)
        path.mkdir(parents=True, exist_ok=True)
        data = Path(path, "data")
        data.mkdir(parents=True, exist_ok=True)
        sessions = Path(data, "sessions")
        sessions.mkdir(parents=True, exist_ok=True)
        videos = Path(data, "videos")
        videos.mkdir(parents=True, exist_ok=True)
        code = Path(path, "code")
        code.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def download_github_repository(repository: str) -> None:
    directory = Path(settings.get("CODE_DIRECTORY"))
    default_directory = Path(settings.get("DEFAULT_CODE_DIRECTORY"))
    if len(os.listdir(directory)) == 0 and directory == default_directory:
        directory.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["git", "clone", repository, directory])
            log.info("Repository " + repository + " downloaded")
        except Exception:
            log.error(
                "Error downloading repository " + repository,
                exception=traceback.format_exc(),
            )


def is_active_regular(value: str) -> bool:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_number = time_utils.now().weekday()
    today = days[weekday_number]

    if value == "ON":
        return True
    elif today in value.split("-"):
        return True
    else:
        return False


def is_active(value: str) -> bool:
    if value == "ON":
        return True
    elif value == "OFF":
        return False

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    now = time_utils.now()
    day_init_time = time_utils.time_from_setting_string(settings.get("DAYTIME"))
    night_init_time = time_utils.time_from_setting_string(settings.get("NIGHTTIME"))
    first_init_time = min([day_init_time, night_init_time])

    active_days = value.split("-")
    active_time_ranges = []

    for day in active_days:
        day_index = days.index(day)
        day_date = time_utils.date_from_previous_weekday(day_index)
        range_24 = time_utils.range_24_hours(day_date, first_init_time)
        active_time_ranges.append(range_24)

    for start_time, end_time in active_time_ranges:
        if start_time <= now <= end_time:
            return True

    return False


def calculate_active_hours(df) -> dict[str, int]:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_number = time_utils.now().weekday()
    today = days[weekday_number]

    result = {}

    for _, row in df.iterrows():
        name = row["name"]
        active = row["active"]

        active_time = 0

        if active != "OFF":
            if active == "ON":
                active_days = "Mon-Tue-Wed-Thu-Fri-Sat-Sun"
            else:
                active_days = active.split("-")

            if weekday_number == 0:
                yesterday = days[6]
                day_before_yesterday = days[5]
            elif weekday_number == 1:
                yesterday = days[0]
                day_before_yesterday = days[6]
            else:
                yesterday = days[weekday_number - 1]
                day_before_yesterday = days[weekday_number - 2]

            if today in active_days:
                time = time_utils.time_since_day_started()
                active_time += int(time.total_seconds() / 3600)
                if yesterday in active_days:
                    active_time += 24
                    if day_before_yesterday in active_days:
                        active_time += 24

        result[name] = active_time

    return result


def delete_all_elements_from_layout(layout: QLayout) -> None:
    for i in reversed(range(layout.count())):
        layoutItem = layout.itemAt(i)
        if layoutItem is not None:
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.deleteLater()
            else:
                if layoutItem.layout() is not None:
                    delete_all_elements_from_layout(layoutItem.layout())


def reformat_trial_data(
    data: dict, date: str, trial: int, subject: str, task: str, system_name: str
) -> dict:

    output = {
        "date": date,
        "trial": trial,
        "subject": subject,
        "task": task,
        "system_name": system_name,
        "TRIAL_START": data["TRIAL_START"],
        "TRIAL_END": max(
            [max(timestamps) for timestamps in data["Events timestamps"].values()]
        ),
    }

    for event, timestamps in data["Events timestamps"].items():
        output[f"{event}_START"] = ",".join(map(str, timestamps))

    for state, intervals in data["States timestamps"].items():
        starts = [start for start, _ in intervals]
        ends = [end for _, end in intervals]
        output[f"STATE_{state}_START"] = ",".join(map(str, starts))
        output[f"STATE_{state}_END"] = ",".join(map(str, ends))

    useful_keys = data.keys() - {
        "Events timestamps",
        "States timestamps",
        "ordered_list_of_events",
    }

    output.update({key: data[key] for key in useful_keys})

    return output


def transform_raw_to_clean(df: pd.DataFrame) -> pd.DataFrame:

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
        item[1] + "_" + item[0] if type(item) == tuple else item for item in df4.columns
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


def setup_logging(logs_subdirectory: str) -> str:
    """Configure logging to both file and console"""
    data_dir = settings.get("DATA_DIRECTORY")
    logs_dir = os.path.join(data_dir, logs_subdirectory)
    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Setup logging with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )
    return log_filename


def has_low_disk_space(threshold_gb=10) -> bool:
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024**3)
    return free_gb < threshold_gb
