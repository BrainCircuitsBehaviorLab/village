import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class OnlinePlotBase:
    """
    Class to handle creation and management of Matplotlib figures
    to monitor behavioral data in real-time.

    Use this with the variables you are registering in your task,
    that are part of Task.session_df.

    Subclasses should override `create_figure_and_axes` (to create axes) and
    `update_plot` (to draw on existing axes).
    """

    def __init__(self) -> None:
        self.name = "Online Plot"
        self.fig: Figure | None = None
        self.active = False

    def ensure_figure(self, width=10, height=8) -> None:
        if self.fig is None or getattr(self.fig, "canvas", None) is None:
            self.create_figure_and_axes(width, height)

    def close(self) -> None:
        try:
            if self.fig is not None:
                plt.close(self.fig)
        finally:
            self.fig = None
            self.active = False

    def update_canvas(self, df: pd.DataFrame) -> None:
        self.ensure_figure()
        self.update_plot(df)
        try:
            if self.fig is not None and self.fig.canvas is not None:
                self.fig.canvas.draw_idle()
        except Exception:
            pass

    def create_figure_and_axes(self, width=10, height=8) -> None:
        self.fig, self.ax = plt.subplots(figsize=(width, height))

        # self.fig = plt.figure(figsize=(width, height))
        # self.ax1 = self.fig.add_subplot(121)
        # self.ax2 = self.fig.add_subplot(122)

    def update_plot(self, df: pd.DataFrame) -> None:
        """
        This is the method that will be called every time the
        data is updated. You should override this method in your
        child class in your code repository.
        """
        self.ax.clear()

        if df.empty:
            self.ax.set_title("Online Plot (no data)")
            return

        df.plot(kind="scatter", x="TRIAL_START", y="trial", ax=self.ax)
