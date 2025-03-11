from datetime import timedelta

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from village.scripts import time_utils
from village.settings import settings


def corridor_plot(
    df: pd.DataFrame, subjects: list[str], width: float, height: float
) -> Figure:

    subjects = sorted(subjects)

    day = time_utils.time_from_setting_string(settings.get("DAYTIME"))
    night = time_utils.time_from_setting_string(settings.get("NIGHTTIME"))

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

    start_first, start_second = time_utils.days_ago_init_times(first, second, 3)
    end = time_utils.tomorrow_init_time(first)

    df["date"] = pd.to_datetime(df["date"])

    df = df[df["date"] >= start_first]

    detections = df[
        (df["description"] == "Subject detected") & (df["subject"].isin(subjects))
    ]

    # Convert the 'subject' column to a categorical type with the specified order
    detections["subject"] = pd.Categorical(
        detections["subject"], categories=subjects, ordered=True
    )

    # detections["subject"] = detections["subject"].astype("category")
    # detections["subject"] = detections["subject"].cat.set_categories(
    #     subjects, ordered=True
    # )

    fig, ax = plt.subplots(figsize=(width, height))

    starts_first = [start_first + timedelta(days=i) for i in range(3)]
    starts_second = [start_second + timedelta(days=i) for i in range(3)]

    for i in range(3):
        ax.axvspan(starts_first[i], starts_second[i], color=color_first)

    ax.scatter(
        detections["date"], detections["subject"], s=4, c="orange", label="Detections"
    )

    y_positions = {subject: i for i, subject in enumerate(subjects)}

    for subject in subjects:
        subject_data = df[df["subject"] == subject]
        active_start = None
        y_pos = y_positions[subject]

        for i, (_, row) in enumerate(subject_data.iterrows()):
            if row["type"] == "START":
                active_start = row["date"]
                if i == len(subject_data) - 1:
                    ax.plot(
                        [active_start, active_start + timedelta(minutes=5)],
                        [y_pos, y_pos],
                        color="blue",
                        linewidth=10,
                        solid_capstyle="butt",
                    )
            elif row["type"] == "END" and active_start:
                ax.plot(
                    [active_start, row["date"]],
                    [y_pos, y_pos],
                    color="blue",
                    linewidth=10,
                    solid_capstyle="butt",
                )
                active_start = None
            elif row["type"] == "START" and active_start:
                ax.plot(
                    [active_start, active_start + timedelta(minutes=5)],
                    [y_pos, y_pos],
                    color="blue",
                    linewidth=10,
                    solid_capstyle="butt",
                )
                active_start = row["date"]

    ax.set_xlim(start_first, end)
    ax.set_ylim(-0.5, len(subjects) - 0.5)

    ax.set_xticks(starts_second)
    ax.set_yticks(range(len(subjects)))
    ax.set_yticklabels(subjects)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m-%d"))
    ax.set_facecolor(color_second)

    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", labelsize=6)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.1)

    return fig
