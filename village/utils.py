import os

from village.settings import settings


def create_directories():
    data_directory = settings.get("DATA_DIRECTORY")
    sessions_directory = os.path.join(data_directory, "sessions")
    videos_directory = os.path.join(data_directory, "videos")
    user_directory = settings.get("USER_DIRECTORY")
    backup_tasks_directory = settings.get("BACKUP_TASKS_DIRECTORY")
    os.makedirs(data_directory, exist_ok=True)
    os.makedirs(sessions_directory, exist_ok=True)
    os.makedirs(videos_directory, exist_ok=True)
    os.makedirs(user_directory, exist_ok=True)
    os.makedirs(backup_tasks_directory, exist_ok=True)
