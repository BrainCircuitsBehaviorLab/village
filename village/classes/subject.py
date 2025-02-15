import traceback

import pandas as pd

from village.log import log
from village.scripts import time_utils, utils


class Subject:
    def __init__(self, name: str = "None") -> None:
        self.name: str = name
        self.tag: str = ""
        self.basal_weight: float = 0.0
        self.active: str = "Off"
        self.next_session_time: str = ""
        self.next_settings: str = ""
        self.subject_series: pd.Series | None = None

    def create_from_subject_series(self, auto: bool) -> bool:
        if self.subject_series is not None:
            try:
                self.name = self.subject_series["name"]
                self.tag = self.subject_series["tag"]
                self.basal_weight = self.subject_series["basal_weight"]
                self.active = self.subject_series["active"]
                self.next_session_time = self.subject_series["next_session_time"]
                self.next_settings = self.subject_series["next_settings"]
                if auto:
                    log.info("Subject detected", subject=self.name)
                return True
            except Exception:
                log.alarm(
                    "Invalid data in subjects.csv",
                    exception=traceback.format_exc(),
                )
                return False
        else:
            log.alarm("Invalid data in subjects.csv")
            return False

    def minimum_time_ok(self) -> bool:
        next_session = time_utils.date_from_string(self.next_session_time)
        now = time_utils.now()
        if not utils.is_active(self.active):
            log.info("Subject not active", subject=self.name)
            return False
        elif now > next_session:
            return True
        else:
            log.info(
                "Subject not allowed to enter until " + self.next_session_time,
                subject=self.name,
            )
            return False
