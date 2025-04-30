import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from numpy.polynomial import Polynomial


def sound_calibration_plot(
    df: pd.DataFrame,
    width: float,
    height: float,
    point: tuple[float, float] | None,
) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))

    speakers = sorted(df["speaker"].unique())
    sounds = sorted(df["sound_name"].unique())

    colors_left = sns.light_palette("green", len(sounds) + 1, reverse=True)[:-1]
    colors_right = sns.light_palette("purple", len(sounds) + 1, reverse=True)[:-1]

    for speaker in speakers:
        subset = df[df["speaker"] == speaker]
        for index, sound in enumerate(sounds):
            subset2 = subset[subset["sound_name"] == sound]
            x = subset2["gain"].values
            y = subset2["dB_obtained"].values
            label = sound

            if speaker == 0:
                color = colors_left[index]
            else:
                color = colors_right[index]

            ax.plot(
                x,
                y,
                marker="o",
                linestyle="None",
                color=color,
                label=label,
            )

            if len(x) == 2:
                poly = Polynomial.fit(x, y, 1).convert()
            elif len(x) > 2:
                poly = Polynomial.fit(x, y, 2).convert()
            else:
                continue

            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = poly(x_fit)
            ax.plot(x_fit, y_fit, linestyle="-", color=color)
            ax.plot(
                [],
                [],
                linestyle="None",
                marker="None",
            )

    if point is not None:
        ax.plot(point[0], point[1], marker="x", color="red", markersize=10)

    ax.set_xlabel("Gain (0-1)", fontsize=7)
    ax.set_ylabel("dB_obtained", fontsize=7)

    ax.tick_params(axis="both", labelsize=6)

    if not df.empty:
        ax.legend(title="Speaker", fontsize=6, title_fontsize=7)

    ax.grid(True)

    return fig
