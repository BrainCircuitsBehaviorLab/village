import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SessionPlot:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(self, df: pd.DataFrame, df_raw: pd.DataFrame) -> Figure:
        """
        Default plot for the session. Cumulative count of trials by trial start.
        You can override this method in the child class in
        your code repository in order to create a custom plot.
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(kind="line", x="TRIAL_START", y="trial", ax=ax)
        ax.scatter(df["TRIAL_START"], df["trial"], color="red")
        return fig


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


class OnlinePlotFigureManager:
    # TODO: modify this so it receives the data to plot
    """Class to handle creation and management of Matplotlib figures"""

    def __init__(self):
        self.fig = plt.figure(figsize=(10, 8))

    def create_multiplot(self, trial_data: dict) -> Figure:
        self.fig.clear()

        # Create sample data
        # x = np.linspace(0, 10, num_points)
        # y1 = np.sin(x)
        # y2 = np.cos(x)
        # y3 = np.tan(x)

        # Create subplots
        ax1 = self.fig.add_subplot(221)
        ax2 = self.fig.add_subplot(222)
        ax3 = self.fig.add_subplot(223)
        ax4 = self.fig.add_subplot(224)

        # Plot data
        # ax1.plot(x, y1, label="Sine")
        # ax1.set_title("Sine Wave")
        # ax1.grid(True)

        # ax2.plot(x, y2, label="Cosine")
        # ax2.set_title("Cosine Wave")
        ax2.grid(True)

        # ax3.plot(x, y3, label="Tangent")
        # ax3.set_title("Tangent Wave")
        ax3.grid(True)

        # # Combined plot
        # ax4.plot(x, y1, label="Sine")
        # ax4.plot(x, y2, label="Cosine")
        # ax4.set_title("Combined")
        ax4.grid(True)
        # ax4.legend()

        # plot the dict data as text in the first axis,
        # formatted as one key-value pair per line
        ax1.text(
            0.5,
            0.5,
            "\n".join([f"{k}: {v}" for k, v in trial_data.items()]),
            ha="center",
            va="center",
            fontsize=6,
        )

        self.fig.tight_layout()
        return self.fig
