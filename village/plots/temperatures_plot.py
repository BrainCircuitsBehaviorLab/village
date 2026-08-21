import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def temperatures_plot(df: pd.DataFrame, width: float, height: float) -> Figure:
    """Generates a plot of temperature data over time.

    Args:
        df (pd.DataFrame): DataFrame containing 'date' and 'temperature' columns.
        width (float): Width of the figure in inches.
        height (float): Height of the figure in inches.

    Returns:
        Figure: The generated matplotlib figure.
    """
    max_data_points = 365 * 24
    if len(df) > max_data_points:
        df = df.iloc[-max_data_points:]

    df["date"] = pd.to_datetime(df["date"])

    fig = plt.figure(figsize=(width, height))
    gs = fig.add_gridspec(2, 2)
    ax_time = fig.add_subplot(gs[0, :])
    ax_hour = fig.add_subplot(gs[1, 0])
    ax_day = fig.add_subplot(gs[1, 1])

    # Top: temperature over time
    ax_time.plot(
        df["date"],
        df["temperature"],
        marker="o",
        linestyle="-",
        color="b",
        markersize=4,
    )
    ax_time.set_title("Temperatures Plot")
    ax_time.set_xlabel("Date")
    ax_time.set_ylabel("Temperature")
    num_labels = min(10, len(df))
    ax_time.xaxis.set_major_locator(
        mdates.AutoDateLocator(minticks=5, maxticks=num_labels)
    )
    ax_time.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))

    # Bottom-left: median +/- IQR per hour of day
    hour = df["date"].dt.hour
    g = df.groupby(hour)["temperature"]
    stats = pd.DataFrame(
        {"median": g.median(), "q1": g.quantile(0.25), "q3": g.quantile(0.75)}
    ).sort_index()
    ax_hour.fill_between(stats.index, stats["q1"], stats["q3"], alpha=0.3, label="IQR")
    ax_hour.plot(stats.index, stats["median"], lw=2, label="Median")
    for _, group in df.groupby(df["date"].dt.date):
        ax_hour.plot(
            group["date"].dt.hour, group["temperature"], color="k", alpha=0.5, lw=0.5
        )
    ax_hour.set_title("Average per hour")
    ax_hour.set_xlabel("Hour")
    ax_hour.set_ylabel("T °C")
    ax_hour.set_xticks(range(24))
    ax_hour.legend()

    # Bottom-right: mean per day
    daily = df.groupby(df["date"].dt.date)["temperature"].mean()
    ax_day.plot(daily.index, daily.values, marker="o", markersize=3, color="b")
    ax_day.set_title("Average per day")
    ax_day.set_xlabel("Date")
    ax_day.set_ylabel("Temperature")
    ax_day.xaxis.set_major_locator(plt.MaxNLocator(6))
    for label in ax_day.get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")

    fig.tight_layout()
    return fig
