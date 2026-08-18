from datetime import datetime, timedelta
from typing import Union

import pandas as pd
from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from village.scripts import utils
from village.scripts.time_utils import time_utils
from village.settings import settings


def corridor_plot(
    df: pd.DataFrame,
    subjects: list[str],
    width: float,
    height: float,
    ndays: int = 3,
    from_date: Union[str, None, datetime] = None,
    active_states: Union[dict[str, str], None] = None,
) -> Figure:
    """Generates a corridor activity plot for multiple subjects.

    Visualizes subject activity (detections and session times) over a specified
    number of days, with a day/night white/gray background. Hours in which a
    subject is inactive (OFF, or outside its schedule) are overlaid with red
    diagonal hatching; sessions and detections are drawn on top of everything.

    Args:
        df (pd.DataFrame): DataFrame containing activity data.
        subjects (list[str]): List of subject names to include in the plot.
        width (float): Width of the figure in inches.
        height (float): Height of the figure in inches.
        ndays (int, optional): Number of days to plot. Defaults to 3.
        from_date (Union[str, None, datetime], optional): Start date for the plot.
            If None, uses the current time. Defaults to None.
        active_states (Union[dict[str, str], None], optional): Maps subject name
            to its active value ("ON"/"OFF"/schedule string), used to draw the
            red inactive-hours hatching. Missing subjects default to "ON".
            Defaults to None.

    Returns:
        Figure: The generated matplotlib figure.
    """

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
        ax.axvspan(starts_first[i], starts_second[i], color=color_first, zorder=0)

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

    # per-subject overlay: red diagonal hatching over the hours the subject is
    # inactive (OFF -> whole row, schedule -> its inactive hours, ON -> none).
    # sits above the day/night background; sessions/detections sit above this.
    hour_edges = pd.date_range(
        start=pd.Timestamp(start_first).floor("h"),
        end=pd.Timestamp(end) + pd.Timedelta(hours=1),
        freq="h",
    )
    edge_nums = mdates.date2num(hour_edges)
    for subject in subjects:
        active_value = active_states.get(subject, "ON") if active_states else "ON"
        if not isinstance(active_value, str):
            active_value = "ON"
        y0 = y_positions[subject] - 0.5
        # merge consecutive inactive hours into runs, then hatch each run
        inactive_ranges = []
        run_start = None
        for i in range(len(hour_edges) - 1):
            inactive = not utils.is_active_at(active_value, hour_edges[i])
            if inactive and run_start is None:
                run_start = i
            elif not inactive and run_start is not None:
                inactive_ranges.append((run_start, i))
                run_start = None
        if run_start is not None:
            inactive_ranges.append((run_start, len(hour_edges) - 1))
        for a, b in inactive_ranges:
            ax.add_patch(
                Rectangle(
                    (edge_nums[a], y0),
                    edge_nums[b] - edge_nums[a],
                    1.0,
                    facecolor="none",
                    edgecolor="red",
                    hatch="//",
                    linewidth=0,
                    zorder=1,
                )
            )

    # orange: corridor/box not clear (co-occupancy, large detection, box not
    # empty, multiple tags). purple: subject rejected by rules (not active /
    # minimum time between sessions not elapsed).
    detections_x = []
    detections_y = []
    rejections_x = []
    rejections_y = []

    for subject in subjects:
        subject_data = df[df["subject"] == subject]
        active_start = None
        y_pos = y_positions[subject]

        for i, (_, row) in enumerate(subject_data.iterrows()):
            if row["description"].startswith("Subject not"):
                rejections_x.append(row["date"])
                rejections_y.append(y_pos)
            elif row["description"].startswith(("Detection in", "Large", "Multiple")):
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

    ax.scatter(detections_x, detections_y, color="orange", s=3, zorder=3)
    ax.scatter(rejections_x, rejections_y, color="purple", s=3, zorder=3)

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

    # legend outside the axes, to the right, so it never covers data; the axes
    # are shrunk horizontally (right margin) to make room for it
    legend_handles = [
        Patch(facecolor="white", edgecolor="gray", label="day"),
        Patch(facecolor="gray", edgecolor="gray", label="night"),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor="orange",
            markeredgecolor="orange",
            markersize=6,
            label="corridor busy",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor="purple",
            markeredgecolor="purple",
            markersize=6,
            label="not allowed",
        ),
        Line2D([0], [0], color="blue", linewidth=6, label="session"),
        Patch(facecolor="none", hatch="////", label="inactive"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=8,
        frameon=False,
        handlelength=1.5,
        handletextpad=0.6,
        labelspacing=0.8,
    )

    fig.subplots_adjust(left=0.03, right=0.93, top=0.97, bottom=0.1)

    return fig
