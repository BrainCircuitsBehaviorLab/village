import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def water_calibration_plot(df: pd.DataFrame, width: float, height: float) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))
    # df.plot(kind="bar", x=df.columns[0], y=df.columns[1], ax=ax)
    ax.set_xlabel(df.columns[0])
    ax.set_ylabel(df.columns[1])

    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", labelsize=6)
    return fig
