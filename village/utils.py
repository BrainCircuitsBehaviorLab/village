from pathlib import Path

from village.settings import settings


# TODO: should this function get settings as an input so it can be
# independent of settings initiation?
def create_directories() -> None:
    data_directory = Path(settings.get("DATA_DIRECTORY"))
    sessions_directory = data_directory / "sessions"
    videos_directory = data_directory / "videos"
    user_directory = Path(settings.get("USER_DIRECTORY"))
    backup_tasks_directory = Path(settings.get("BACKUP_TASKS_DIRECTORY"))
    data_directory.mkdir(parents=True, exist_ok=True)  # TODO: exist ok? here and below
    sessions_directory.mkdir(parents=True, exist_ok=True)
    videos_directory.mkdir(parents=True, exist_ok=True)
    user_directory.mkdir(parents=True, exist_ok=True)
    backup_tasks_directory.mkdir(parents=True, exist_ok=True)
