# runs when cycle day/night changes and there is no animal in the behavioural box
"""
1. Deletes the old videos.
2. You can override this class in your project code to implement custom behavior.
"""

from pathlib import Path
from typing import Optional

from village.classes.enums import SyncType
from village.scripts.safe_removal_of_data import main as safe_removal_script
from village.settings import Active, settings


class ChangeCycleBase:
    def __init__(self) -> None:
        self.directory = settings.get("VIDEOS_DIRECTORY")
        self.days = settings.get("DAYS_OF_VIDEO_STORAGE")
        self.safe = settings.get("SAFE_DELETE") == Active.ON
        self.backup_dir = str(Path(settings.get("SYNC_DIRECTORY"), "videos"))
        self.remote_user = settings.get("SERVER_USER")
        self.remote_host = settings.get("SERVER_HOST")
        self.sync_type = settings.get("SYNC_TYPE")
        try:
            self.port: Optional[int] = int(settings.get("SERVER_PORT"))
        except ValueError:
            self.port = None

    def run(self) -> None:
        if self.sync_type == SyncType.HD:
            safe_removal_script(
                directory=self.directory,
                days=self.days,
                safe=self.safe,
                backup_dir=self.backup_dir,
                remote=False,
            )
        elif self.sync_type == SyncType.SERVER:
            safe_removal_script(
                directory=self.directory,
                days=self.days,
                safe=self.safe,
                backup_dir=self.backup_dir,
                remote_user=self.remote_user,
                remote_host=self.remote_host,
                port=self.port,
                remote=True,
            )


if __name__ == "__main__":
    change_cycle = ChangeCycleBase()
    change_cycle.run()
