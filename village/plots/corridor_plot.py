from datetime import datetime, timedelta
from typing import Union

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from village.scripts.time_utils import time_utils
from village.settings import settings


def corridor_plot(
    df: pd.DataFrame,
    subjects: list[str],
    width: float,
    height: float,
    ndays: int = 3,
    from_date: Union[str, None, datetime] = None,
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

    if from_date is None:
        from_date = time_utils.now()
        end = time_utils.tomorrow_init_time(first)
    else:
        if isinstance(from_date, str):
            from_date = time_utils.date_from_string(from_date)
        end = from_date.replace(
            hour=first.hour,
            minute=first.minute,
            second=first.second,
            microsecond=first.microsecond,
        )
    start_first, start_second = time_utils.days_ago_init_times(
        first, second, ndays, time_to_end=from_date
    )

    df["date"] = pd.to_datetime(df["date"])

    df = df[df["date"] >= start_first]

    fig, ax = plt.subplots(figsize=(width, height))

    starts_first = [start_first + timedelta(days=i) for i in range(ndays)]
    starts_second = [start_second + timedelta(days=i) for i in range(ndays)]

    for i in range(ndays):
        ax.axvspan(starts_first[i], starts_second[i], color=color_first)

    min_time = start_first
    max_time = start_first + timedelta(days=ndays + 1)
    min_time = (min_time + timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0
    )
    max_time = max_time.replace(minute=0, second=0, microsecond=0)

    hourly_ticks = pd.date_range(start=min_time, end=max_time, freq="h")

    for tick in hourly_ticks:
        ax.axvline(tick, color="lightgray", linewidth=1)

    y_positions = {subject: i for i, subject in enumerate(subjects)}
    detections_x = []
    detections_y = []

    for subject in subjects:
        subject_data = df[df["subject"] == subject]
        active_start = None
        y_pos = y_positions[subject]

        for i, (_, row) in enumerate(subject_data.iterrows()):
            if row["description"].startswith(
                ("Subject not", "Detection in", "Large", "Multiple")
            ):
                detections_x.append(row["date"])
                detections_y.append(y_pos)
            elif row["type"] == "START":
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

    ax.scatter(detections_x, detections_y, color="orange", s=3)

    ax.set_xlim(start_first, end)
    ax.set_ylim(-0.5, len(subjects) - 0.5)

    # get the unique days in the plot
    unique_days = pd.date_range(start=start_first, end=end, freq="D")
    # make them at midnight
    unique_days = unique_days.map(
        lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    # remove the first
    unique_days = unique_days[unique_days >= start_first]
    # put the ticks there
    ax.set_xticks(unique_days)
    ax.set_yticks(range(len(subjects)))
    ax.set_yticklabels(subjects)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m-%d"))
    ax.set_facecolor(color_second)

    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", labelsize=6)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.1)

    return fig
