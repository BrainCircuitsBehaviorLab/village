# runs at the end of each session
"""
1. It backs up the session data to a remote cluster using rsync.
2. It generates reports and plots (TODO: implement this).
"""

from village.scripts.rsync_to_server import main as rsync_script
from village.settings import settings
from pathlib import Path


class AfterSessionRun:
    def __init__(self):
        self.data_dir = settings["DATA_DIRECTORY"]
        self.destination_dir = settings["CLUSTER_DESTINATION"]
        self.remote_user = settings["CLUSTER_USER"]
        self.remote_host = settings["CLUSTER_HOST"]
        self.port = settings["CLUSTER_PORT"]

    def backup_to_server(self):
        # define the destination folder
        project_folder = Path(self.data_dir).parent + "_data"
        rsync_script(
            source=self.data_dir,
            destination=f"{self.destination_dir}/{project_folder}",
            remote_user=self.remote_user,
            remote_host=self.remote_host,
            port=self.port,
        )

    def run(self):
        self.backup_to_server()
        # TODO: delete data
        # TODO: deal with deleted data
        # TODO: make reports


if __name__ == "__main__":
    after_session_run = AfterSessionRun()
    after_session_run.run()
