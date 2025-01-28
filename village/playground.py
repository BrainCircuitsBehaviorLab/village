# # mypy: ignore-errors
# from village.scripts.parse_bpod_messages import (
#     parse_input_to_tuple_override,
#     parse_output_to_tuple,
#     parse_output_to_tuple_override,
# )

# print("-----------------------------------------------")
# print("Output Code + Output Override")
# print("-----------------------------------------------")
# my_list = [
#     "Valve2Off",
# ]

# for item in my_list:
#     print(item)
#     print(parse_output_to_tuple_override(item))
#     print("")

# print("-----------------------------------------------")
# print("Output Code + Output Bpod + Output Override")
# print("-----------------------------------------------")
# my_list = [
#     "Valve3",
#     "BNC2Low",
#     "BNC1High",
#     ("Serial4", 5),
#     ("Serial1", 56),
#     ("Serial2", 0),
#     ("PWM1", 255),
#     ("PWM2", 0),
#     ("PWM3", 15),
# ]

# for item in my_list:
#     print(item)
#     print(parse_output_to_tuple(item))
#     print(parse_output_to_tuple_override(item))
#     print("")


# print("-----------------------------------------------")
# print("Output Code + Output Bpod")
# print("-----------------------------------------------")
# my_list = [
#     "SoftCode3",
#     "SoftCode98",
#     "GlobalTimer2Trig",
#     "GlobalTimer4Cancel",
#     "GlobalCounter1Reset",
# ]

# for item in my_list:
#     print(item)
#     print(parse_output_to_tuple(item))
#     print("")

# print("-----------------------------------------------")
# print("Input Code + Input Override")
# print("-----------------------------------------------")
# my_list = [
#     "Port3In",
#     "Port8Out",
# ]

# for item in my_list:
#     print(item)
#     print(parse_input_to_tuple_override(item))
#     print("")


import numpy as np
import pandas as pd

from village.manager import manager
from village.scripts import time_utils


@time_utils.measure_time
def get_time_from_water(df: pd.DataFrame, port: int, target_water: float) -> float:

    max_calibration = df["calibration_number"].max()
    calibration_df = df[
        (df["calibration_number"] == max_calibration) & (df["port_number"] == port)
    ]

    x = calibration_df["time(s)"].values
    y = calibration_df["water_delivered(ul)"].values

    if len(x) == 2:
        coeffs = np.polyfit(x, y, 1)
        a, b = coeffs
        c = 0
    else:
        coeffs = np.polyfit(x, y, 2)
        a, b, c = coeffs

    coeffs_for_root = [a, b, c - target_water]
    roots = np.roots(coeffs_for_root)

    valid_roots = [root for root in roots if np.isreal(root) and root >= 0]

    if valid_roots:
        return float(np.min(valid_roots))
    else:
        text = "Check water calibration.csv"
        text += "It is not possible to provide a valid time value for"
        text += "a water delivery of " + str(target_water) + " ul"
        raise ValueError(text)


df = manager.water_calibration.df
port = 1
target_water = 10

time = get_time_from_water(df, port, target_water)

print(time)
