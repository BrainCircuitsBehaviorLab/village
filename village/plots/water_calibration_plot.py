import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure


def water_calibration_plot(
    df: pd.DataFrame,
    width: float,
    height: float,
    point: tuple[float, float] | None,
) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))

    ports = sorted(df["port_number"].unique())
    colors = sns.color_palette("tab10", 8)
    colors = [colors[0]] + colors

    for port in ports:
        subset = df[df["port_number"] == port]
        x = subset["time(s)"].values
        y = subset["water_delivered(ul)"].values

        ax.plot(x, y, marker="o", linestyle="None", color=colors[port], label=f"{port}")

        if len(x) == 2:
            coeffs = np.polyfit(x, y, 1)
            poly = np.poly1d(coeffs)
        elif len(x) > 2:
            coeffs = np.polyfit(x, y, 2)
            poly = np.poly1d(coeffs)
        else:
            continue

        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = poly(x_fit)
        ax.plot(x_fit, y_fit, linestyle="-", color=colors[port])
        ax.plot(
            [],
            [],
            linestyle="None",
            marker="None",
        )

    if point is not None:
        ax.plot(point[0], point[1], marker="x", color="red", markersize=10)

    ax.set_xlabel("Time (s)", fontsize=7)
    ax.set_ylabel("Water Delivered (ul)", fontsize=7)

    ax.tick_params(axis="both", labelsize=6)

    ax.legend(title="Port", fontsize=6, title_fontsize=7)

    ax.grid(True)

    return fig
