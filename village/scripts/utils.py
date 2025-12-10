import getpass
import logging
import os
import re
import shutil
import subprocess
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLayout
from scipy.interpolate import PchipInterpolator

from village.classes.enums import Active
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import settings


def change_directory_settings(new_path: str) -> None:
    """Update all directory settings based on a new project root path.

    Args:
        new_path (str): The absolute path to the new project root directory.
    """
    system_name = settings.get("SYSTEM_NAME")
    settings.set("PROJECT_DIRECTORY", new_path)
    settings.set("DATA_DIRECTORY", str(Path(new_path, "data")))
    settings.set("SESSIONS_DIRECTORY", str(Path(new_path, "data", "sessions")))
    settings.set("VIDEOS_DIRECTORY", str(Path(new_path, "data", "videos")))
    settings.set("SYSTEM_DIRECTORY", str(Path(new_path, "data", system_name)))
    settings.set("CODE_DIRECTORY", str(Path(new_path, "code")))
    settings.set("MEDIA_DIRECTORY", str(Path(new_path, "media")))


def change_system_directory_settings() -> None:
    """Updates the system directory setting and renames the directory if it changed.

    This handles cases where the SYSTEM_NAME setting might have been updated.
    """
    system_name = settings.get("SYSTEM_NAME")
    data_directory = settings.get("DATA_DIRECTORY")
    old_system_directory = settings.get("SYSTEM_DIRECTORY")
    new_system_directory = str(Path(data_directory, system_name))

    if old_system_directory != new_system_directory:
        try:
            os.rename(old_system_directory, new_system_directory)
        except Exception:
            pass

    settings.set("SYSTEM_DIRECTORY", new_system_directory)


def create_directories() -> None:
    """Create all necessary system directories if they do not exist.

    Uses paths defined in the global settings.
    """
    directory = Path(settings.get("PROJECT_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("DATA_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("SESSIONS_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("VIDEOS_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("SYSTEM_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("CODE_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)
    directory = Path(settings.get("MEDIA_DIRECTORY"))
    directory.mkdir(parents=True, exist_ok=True)


def create_directories_from_path(p: str) -> bool:
    """Creates a standard directory structure rooted at the given path.

    Args:
        p (str): Root path for the new directory structure.

    Returns:
        bool: True if successful, False if an exception occurred.
    """
    try:
        path = Path(p)
        path.mkdir(parents=True, exist_ok=True)
        data = Path(path, "data")
        data.mkdir(parents=True, exist_ok=True)
        sessions = Path(data, "sessions")
        sessions.mkdir(parents=True, exist_ok=True)
        videos = Path(data, "videos")
        videos.mkdir(parents=True, exist_ok=True)
        system = Path(data, settings.get("SYSTEM_NAME"))
        system.mkdir(parents=True, exist_ok=True)
        code = Path(path, "code")
        code.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def download_github_repositories(repositories: list[str]) -> None:
    """Clone a list of GitHub repositories into the user's village_projects directory.

    If a repository already exists and is not empty, it is skipped.
    Updates the 'GITHUB_REPOSITORIES_DOWNLOADED' setting upon success.

    Args:
        repositories (list[str]): A list of GitHub repository URLs.
    """
    if settings.get("GITHUB_REPOSITORIES_DOWNLOADED") == Active.ON:
        return
    downloaded_demo = False
    downloaded_all = True
    base_dir = Path("/home", getpass.getuser(), "village_projects")
    base_dir.mkdir(parents=True, exist_ok=True)

    for repository in repositories:
        name = repository.rstrip("/").split("/")[-1]
        name = re.sub(r"\.git$", "", name)
        base_dir2 = Path(base_dir, name)
        directory = Path(base_dir2, "code")
        if directory.exists() and any(directory.iterdir()):
            continue
        directory.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ["git", "clone", repository, str(directory)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                log.info("Repository " + repository + " downloaded")
                if directory == Path(settings.get("DEFAULT_CODE_DIRECTORY")):
                    downloaded_demo = True
                continue
            stderr_txt = result.stderr or ""
            downloaded_all = False
            shutil.rmtree(base_dir2, ignore_errors=True)
            log.error(
                "Error downloading repository " + repository,
                exception=stderr_txt,
            )
        except Exception:
            downloaded_all = False
            shutil.rmtree(base_dir2, ignore_errors=True)
            log.error(
                "Error downloading repository " + repository,
                exception=traceback.format_exc(),
            )
    if downloaded_all:
        settings.set("GITHUB_REPOSITORIES_DOWNLOADED", "ON")
    if not downloaded_demo:
        new_path = str(Path(base_dir, "empty-project"))
        change_directory_settings(new_path=new_path)


def is_active_regular(value: str) -> bool:
    """Checks if the current day allows activity based on a simple schedule.

    Args:
        value (str): "ON", "OFF", or a hyphen-separated list of active days
                     (e.g., "Mon-Wed-Fri").

    Returns:
        bool: True if active today, False otherwise.
    """
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
    """Check if a schedule string dictates activity at the current time.

    The value can be "ON", "OFF", or a range of days (e.g., "Mon-Fri").
    Uses DAYTIME and NIGHTTIME settings to determine active hours within those days.

    Args:
        value (str): The schedule string to evaluate.

    Returns:
        bool: True if active right now, False otherwise.
    """
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


def calculate_active_hours(df: pd.DataFrame) -> dict[str, int]:
    """Calculates the total active hours for different entities based on a DataFrame.

    The DataFrame is expected to have 'name' and 'active' columns.

    Args:
        df (pd.DataFrame): Input dataframe with schedule information.

    Returns:
        dict[str, int]: Dictionary mapping names to total active hours.
    """
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
    """Recursively removes all widgets and sub-layouts from a QLayout.

    Args:
        layout (QLayout): The layout to clear.
    """
    for i in reversed(range(layout.count())):
        layoutItem = layout.itemAt(i)
        if layoutItem is not None:
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.deleteLater()
            else:
                if layoutItem.layout() is not None:
                    delete_all_elements_from_layout(layoutItem.layout())


# not used function
def reformat_trial_data(
    data: dict, date: str, trial: int, subject: str, task: str, system_name: str
) -> dict:
    """Reformats raw trial data into a flattened dictionary structure.

    Args:
        data (dict): Raw data dictionary containing events and states.
        date (str): Date string.
        trial (int): Trial number.
        subject (str): Subject identifier.
        task (str): Task identifier.
        system_name (str): System name.

    Returns:
        dict: Flattened dictionary including formatted start/end times.
    """

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


# not used function
def transform_raw_to_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms raw Bpod trial data into a clean, wide-format DataFrame.

    Processes MSG, START, and END columns to create specific start/end columns
    for each message type.

    Args:
        df (pd.DataFrame): Raw input DataFrame.

    Returns:
        pd.DataFrame: Cleaned and pivoted DataFrame.
    """

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


def setup_logging(logs_subdirectory: str) -> tuple[str, logging.FileHandler]:
    """Configure the logging system to write to a timestamped file.
    Creates the log directory if needed, resets existing handlers, and suppresses
    verbose logs from external libraries (urllib3, telegram, etc.).

    Args:
        logs_subdirectory (str): The name of the subdirectory in the system folder
            where logs should be stored.

    Returns:
        tuple[str, logging.FileHandler]: A tuple containing the log filename and
            the created FileHandler instance.
    """
    data_dir = settings.get("SYSTEM_DIRECTORY")
    logs_dir = os.path.join(data_dir, logs_subdirectory)

    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)

    # Setup logging with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"{timestamp}.log")

    # Reset root logger to prevent duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create File Handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Suppress unwanted logs from external modules
    for unwanted_logger in [
        "urllib3",
        "requests",
        "telegram",
        "telegram.request",
        "telegram.request.BaseRequest",
        "telegram.request.HTTPXRequest",
        "telegram.ext",
        "httpx",
    ]:
        log = logging.getLogger(unwanted_logger)
        log.setLevel(logging.WARNING)
        log.propagate = False  # Prevents logs from bubbling up to the root logger
    
    return log_filename, file_handler


def has_low_disk_space(threshold_gb=10) -> bool:
    """Checks if the root partition has low disk space.

    Args:
        threshold_gb (int, optional): The threshold in GB. Defaults to 10.

    Returns:
        bool: True if free space is below the threshold, False otherwise.
    """
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024**3)
    return free_gb < threshold_gb


def interpolate(x: Any, y: Any, points: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Perform PCHIP interpolation on specific data points.

    Sorts the data, averages y-values for duplicate x-values, and generates
    interpolated points.

    Args:
        x (Any): Input x coordinates (array-like).
        y (Any): Input y coordinates (array-like).
        points (int, optional): Number of interpolated points to generate. Defaults to 100.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple (x_fit, y_fit) of interpolated arrays,
        or (None, None) if insufficient data points.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    order = np.argsort(x)
    x_sorted = x[order]
    y_sorted = y[order]

    x_unique, indices = np.unique(x_sorted, return_inverse=True)
    y_avg = np.zeros_like(x_unique, dtype=float)

    for i in range(len(x_unique)):
        y_avg[i] = y_sorted[indices == i].mean()

    if len(x_unique) < 2:
        return None, None

    f = PchipInterpolator(x_unique, y_avg)

    x_fit = np.linspace(min(x_unique), max(x_unique), points)
    y_fit = f(x_fit)

    return x_fit, y_fit


def get_x_value_interp(x: Any, y: Any, y_target: float) -> float | None:
    """Find the x-value corresponding to a target y-value using interpolation.

    Useful for finding thresholds (e.g., x value where y crosses 50%).

    Args:
        x (Any): Input x coordinates.
        y (Any): Input y coordinates.
        y_target (float): The target y value to search for.

    Returns:
        float | None: The estimated x value, or None if the target is out of range
        or interpolation fails.
    """

    if y_target < np.min(y) or y_target > np.max(y):
        return None

    x_fit, y_fit = interpolate(x, y, points=1000)

    if x_fit is None:
        return None

    if y_target < np.min(y_fit) or y_target > np.max(y_fit):
        return None

    diffs = np.abs(y_fit - y_target)
    best_idx = int(np.argmin(diffs))

    return round(float(x_fit[best_idx]), 5)


def create_pixmap(fig: Figure) -> QPixmap:
    """Creates a QPixmap from a matplotlib Figure.

    Args:
        fig (Figure): The matplotlib figure.

    Returns:
        QPixmap: The generated QPixmap, or an empty QPixmap if an error occurs.
    """
    try:
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        plt.close(fig)
        return pixmap
    except Exception:
        return QPixmap()

