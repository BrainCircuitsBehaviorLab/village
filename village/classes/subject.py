import pandas as pd

from village.utils import utils


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
        self.conditions: str = ""
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
            self.conditions = self.subject_series["conditions"]
            return True
        except Exception as e:
            utils.log("data incorrectly saved in subjects.csv", exception=e)
            return False
