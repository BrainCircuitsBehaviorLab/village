import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SessionPlotBase:
    def __init__(self) -> None:
        self.name = "Session Plot"

    def create_plot(
        self,
        df: pd.DataFrame,
        weight: float = 0.0,
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
