import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def water_calibration_plot(df: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind="bar", x=df.columns[0], y=df.columns[1], ax=ax)
    ax.set_title("Water Calibration Plot")
    ax.set_xlabel(df.columns[0])
    ax.set_ylabel(df.columns[1])
    return fig
