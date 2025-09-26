# runs at the end of each session when the animal is back home
"""
1. It backs up the session data to a remote server using rsync.
2. You can override this class in your project code to implement custom behavior.
"""

from typing import Optional

from village.classes.enums import SyncType
from village.scripts.rsync_to_hard_drive import main as rsync_to_hard_drive
from village.scripts.rsync_to_server import main as rsync_to_server
from village.settings import settings


class AfterSessionBase:
    def __init__(self) -> None:
        self.data_directory = settings.get("DATA_DIRECTORY")
        self.sync_directory = settings.get("SYNC_DIRECTORY")
        self.server_user = settings.get("SERVER_USER")
        self.server_host = settings.get("SERVER_HOST")
        self.maximum_sync_time = settings.get("MAXIMUM_SYNC_TIME")
        self.sync_type = settings.get("SYNC_TYPE")
        try:
            self.port: Optional[int] = int(settings.get("SERVER_PORT"))
        except Exception:
            self.port = None

    def run(self) -> None:
        if self.sync_type == SyncType.HD:
            rsync_to_hard_drive(
                source=self.data_directory,
                destination=self.sync_directory,
                maximum_sync_time=self.maximum_sync_time,
            )
        elif self.sync_type == SyncType.SERVER:
            rsync_to_server(
                source=self.data_directory,
                destination=self.sync_directory,
                remote_user=self.server_user,
                remote_host=self.server_host,
                port=self.port,
                maximum_sync_time=self.maximum_sync_time,
            )


if __name__ == "__main__":
    after_session = AfterSessionBase()
    after_session.run()
