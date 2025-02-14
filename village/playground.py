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

# import serial

# port = "/dev/ttyAMA0"
# baudrate = 9600

# try:
#     s = serial.Serial(port, baudrate, timeout=1)  # Timeout para evitar bloqueos
#     if s.is_open:
#         print(f"El puerto {port} está abierto y listo para recibir datos.")
#     else:
#         print(f"No se pudo abrir el puerto {port}.")
# except serial.SerialException as e:
#     print(f"Error al acceder al puerto {port}: {e}")


value = "2.0"

print(value)

print(str(value))

print(int(value))

print(str(int(value)))
