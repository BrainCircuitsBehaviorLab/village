# runs at the end of each session when the animal is back home
"""
1. It backs up the session data to a remote server using rsync.
2. You can override this class in your project code to implement custom behavior.
"""

from typing import Optional

from village.scripts.rsync_to_server import main as rsync_script
from village.settings import settings


class AfterSessionRun:
    def __init__(self) -> None:
        self.data_directory = settings.get("DATA_DIRECTORY")
        self.sync_directory = settings.get("SYNC_DIRECTORY")
        self.server_user = settings.get("SERVER_USER")
        self.server_host = settings.get("SERVER_HOST")
        self.maximum_sync_time = settings.get("MAXIMUM_SYNC_TIME")
        try:
            self.port: Optional[int] = int(settings.get("SERVER_PORT"))
        except Exception:
            self.port = None

    def run(self) -> None:
        rsync_script(
            source=self.data_directory,
            destination=self.sync_directory,
            remote_user=self.server_user,
            remote_host=self.server_host,
            port=self.port,
            maximum_sync_time=self.maximum_sync_time,
        )


if __name__ == "__main__":
    after_session_run = AfterSessionRun()
    after_session_run.run()
