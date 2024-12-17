import pandas as pd
from PyQt5.QtGui import QPixmap


class SessionPlot:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(self, df: pd.DataFrame, df_raw: pd.DataFrame) -> QPixmap:
        return QPixmap()


class SubjectPlot:
    def __init__(self) -> None:
        self.name = "Subject Plot"

    def create_plot(self, df: pd.DataFrame) -> QPixmap:
        return QPixmap()
