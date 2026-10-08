import matplotlib.pyplot as plt
import pandas as pd

from village.custom_classes.online_plot_base import OnlinePlotBase

ROLLING_WINDOW = 10


def _rolling_accuracy(df: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.Series:
    valid = df[df["outcome"].isin(["correct", "incorrect"])]
    if valid.empty:
        return pd.Series(dtype=float)
    is_correct = (valid["outcome"] == "correct").astype(float)
    return is_correct.rolling(window, min_periods=1).mean()


class OnlinePlot(OnlinePlotBase):
    """Live view of the session currently running: cumulative trial count
    plus a rolling accuracy curve (blank until the task actually registers
    an "outcome" column -- works the same for every task in this project).
    """

    def create_figure_and_axes(self) -> None:
        self.fig = plt.figure(figsize=(10, 5))
        self.ax_trials = self.fig.add_subplot(1, 2, 1)
        self.ax_accuracy = self.fig.add_subplot(1, 2, 2)

    def update_plot(self, df: pd.DataFrame) -> None:
        self.ax_trials.clear()
        self.ax_accuracy.clear()

        if df.empty:
            self.ax_trials.set_title("Online Plot (no data yet)")
            return

        n_trials = len(df)
        trial_index = range(1, n_trials + 1)

        if "TRIAL_START" in df.columns:
            self.ax_trials.plot(df["TRIAL_START"], trial_index, marker=".")
            self.ax_trials.set_xlabel("Session time (s)")
        else:
            self.ax_trials.plot(trial_index, trial_index, marker=".")
            self.ax_trials.set_xlabel("Trial")
        self.ax_trials.set_ylabel("Cumulative trials")
        self.ax_trials.set_title("Trial progression")

        if "outcome" in df.columns:
            acc = _rolling_accuracy(df)
            if not acc.empty:
                self.ax_accuracy.plot(acc.index + 1, acc.values, color="tab:green")
                self.ax_accuracy.axhline(0.5, color="gray", linestyle="--", linewidth=1)
                self.ax_accuracy.set_ylim(0, 1)
            self.ax_accuracy.set_xlabel("Trial")
        else:
            self.ax_accuracy.text(0.5, 0.5, "no outcome data", ha="center", va="center")
            self.ax_accuracy.axis("off")
        self.ax_accuracy.set_title(f"Rolling accuracy (window={ROLLING_WINDOW})")

        self.fig.tight_layout()
