# runs at the end of each session
"""
1. It backs up the session data to a remote server using rsync.
2. It generates reports and plots (TODO: implement this).
"""

from pathlib import Path

from village.scripts.rsync_to_server import main as rsync_script
from village.settings import settings
# TODO: should we get these from manager????


class AfterSessionRun:
    def __init__(self):
        self.data_dir = settings.get("DATA_DIRECTORY")
        self.destination_dir = settings.get("SERVER_DESTINATION")
        self.remote_user = settings.get("SERVER_USER")
        self.remote_host = settings.get("SERVER_HOST")
        self.port = settings.get("SERVER_PORT")

    def backup_to_server(self):
        # define the destination folder
        project_folder = f"{Path(self.data_dir).parent.name}_data"
        rsync_script(
            source=self.data_dir,
            destination=f"{self.destination_dir}/{project_folder}",
            remote_user=self.remote_user,
            remote_host=self.remote_host,
            port=self.port,
        )

    def run(self):
        self.backup_to_server()
        # TODO: delete data here?
        # TODO: deal with deleted data
        # TODO: make reports


if __name__ == "__main__":
    after_session_run = AfterSessionRun()
    after_session_run.run()
