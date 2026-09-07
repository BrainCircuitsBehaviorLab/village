from datetime import datetime, timedelta

import pandas as pd
from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from village.scripts import utils
from village.scripts.time_utils import time_utils
from village.settings import settings


def _is_subject_active_during_hour(
    changes: list[tuple[pd.Timestamp, str]],
    hour_start: pd.Timestamp,
    hour_end: pd.Timestamp,
    fallback_value: str,
) -> bool:
    """True if the subject's schedule was active at any point during
    [hour_start, hour_end) -- checked against every distinct schedule value
    that held during that hour: the one already in effect at hour_start, plus
    any changes that happened partway through it. An hour only counts as
    inactive if every one of those values says so for the whole hour.

    Args:
        changes: (timestamp, active_value) pairs for this subject, sorted by
            timestamp ascending (see log.active_changed).
        hour_start: Start of the hour being checked (inclusive).
        hour_end: End of the hour being checked (exclusive).
        fallback_value: Used only if `changes` is empty (no history at all
            for this subject) -- today's live active value.
    """
    candidates = [value for ts, value in changes if hour_start <= ts < hour_end]

    before = [value for ts, value in changes if ts <= hour_start]
    if before:
        candidates.append(before[-1])
    elif changes:
        # No change recorded before this hour, but we do have later ones --
        # best guess is that the earliest known value already applied.
        candidates.append(changes[0][1])
    else:
        # No history at all for this subject -- fall back to today's value.
        candidates.append(fallback_value)

    return any(utils.is_active_at(value, hour_start) for value in candidates)


def corridor_plot(
    df: pd.DataFrame,
    subjects: list[str],
    width: float,
    height: float,
    ndays: int = 3,
    from_date: str | None | datetime = None,
    active_states: dict[str, str] | None = None,
    active_history_df: pd.DataFrame | None = None,
) -> Figure:
    """Generates a corridor activity plot for multiple subjects.

    Visualizes subject activity (detections and session times) over a specified
    number of days, with a day/night white/gray background. Hours in which a
    subject is inactive (OFF, or outside its schedule) are overlaid with red
    diagonal hatching; sessions and detections are drawn on top of everything.

    Args:
        df (pd.DataFrame): DataFrame containing activity data (events.csv).
        subjects (list[str]): List of subject names to include in the plot.
        width (float): Width of the figure in inches.
        height (float): Height of the figure in inches.
        ndays (int, optional): Number of days to plot. Defaults to 3.
        from_date (Union[str, None, datetime], optional): Start date for the plot.
            If None, uses the current time. Defaults to None.
        active_states (Union[dict[str, str], None], optional): Maps subject name
            to its current active value ("ON"/"OFF"/schedule string) -- used
            as a fallback for the hours before any known active_history_df
            entry for that subject, and for subjects missing from it
            entirely. Missing subjects default to "ON". Defaults to None.
        active_history_df (pd.DataFrame | None, optional): Columns "date",
            "subject", "active" (see log.active_changed / data.active_history)
            -- one row per past change to a subject's active schedule, used to
            reconstruct what it actually was at each past hour instead of
            applying active_states retroactively to the whole plotted range.
            Defaults to None (falls back to active_states everywhere, like
            before this parameter existed).

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

    # Per-subject history of active-schedule changes (see log.active_changed
    # / data.active_history), used below to reconstruct what each subject's
    # schedule actually was at any past hour. Not filtered to the plotted
    # window -- a change from before start_first is still what was in effect
    # at its start.
    active_changes: dict[str, list[tuple[pd.Timestamp, str]]] = {}
    if active_history_df is not None and not active_history_df.empty:
        changes_df = active_history_df.copy()
        changes_df["date"] = pd.to_datetime(changes_df["date"])
        changes_df = changes_df.sort_values("date")
        for subject_name, group in changes_df.groupby("subject"):
            active_changes[str(subject_name)] = list(
                zip(group["date"], group["active"], strict=False)
            )

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
        fallback_value = active_states.get(subject, "ON") if active_states else "ON"
        if not isinstance(fallback_value, str):
            fallback_value = "ON"
        changes = active_changes.get(subject, [])
        y0 = y_positions[subject] - 0.5
        # merge consecutive inactive hours into runs, then hatch each run
        inactive_ranges = []
        run_start = None
        for i in range(len(hour_edges) - 1):
            active = _is_subject_active_during_hour(
                changes, hour_edges[i], hour_edges[i + 1], fallback_value
            )
            inactive = not active
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

    # vertical line marking the current moment, if it falls within the
    # plotted range (it won't for a plot of a past date range).
    now = time_utils.now()
    if start_first <= now <= end:
        ax.axvline(now, color="black", linewidth=1.5, zorder=6)

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
        Line2D([0], [0], color="black", linewidth=1.5, label="now"),
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
