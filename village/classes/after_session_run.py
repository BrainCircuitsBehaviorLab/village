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
        self.data_dir = settings.get("DATA_DIRECTORY")
        self.sync_directory = settings.get("SYNC_DIRECTORY")
        self.remote_user = settings.get("SERVER_USER")
        self.remote_host = settings.get("SERVER_HOST")
        try:
            self.port: Optional[int] = int(settings.get("SERVER_PORT"))
        except ValueError:
            self.port = None
        self.timeout = 1800

    def run(self) -> None:
        rsync_script(
            source=self.data_dir,
            destination=self.sync_directory,
            remote_user=self.remote_user,
            remote_host=self.remote_host,
            port=self.port,
            timeout=self.timeout,
        )


if __name__ == "__main__":
    after_session_run = AfterSessionRun()
    after_session_run.run()
