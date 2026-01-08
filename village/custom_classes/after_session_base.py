"""
This module runs at the end of each session when the animal is back home.

1. It backs up the session data to a remote server using rsync.
2. You can override this class in your project code to implement custom behavior.
"""

import threading
from typing import Optional

from village.classes.enums import SyncType
from village.scripts.rsync_to_hard_drive import main as rsync_to_hard_drive
from village.scripts.rsync_to_server import main as rsync_to_server
from village.settings import settings


class AfterSessionBase:
    """Base class for operations performed after a session ends.

    This class handles data synchronization (backup) to either a hard drive
    or a remote server based on current settings.
    """

    def __init__(self) -> None:
        """Initializes the AfterSessionBase instance with settings."""
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
        self.cancel_event = threading.Event()

    def run(self) -> None:
        """Executes the post-session logic, primarily data synchronization.

        Checks the SYNC_TYPE setting and initiates either a local or remote rsync.
        """
        if self.sync_type == SyncType.HD:
            rsync_to_hard_drive(
                source=self.data_directory,
                destination=self.sync_directory,
                maximum_sync_time=self.maximum_sync_time,
                cancel_event=self.cancel_event,
            )
        elif self.sync_type == SyncType.SERVER:
            rsync_to_server(
                source=self.data_directory,
                destination=self.sync_directory,
                remote_user=self.server_user,
                remote_host=self.server_host,
                port=self.port,
                maximum_sync_time=self.maximum_sync_time,
                cancel_event=self.cancel_event,
            )


if __name__ == "__main__":
    after_session = AfterSessionBase()
    after_session.run()
