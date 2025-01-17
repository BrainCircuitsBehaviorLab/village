from datetime import timedelta

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from village.scripts import time_utils
from village.settings import settings


def corridor_plot(
    df: pd.DataFrame, subjects: list[str], width: float, height: float
) -> Figure:

    day = time_utils.date_from_setting_string(settings.get("DAYTIME"))
    night = time_utils.date_from_setting_string(settings.get("NIGHTTIME"))

    if day < night:
        first = day
        second = night
        color_first = "white"
        color_second = "gray"
    else:
        first = night
        second = day
        color_first = "gray"
        color_second = "white"

    start_first, start_second = time_utils.one_week_ago_init_times(first, second)
    end = time_utils.tomorrow_init_time(first)

    df["date"] = pd.to_datetime(df["date"])

    df = df[df["date"] >= start_first]

    detections = df[
        (df["description"] == "Subject detected") & (df["subject"].isin(subjects))
    ]

    fig, ax = plt.subplots(figsize=(width, height))

    starts_firsts = [start_first + timedelta(days=i) for i in range(7)]
    start_seconds = [start_second + timedelta(days=i) for i in range(7)]

    for i in range(7):
        # ax.axvspan(starts_firsts[i], end, color=color_second)
        ax.axvspan(starts_firsts[i], start_seconds[i], color=color_first)

    ax.scatter(
        detections["date"], detections["subject"], s=10, c="blue", label="Detections"
    )

    y_positions = {subject: i for i, subject in enumerate(subjects)}

    for subject in subjects:
        subject_data = df[df["subject"] == subject]
        active_start = None
        y_pos = y_positions[subject]

        for _, row in subject_data.iterrows():
            if row["type"] == "START":
                active_start = row["date"]
            elif row["type"] == "END" and active_start:
                ax.plot(
                    [active_start, row["date"]],
                    [y_pos, y_pos],
                    color="orange",
                    linewidth=10,
                )
                active_start = None
            elif row["type"] == "START" and active_start:
                ax.plot(
                    [active_start, active_start + timedelta(minutes=5)],
                    [y_pos, y_pos],
                    color="orange",
                    linewidth=10,
                )
                active_start = row["date"]

    ax.set_xlim(start_first, end)
    ax.set_ylim(-0.5, len(subjects) - 0.5)

    ax.set_xticks(start_seconds)
    ax.set_yticks(len(subjects))
    ax.set_yticklabels(subjects)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m-%d"))
    ax.set_facecolor(color_second)

    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", labelsize=6)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.1)

    return fig
