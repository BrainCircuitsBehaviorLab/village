import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SubjectPlotBase:
    """Base class for generating subject-level summary plots."""

    def __init__(self) -> None:
        """Initializes the SubjectPlotBase instance."""
        self.name = "Subject Plot"

    def create_plot(
        self,
        df: pd.DataFrame,
        summary_df: pd.DataFrame,
        width: float = 10,
        height: float = 8,
    ) -> Figure:
        """Creates a subject summary plot.

        Default behavior is to plot a bar chart of trials per day.
        This method is intended to be overridden by subclasses for custom plots.

        Args:
            df (pd.DataFrame): The subject's detailed data.
            summary_df (pd.DataFrame): A summary DataFrame for the subject.
            width (float, optional): Width of the figure. Defaults to 10.
            height (float, optional): Height of the figure. Defaults to 8.

        Returns:
            Figure: The generated matplotlib figure.
        """
        fig, ax = plt.subplots(figsize=(width, height))
        df.date.value_counts(sort=False).plot(kind="bar", ax=ax)
        ax.set_title("Subject Plot")
        ax.set_ylabel("Number of trials")
        return fig

