import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SessionPlotBase:
    """Base class for generating session summary plots."""

    def __init__(self) -> None:
        """Initializes the SessionPlotBase instance."""
        self.name = "Session Plot"

    def create_plot(
        self,
        df: pd.DataFrame,
        weight: float = 0.0,
        width: float = 10,
        height: float = 8,
    ) -> Figure:
        """Creates a session summary plot.

        Default behavior is to plot the cumulative count of trials by trial start time.
        This method is intended to be overridden by subclasses for custom plots.

        Args:
            df (pd.DataFrame): The session data.
            weight (float, optional): The weight of the subject. Defaults to 0.0.
            width (float, optional): Width of the figure. Defaults to 10.
            height (float, optional): Height of the figure. Defaults to 8.

        Returns:
            Figure: The generated matplotlib figure.
        """
        fig, ax = plt.subplots(figsize=(width, height))
        df.plot(kind="line", x="TRIAL_START", y="trial", ax=ax)
        ax.scatter(df["TRIAL_START"], df["trial"], color="red")
        return fig
