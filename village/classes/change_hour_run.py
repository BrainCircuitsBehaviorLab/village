# runs when hour changes
"""
1. Sends a heartbeat signal to the server.
2. You can override this class in your project code to implement custom behavior.
"""

from village.scripts.heartbeat_to_server import main as heartbeat_script
from village.settings import settings


class ChangeHourRun:
    def __init__(self) -> None:
        self.server_directory = settings.get("SERVER_DIRECTORY")
        self.remote_user = settings.get("SERVER_USER")
        self.remote_host = settings.get("SERVER_HOST")
        self.port = settings.get("SERVER_PORT")

    def run(self) -> None:
        heartbeat_script(
            destination=self.server_directory,
            remote_user=self.remote_user,
            remote_host=self.remote_host,
            port=self.port,
        )


if __name__ == "__main__":
    change_hour_run = ChangeHourRun()
    change_hour_run.run()
