import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class OnlinePlotBase:
    """Class to handle creation and management of Matplotlib figures to monitor behavioral data in real-time.

    Use this with the variables you are registering in your task,
    that are part of Task.session_df.

    Subclasses should override `create_figure_and_axes` (to create axes) and
    `update_plot` (to draw on existing axes).
    """

    def __init__(self) -> None:
        """Initializes the OnlinePlotBase instance."""
        self.name = "Online Plot"
        self.fig: Figure | None = None
        self.active = False

    def ensure_figure(self, width: int = 10, height: int = 8) -> None:
        """Ensures that the matplotlib figure exists, creating it if necessary.

        Args:
            width (int, optional): Width of the figure in inches. Defaults to 10.
            height (int, optional): Height of the figure in inches. Defaults to 8.
        """
        if self.fig is None or getattr(self.fig, "canvas", None) is None:
            self.create_figure_and_axes(width, height)

    def close(self) -> None:
        """Closes the matplotlib figure and resets the state."""
        try:
            if self.fig is not None:
                plt.close(self.fig)
        finally:
            self.fig = None
            self.active = False

    def update_canvas(self, df: pd.DataFrame) -> None:
        """Updates the plot with new data and redraws the canvas.

        Args:
            df (pd.DataFrame): The dataframe containing the latest session data.
        """
        self.ensure_figure()
        self.update_plot(df)
        try:
            if self.fig is not None and self.fig.canvas is not None:
                self.fig.canvas.draw_idle()
        except Exception:
            pass

    def create_figure_and_axes(self, width: int = 10, height: int = 8) -> None:
        """Creates the figure and axes. Should be overridden by subclasses.

        Args:
            width (int, optional): Width of the figure. Defaults to 10.
            height (int, optional): Height of the figure. Defaults to 8.
        """
        self.fig, self.ax = plt.subplots(figsize=(width, height))

        # self.fig = plt.figure(figsize=(width, height))
        # self.ax1 = self.fig.add_subplot(121)
        # self.ax2 = self.fig.add_subplot(122)

    def update_plot(self, df: pd.DataFrame) -> None:
        """Updates the plot content. Should be overridden by subclasses.

        Args:
            df (pd.DataFrame): The dataframe containing the latest session data.
        """
        self.ax.clear()

        if df.empty:
            self.ax.set_title("Online Plot (no data)")
            return

        df.plot(kind="scatter", x="TRIAL_START", y="trial", ax=self.ax)

