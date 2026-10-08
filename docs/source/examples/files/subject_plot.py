import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from village.custom_classes.subject_plot_base import SubjectPlotBase


class SubjectPlot(SubjectPlotBase):
    """Subject-level history, built entirely from summary_df (one row per
    session, from sessions_summary.csv: date/weight/task/duration/trials/
    water) -- task-agnostic, so it works the same for every task in this
    project without listing any of them. df (the subject's full per-trial
    history) is only used for the total-trial-count fallback if trials
    ever isn't in summary_df.
    """

    def __init__(self) -> None:
        super().__init__()

    def create_plot(
        self,
        df: pd.DataFrame,
        summary_df: pd.DataFrame,
        width: float = 10,
        height: float = 8,
    ) -> Figure:
        fig, axes = plt.subplots(2, 3, figsize=(width, height))
        sdf = (
            summary_df.sort_values("date")
            if "date" in summary_df.columns
            else summary_df
        )

        # --- Sessions over time ---
        ax = axes[0, 0]
        if "date" in sdf.columns and len(sdf):
            sdf["date"].value_counts().sort_index().plot(kind="bar", ax=ax)
            ax.tick_params(axis="x", rotation=60, labelsize=6)
        ax.set_title("Sessions per day")
        ax.set_ylabel("Sessions")

        # --- Water per session ---
        ax = axes[0, 1]
        if "water" in sdf.columns and len(sdf):
            ax.plot(range(1, len(sdf) + 1), sdf["water"], marker=".", color="tab:blue")
        ax.set_xlabel("Session #")
        ax.set_ylabel("Water (µL)")
        ax.set_title("Water per session")

        # --- Weight over time ---
        ax = axes[0, 2]
        if "weight" in sdf.columns and len(sdf):
            ax.plot(range(1, len(sdf) + 1), sdf["weight"], marker=".", color="tab:red")
        ax.set_xlabel("Session #")
        ax.set_ylabel("Weight (g)")
        ax.set_title("Weight")

        # --- Cumulative trials across sessions ---
        ax = axes[1, 0]
        if "trials" in sdf.columns and len(sdf):
            ax.plot(range(1, len(sdf) + 1), sdf["trials"].cumsum(), color="tab:green")
        elif len(df):
            ax.plot(range(1, len(df) + 1))
        ax.set_xlabel("Session #")
        ax.set_ylabel("Cumulative trials")
        ax.set_title("Trial progression")

        # --- Sessions per task ---
        ax = axes[1, 1]
        if "task" in sdf.columns and len(sdf):
            counts = sdf["task"].value_counts()
            ax.bar(counts.index.astype(str), counts.values, color="tab:orange")
            ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.set_title("Sessions per task")

        # --- Trials per task ---
        ax = axes[1, 2]
        if "task" in sdf.columns and "trials" in sdf.columns and len(sdf):
            totals = sdf.groupby("task")["trials"].sum()
            ax.bar(totals.index.astype(str), totals.values, color="tab:purple")
            ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.set_title("Trials per task")

        has_subject = "subject" in sdf.columns and len(sdf)
        fig.suptitle(str(sdf["subject"].iloc[0]) if has_subject else "")
        fig.tight_layout()
        return fig
