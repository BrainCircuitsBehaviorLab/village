from pathlib import Path

from village.settings import settings


def create_directories():
    data_directory = Path(settings.get("DATA_DIRECTORY"))
    sessions_directory = data_directory / "sessions"
    videos_directory = data_directory / "videos"
    user_directory = Path(settings.get("USER_DIRECTORY"))
    backup_tasks_directory = Path(settings.get("BACKUP_TASKS_DIRECTORY"))
    data_directory.mkdir(parents=True, exist_ok=True)
    sessions_directory.mkdir(parents=True, exist_ok=True)
    videos_directory.mkdir(parents=True, exist_ok=True)
    user_directory.mkdir(parents=True, exist_ok=True)
    backup_tasks_directory.mkdir(parents=True, exist_ok=True)
