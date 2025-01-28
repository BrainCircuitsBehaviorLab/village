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


from village.manager import manager

port = 1
target_water = 2

time = manager.water_calibration.get_valve_time(port, target_water)

print(time)
