import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def weights_plot(df: pd.DataFrame, width: float, height: float) -> Figure:
    if df is None or df.empty:
        fig, _ = plt.subplots(figsize=(width, height))
        return fig

    # Keep only relevant columns
    df = (
        df.loc[:, ["subject", "date", "weight"]]
        .dropna(subset=["subject", "date", "weight"])
        .copy()
    )

    # Parse dates and sort
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values(["subject", "date"])

    subjects = df["subject"].astype(str).unique().tolist()
    n_subjects = len(subjects)

    if n_subjects == 0:
        fig, _ = plt.subplots(figsize=(width, height))
        return fig

    # Compute grid (square-ish, no wasted space)
    cols = math.ceil(math.sqrt(n_subjects))
    rows = math.ceil(n_subjects / cols)

    # Global x/y limits for consistency across subplots
    x_min, x_max = df["date"].min(), df["date"].max()

    q1 = df["weight"].quantile(0.25)
    q3 = df["weight"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    df_clean = df[(df["weight"] >= lower) & (df["weight"] <= upper)].copy()
    y_min, y_max = df_clean["weight"].min(), df_clean["weight"].max()

    fig, axes = plt.subplots(rows, cols, figsize=(width, height), squeeze=False)

    for i, subj in enumerate(subjects):
        r, c = divmod(i, cols)
        ax = axes[r][c]

        sub = df[df["subject"].astype(str) == subj]

        ax.plot(sub["date"], sub["weight"], marker="o", linestyle="-", markersize=3)

        ax.set_title(f"{subj} (n={len(sub)})")
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight")

        # Apply global limits
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        x_range = x_max - x_min
        y_range = y_max - y_min

        if x_range == pd.Timedelta(0):
            x_in = x_min
            x_out = x_max
        else:
            x_in = x_min + x_range * 0.05
            x_out = x_max - x_range * 0.05

        if y_range == 0:
            y_in = y_min
            y_out = y_max
        else:
            y_in = y_min + y_range * 0.05
            y_out = y_max - y_range * 0.05

        ax.set_xticks([x_in, x_out])
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.set_yticks([y_in, y_out])

        xt = ax.get_xticklabels()
        if len(xt) == 2:
            xt[0].set_ha("left")
            xt[1].set_ha("right")

        ax.grid(True, alpha=0.3)

    # Hide unused axes
    total_slots = rows * cols
    for j in range(n_subjects, total_slots):
        r, c = divmod(j, cols)
        axes[r][c].set_visible(False)

    fig.suptitle(f"Weights by Subject (N subjects = {n_subjects})", y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return fig
