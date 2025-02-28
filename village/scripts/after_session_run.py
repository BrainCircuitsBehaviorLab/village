# runs at the end of each session
"""
1. It backs up the session data to a remote cluster using rsync.
2. It generates reports and plots (TODO: implement this).
"""

from village.scripts.backup_to_cluster import main as backup_to_cluster
from village.settings import settings


class AfterSessionRun:
    def __init__(self):
        # TODO: get all this from settings
        self.data_dir = settings["DATA_DIRECTORY"]
        self.destination_dir = "/archive/training_village"
        self.remote_user = "training_village"
        self.remote_host = "cluster"
        self.port = 4022

    def run(self):
        backup_to_cluster(
            source=self.data_dir,
            destination=self.destination_dir,
            remote_user=self.remote_user,
            remote_host=self.remote_host,
            port=self.port,
        )
        # TODO: delete data
        # TODO: deal with deleted data
        # TODO: make reports


if __name__ == "__main__":
    after_session_run = AfterSessionRun()
    after_session_run.run()
