import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SessionPlotFigureManager:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(
        self,
        df: pd.DataFrame,
        width: float = 10,
        height: float = 8,
    ) -> Figure:
        """
        Default plot for the session. Cumulative count of trials by trial start.
        You can override this method in the child class in
        your code repository in order to create a custom plot.
        """
        fig, ax = plt.subplots(figsize=(width, height))
        df.plot(kind="line", x="TRIAL_START", y="trial", ax=ax)
        ax.scatter(df["TRIAL_START"], df["trial"], color="red")
        return fig


class SubjectPlotFigureManager:
    def __init__(self) -> None:
        self.name = "Subject Plot"

    def create_plot(
        self, df: pd.DataFrame, width: float = 10, height: float = 8
    ) -> Figure:
        """
        Default plot for the subject.
        You can override this method in the child class in
        your code repository in order to create a custom plot.
        """
        fig, ax = plt.subplots(figsize=(width, height))
        df.date.value_counts(sort=False).plot(kind="bar", ax=ax)
        ax.set_title("Subject Plot")
        ax.set_ylabel("Number of trials")
        return fig


class OnlinePlotFigureManager:
    """
    Class to handle creation and management of Matplotlib figures
    to monitor behavioral data in real-time.

    Use this with the variables you are registering in your task,
    that are part of Task.session_df.
    """

    def __init__(self) -> None:
        self.name = "Online Plot"
        self.fig = plt.figure(figsize=(10, 8))
        self.ax1 = self.fig.add_subplot(121)
        self.active = False

    def update_canvas(self, df: pd.DataFrame) -> None:
        self.update_plot(df)
        try:
            if hasattr(self.fig, "canvas") and self.fig.canvas is not None:
                self.fig.canvas.draw()
        except Exception:
            pass

    def update_plot(self, df: pd.DataFrame) -> None:
        """
        This is the method that will be called every time the
        data is updated. You should override this method in your
        child class in your code repository.
        """
        self.ax1.clear()
        df.plot(kind="scatter", x="TRIAL_START", y="trial", ax=self.ax1)
