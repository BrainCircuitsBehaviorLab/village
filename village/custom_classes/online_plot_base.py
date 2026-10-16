import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class OnlinePlotBase:
    """Class to handle creation and management of Matplotlib figures to monitor
    behavioral data in real-time.

    Use this with the variables you are registering in your task,
    that are part of Task.session_df.

    Subclasses should override `create_figure_and_axes` (to create axes) and
    `update_plot` (to draw on existing axes).

    By default the plot is redrawn when a new trial has finished. Set
    `self.refresh_period` (seconds) in `__init__` to redraw it periodically
    instead, while its window is open (e.g. to show data that change during a
    trial); the redraw then runs in the GUI thread.
    """

    def __init__(self) -> None:
        """Initializes the OnlinePlotBase instance."""
        self.name = "Online Plot"
        self.fig: Figure | None = None
        self.active = False
        self.window_geometry: tuple[int, int, int, int] | None = None
        # Seconds between periodic redraws, or None to redraw only when a new
        # trial has finished
        self.refresh_period: float | None = None

    def create_figure_and_axes(self) -> None:
        """Creates the figure and axes. Should be overridden by subclasses."""
        width = 10
        height = 8
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

    def ensure_figure(self) -> None:
        """Ensures that the matplotlib figure exists, creating it if necessary."""
        if self.fig is None or getattr(self.fig, "canvas", None) is None:
            self.create_figure_and_axes()

    def update_canvas(self, df: pd.DataFrame) -> None:
        """Updates the plot with new data and redraws the canvas.

        Args:
            df (pd.DataFrame): The dataframe containing the latest session data.
        """
        try:
            self.ensure_figure()
            self.update_plot(df)
            if self.fig is not None and self.fig.canvas is not None:
                self.fig.canvas.draw_idle()
        except Exception:
            pass

    def close(self) -> None:
        """Closes the matplotlib figure and resets the state."""
        try:
            if self.fig is not None:
                plt.close(self.fig)
        finally:
            self.fig = None
            self.active = False
