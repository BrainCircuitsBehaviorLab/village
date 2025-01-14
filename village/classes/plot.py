import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SessionPlot:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(
        self, df: pd.DataFrame, df_raw: pd.DataFrame, width: float, height: float
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


class SubjectPlot:
    def __init__(self) -> None:
        self.name = "Subject Plot"

    def create_plot(self, df: pd.DataFrame, width: float, height: float) -> Figure:
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

    Use this with the variables you are sending registering in your task,
    that are part of Task.trial_data.
    """

    def __init__(self):
        self.name = "Online Plot"
        self.fig = plt.figure(figsize=(10, 8))
        self.ax1 = self.fig.add_subplot(121)
        self.df = pd.DataFrame()
        self.active = False
        self.columns_to_plot = ["trial", "TRIAL_START"]

    def create_multiplot(self, df: pd.DataFrame) -> Figure:
        try:
            self.df = df[self.columns_to_plot].copy()
            self.make_plot()
            self.fig.tight_layout()
        except Exception:
            self.make_error_plot()

        return self.fig

    def update_plot(self, trial_data: dict) -> None:
        try:
            self.update_df(trial_data)
            self.make_plot()
        except Exception:
            self.make_error_plot()

    def update_df(self, trial_data: dict) -> None:
        # get the same keys from the dictionary
        trial_data = {k: v for k, v in trial_data.items() if k in self.columns_to_plot}
        new_row = pd.DataFrame(data=trial_data, columns=self.df.columns, index=[0])
        self.df = pd.concat([self.df, new_row], ignore_index=True)

    def make_plot(self) -> None:
        self.ax1.clear()
        self.df.plot(kind="scatter", x="TRIAL_START", y="trial", ax=self.ax1)
        self.fig.canvas.draw()

    def make_error_plot(self) -> None:
        self.ax1.clear()
        self.ax1.text(
            0.5,
            0.5,
            "Could not create plot",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax1.transAxes,
        )
        self.fig.canvas.draw()
