import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from PyQt5.QtGui import QPixmap


class SessionPlot:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(self, df: pd.DataFrame, df_raw: pd.DataFrame) -> QPixmap:
        return QPixmap()


class SubjectPlot:
    def __init__(self) -> None:
        self.name = "Subject Plot"

    def create_plot(self, df: pd.DataFrame) -> Figure:
        """
        Default plot for the subject.
        You can override this method in the child class in
        your code repository in order to create a custom plot.
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        df.date.value_counts(sort=False).plot(kind="bar", ax=ax)
        ax.set_title("Subject Plot")
        ax.set_ylabel("Number of trials")
        return fig
