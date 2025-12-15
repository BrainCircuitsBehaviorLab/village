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

    fig, ax = plt.subplots(figsize=(width, height))

    ax.plot(
        df["date"],
        df["temperature"],
        marker="o",
        linestyle="-",
        color="b",
        markersize=4,
    )

    ax.set_title("Temperatures Plot")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature")

    num_labels = min(10, len(df))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=num_labels))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))

    return fig

