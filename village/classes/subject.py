import traceback

import pandas as pd

from village.log import log
from village.time_utils import time_utils


class Subject:
    def __init__(self, name: str = "None") -> None:
        self.date: str = ""
        self.name: str = name
        self.tag: str = ""
        self.basal_weight: float = 0.0
        self.active: bool = False
        self.last_session_ended: str = ""
        self.waiting_period: int = 0
        self.next_session_time: str = ""
        self.next_task: str = ""
        self.next_variables: str = ""
        self.subject_series: pd.Series = pd.Series()

    def get_data_from_subject_series(self) -> bool:
        try:
            self.date = self.subject_series["date"]
            self.name = self.subject_series["name"]
            self.tag = self.subject_series["tag"]
            self.basal_weight = self.subject_series["basal_weight"]
            self.active = self.subject_series["active"]
            self.last_session_ended = self.subject_series["last_session_ended"]
            self.waiting_period = self.subject_series["waiting_period"]
            self.next_session_time = self.subject_series["next_session_time"]
            self.next_task = self.subject_series["next_task"]
            self.next_variables = self.subject_series["next_variables"]
            return True
        except Exception:
            log.error(
                "data incorrectly saved in subjects.csv",
                exception=traceback.format_exc(),
            )
            return False

    def minimum_time_ok(self) -> bool:
        next_session = time_utils.date_from_string(self.next_session_time)
        now = time_utils.now()
        if now > next_session:
            return True
        else:
            return False
