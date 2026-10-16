from village.custom_classes.after_session_base import AfterSessionBase
from village.scripts.log import log
from village.scripts.time_utils import time_utils


class AfterSession(AfterSessionBase):
    """Runs every time a session ends, once the animal is back home.

    It keeps the default behavior (super().run() syncs the data to the hard
    drive or the server, depending on SYNC_TYPE in SETTINGS) and adds one
    thing: it measures how long the sync took and, if it took longer than
    SLOW_SYNC_MINUTES, sends an alarm (shown in the events and sent through
    Telegram). A sync that gets slower and slower usually means a network or
    disk problem.

    The system stays in the SYNC state until run() returns, and no new
    session can start meanwhile, so keep it short.
    """

    SLOW_SYNC_MINUTES = 10

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        start = time_utils.now_timestamp()
        super().run()  # remove this line if you don't want the default sync
        minutes = (time_utils.now_timestamp() - start) / 60

        if minutes > self.SLOW_SYNC_MINUTES:
            log.alarm(f"The data sync after the session took {minutes:.0f} min.")
