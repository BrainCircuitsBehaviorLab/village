import traceback

import pandas as pd

from village.scripts import utils
from village.scripts.log import log
from village.scripts.time_utils import time_utils


class Subject:
    """Represents a subject in the system, holding its data and state.

    Attributes:
        name (str): Subject's name.
        tag (str): RFID tag.
        basal_weight (float): Basal weight.
        active (str): Active days configuration (e.g., "Mon-Fri", "ON", "OFF").
        next_session_time (str): Timestamp for the next allowed session.
        next_settings (str): Next settings JSON string.
        subject_series (pd.Series | None): The raw pandas Series containing subject data.
    """

    def __init__(self, name: str = "None") -> None:
        """Initializes the Subject.

        Args:
            name (str): The subject name.
        """
        self.name: str = name
        self.tag: str = ""
        self.basal_weight: float = 0.0
        self.active: str = "Off"
        self.next_session_time: str = ""
        self.next_settings: str = ""
        self.subject_series: pd.Series | None = None

    def create_from_subject_series(self, tag: str = "") -> bool:
        """Populates subject data from the internal pandas Series.

        Args:
            tag (str): Optional tag to include in error messages if data is invalid.

        Returns:
            bool: True if data was successfully loaded, False otherwise.
        """
        if self.subject_series is not None:
            try:
                self.name = self.subject_series["name"]
                self.tag = self.subject_series["tag"]
                self.basal_weight = self.subject_series["basal_weight"]
                self.active = self.subject_series["active"]
                self.next_session_time = self.subject_series["next_session_time"]
                self.next_settings = self.subject_series["next_settings"]
                return True
            except Exception:
                if tag == "":
                    text = "Invalid data in subjects.csv"
                else:
                    text = "Invalid data in subjects.csv for tag: " + tag
                log.alarm(text, exception=traceback.format_exc())
                return False
        else:
            log.alarm("Invalid data in subjects.csv")
            return False

    def minimum_time_ok(self) -> bool:
        """Checks if the minimum time between sessions has passed.

        Returns:
            bool: True if the subject is allowed to run, False otherwise.
        """
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

