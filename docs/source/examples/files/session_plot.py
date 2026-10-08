import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from village.custom_classes.session_plot_base import SessionPlotBase

ROLLING_WINDOW = 10


def _rolling_accuracy(df: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.Series:
    """Fraction correct over a rolling window of trials, counting only
    trials with a real choice (correct/incorrect) -- miss/omission excluded
    so they don't get counted as wrong."""
    valid = df[df["outcome"].isin(["correct", "incorrect"])]
    if valid.empty:
        return pd.Series(dtype=float)
    is_correct = (valid["outcome"] == "correct").astype(float)
    return is_correct.rolling(window, min_periods=1).mean()


class SessionPlot(SessionPlotBase):
    """Works for every task in this project (bpod_1..6, arduino_1..6, and
    the reference/demo tasks) without listing any of them by name: which
    panels get real content is decided purely by which columns after_trial
    registered for that particular task -- a task that doesn't register
    e.g. response_side just gets a blank "not applicable" panel there.
    """

    def __init__(self) -> None:
        super().__init__()

    def create_plot(
        self,
        df: pd.DataFrame,
        weight: float = 0.0,
        width: float = 10,
        height: float = 8,
    ) -> Figure:
        fig, axes = plt.subplots(2, 3, figsize=(width, height))

        task = str(df["task"].iloc[0]) if "task" in df.columns and len(df) else ""
        n_trials = len(df)
        total_water = float(df["water"].sum()) if "water" in df.columns else 0.0
        fig.suptitle(
            f"{task} -- {n_trials} trials, {total_water:.2f} µL water, "
            f"weight {weight:.1f} g"
        )

        trial_index = range(1, n_trials + 1)

        # --- Trial progression over session time ---
        ax = axes[0, 0]
        if "TRIAL_START" in df.columns and n_trials:
            ax.plot(df["TRIAL_START"], trial_index, marker=".")
            ax.set_xlabel("Session time (s)")
        ax.set_ylabel("Cumulative trials")
        ax.set_title("Trial progression")

        # --- Cumulative water ---
        ax = axes[0, 1]
        if "water" in df.columns and n_trials:
            ax.plot(trial_index, df["water"].cumsum(), color="tab:blue")
        ax.set_xlabel("Trial")
        ax.set_ylabel("Water (µL)")
        ax.set_title("Cumulative water")

        # --- Outcome distribution ---
        ax = axes[0, 2]
        if "outcome" in df.columns and n_trials:
            counts = df["outcome"].value_counts()
            ax.bar(counts.index.astype(str), counts.values, color="tab:orange")
            ax.tick_params(axis="x", rotation=30)
        else:
            ax.text(0.5, 0.5, "no outcome data", ha="center", va="center")
            ax.axis("off")
        ax.set_title("Outcomes")

        # --- Rolling accuracy ---
        ax = axes[1, 0]
        if "outcome" in df.columns:
            acc = _rolling_accuracy(df)
            if not acc.empty:
                ax.plot(acc.index + 1, acc.values, color="tab:green")
                ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
                ax.set_ylim(0, 1)
            else:
                ax.text(0.5, 0.5, "no choice trials", ha="center", va="center")
        else:
            ax.text(0.5, 0.5, "no outcome data", ha="center", va="center")
            ax.axis("off")
        ax.set_xlabel("Trial")
        ax.set_title(f"Rolling accuracy (window={ROLLING_WINDOW})")

        # --- Left / right balance (tasks 2-6 only) ---
        ax = axes[1, 1]
        side_col = next(
            (c for c in ("response_side", "rewarded_side") if c in df.columns), None
        )
        if side_col is not None and n_trials:
            counts = df[side_col].value_counts()
            ax.bar(counts.index.astype(str), counts.values, color="tab:purple")
        else:
            ax.text(0.5, 0.5, "not applicable", ha="center", va="center")
            ax.axis("off")
        ax.set_title(f"{side_col or 'side'} distribution")

        # --- Delay-task difficulty (task 6 only) ---
        ax = axes[1, 2]
        if "p" in df.columns and n_trials:
            ax.plot(trial_index, df["p"], color="tab:red")
            ax.set_ylim(0, 1)
            ax.set_xlabel("Trial")
        else:
            ax.text(0.5, 0.5, "not applicable", ha="center", va="center")
            ax.axis("off")
        ax.set_title("Difficulty (p)")

        fig.tight_layout()
        return fig
