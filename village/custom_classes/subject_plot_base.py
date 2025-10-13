import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class SubjectPlotBase:
    def __init__(self) -> None:
        self.name = "Subject Plot"

    def create_plot(
        self,
        df: pd.DataFrame,
        summary_df: pd.DataFrame,
        width: float = 10,
        height: float = 8,
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
