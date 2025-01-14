import os
import subprocess
import traceback
from pathlib import Path

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


def create_global_csv_for_subject(subject: str, sessions_directory: str) -> None:
    subject_directory = os.path.join(sessions_directory, subject)
    final_path = os.path.join(sessions_directory, subject, subject + ".csv")

    sessions = []
    for file in os.listdir(subject_directory):
        if file.endswith("RAW.csv"):
            continue
        elif file.endswith(".csv"):
            sessions.append(file)

    def extract_datetime(file_name) -> str:
        base_name = str(os.path.basename(file_name))
        datetime = base_name.split("_")[2] + base_name.split("_")[3].split(".")[0]
        return datetime

    sorted_sessions = sorted(sessions, key=extract_datetime)

    dfs: list[pd.DataFrame] = []

    for i, session in enumerate(sorted_sessions):
        df = pd.read_csv(session, sep=";").insert(loc=0, column="session", value=i + 1)
        dfs.append(df)

    final_df = pd.concat(dfs)

    priority_columns = [
        "session",
        "date",
        "trial",
        "subject",
        "task",
        "system_name",
    ]
    reordered_columns = priority_columns + [
        col for col in final_df.columns if col not in priority_columns
    ]
    final_df = final_df[reordered_columns]

    final_df.to_csv(final_path, header=True, index=False, sep=";")


def is_active(value: str) -> bool:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_number = time_utils.now().weekday()
    today = days[weekday_number]

    if value == "ON":
        return True
    elif today in value.split("-"):
        return True
    else:
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
