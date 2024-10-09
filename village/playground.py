# from village.classes.task import Event, Output, Task


# class Testing(Task):
#     def __init__(self) -> None:
#         super().__init__()

#         self.maximum_number_of_trials = 0  # 0 means infinite (the task finishes)
#         self.minimum_duration = 3  # in seconds (door2 opens, animal can leave)
#         self.maximum_duration = 6  # in seconds (the task finishes)

#     def start(self) -> None:
#         return

#     def create_trial(self) -> None:
#         self.bpod.add_state(
#             state_name="light_off",
#             state_timer=1,
#             state_change_conditions={
#                 Event.Port1In: "light_on",
#                 Event.Tup: "exit",
#             },
#             output_actions=[],
#         )

#         self.bpod.add_state(
#             state_name="light_on",
#             state_timer=1,
#             state_change_conditions={
#                 Event.Port1Out: "light_off",
#                 Event.Tup: "exit",
#             },
#             output_actions=[(Output.PWM2, 255), Output.BNC1High],
#         )

#     def after_trial(self) -> None:
#         return

#     def close(self) -> None:
#         return


# testing = Testing()
# testing.test_run()


# import re


# def parse_message_input(message: str | tuple[str, int]) -> tuple[str, int, int]:
#     # Convert the message to string if it's a tuple
#     msg = str(message)

#     # Pattern for "Port#In" and "Port#Out" (where # is 1-9)
#     port_pattern = re.compile(r"Port([1-9])(In|Out)")

#     # Pattern for "PA1_Port#In" and "PA1_Port#Out" (where # is 1-9)
#     pa1_port_pattern = re.compile(r"PA1_Port([1-9])(In|Out)")

#     # Pattern for "BNC#High" and "BNC#Low" (where # is 1-9)
#     bnc_pattern = re.compile(r"BNC([1-9])(High|Low)")

#     # Pattern for "Wire#High" and "Wire#Low" (where # is 1-9)
#     wire_pattern = re.compile(r"Wire([1-9])(High|Low)")

#     # Pattern for "SerialX_Y" messages (where X is 1-9 and Y is 1-99)
#     serial_pattern = re.compile(r"Serial([1-9])_([1-9][0-9]?)")

#     # Pattern for "SoftCodeX" messages (where X is 1-99)
#     softcode_pattern = re.compile(r"SoftCode([1-9][0-9]?)")

#     # Pattern for GlobalTimer#_End
#     global_timer_end_pattern = re.compile(r"_GlobalTimer([1-9])_(End)")

#     # Pattern for GlobalTimer#_Start
#     global_timer_start_pattern = re.compile(r"_GlobalTimer([1-9])_(Start)")

#     # Pattern for GlobalCounter# with _End and _Reset suffixes
#     global_counter_pattern = re.compile(r"_GlobalCounter([1-9])_(End)")

#     # Pattern for "Condition#"
#     condition_pattern = re.compile(r"_Condition([1-9])")

#     if msg == "_Tup":
#         return ("_Tup", 1, 1)

#     elif port_match := port_pattern.match(msg):
#         channel, state = port_match.groups()
#         value = 1 if state == "In" else 0
#         return ("Port", int(channel), value)

#     elif pa1_port_match := pa1_port_pattern.match(msg):
#         channel, state = pa1_port_match.groups()
#         value = 1 if state == "In" else 0
#         return ("PA1_Port", int(channel), value)

#     elif bnc_match := bnc_pattern.match(msg):
#         channel, state = bnc_match.groups()
#         value = 3 if state == "High" else 0
#         return ("BNC", int(channel), value)

#     elif wire_match := wire_pattern.match(msg):
#         channel, state = wire_match.groups()
#         value = 3 if state == "High" else 0
#         return ("Wire", int(channel), value)

#     elif serial_match := serial_pattern.match(msg):
#         channel, value = serial_match.groups()
#         return ("Serial", int(channel), int(value))

#     elif softcode_match := softcode_pattern.match(msg):
#         channel = softcode_match.group(1)
#         return ("USB", int(channel), 1)  # The value is always 1

#     elif global_timer_start_match := global_timer_start_pattern.match(msg):
#         channel, _ = global_timer_start_match.groups()
#         return ("_GlobalTimer_Start", int(channel), 1)

#     elif global_timer_end_match := global_timer_end_pattern.match(msg):
#         channel, _ = global_timer_end_match.groups()
#         return ("_GlobalTimer_End", int(channel), 1)

#     elif global_counter_end_match := global_counter_pattern.match(msg):
#         channel, _ = global_counter_end_match.groups()
#         return ("_GlobalCounter_End", int(channel), 1)

#     elif condition_match := condition_pattern.match(msg):
#         channel = condition_match.group(1)
#         return ("_Condition", int(channel), 1)

#     else:
#         raise ValueError(f"Unrecognized message format: {msg}")


# def parse_message_output(message: str | tuple[str, int]) -> tuple[str, int, int]:
#     # Convert the message to string if it's a tuple
#     msg = str(message)

#     # Pattern for ("PWMX", Y) messages (where X is 1-9 and Y is 0-255)
#     pwm_pattern = re.compile(r"\('PWM([1-9])',\s*([0-9]|[1-9][0-9]{1,2})\)")

#     # Pattern for "Valve#"
#     valve_pattern = re.compile(r"Valve([1-9])")

#     # Pattern for "BNC#High" and "BNC#Low" (where # is 1-9)
#     bnc_pattern = re.compile(r"BNC([1-9])(High|Low)")

#     # Pattern for "Wire#High" and "Wire#Low" (where # is 1-9)
#     wire_pattern = re.compile(r"Wire([1-9])(High|Low)")

#     # Pattern for ("SerialX", Y) messages (where X is 1-9 and Y is 0-99)
#     serial_pattern = re.compile(r"\('Serial([1-9])',\s*([1-9][0-9]?)")

#     # Pattern for ("SoftCode", Y) messages (where Y is 1-99)
#     softcode_pattern = re.compile(r"\('SoftCode',\s*([1-9][0-9]?)")

#     # Pattern for ("_GlobalTimerTrig", Y) messages (where Y is 1-9)
#     global_timer_trig_pattern = re.compile(r"\('_GlobalTimerTrig',\s*([1-9])")

#     # Pattern for ("_GlobalTimerCancel", Y) messages (where Y is 1-9)
#     global_timer_cancel_pattern = re.compile(r"\('_GlobalTimerCancel',\s*([1-9])")

#     # Pattern for ("_GlobalCounterReset", Y) messages (where Y is 1-9)
#     global_counter_reset_pattern = re.compile(r"\('_GlobalCounterReset',\s*([1-9])")

#     if pwm_match := pwm_pattern.match(msg):
#         channel, value = pwm_match.groups()
#         return ("PWM", int(channel), int(value))

#     elif valve_match := valve_pattern.match(msg):
#         channel = valve_match.group(1)
#         return ("Valve", int(channel), 1)  # The value is always 1

#     elif bnc_match := bnc_pattern.match(msg):
#         channel, state = bnc_match.groups()
#         value = 3 if state == "High" else 0
#         return ("BNC", int(channel), value)

#     elif wire_match := wire_pattern.match(msg):
#         channel, state = wire_match.groups()
#         value = 3 if state == "High" else 0
#         return ("Wire", int(channel), value)

#     elif serial_match := serial_pattern.match(msg):
#         channel, value = serial_match.groups()
#         return ("Serial", int(channel), int(value))

#     elif softcode_match := softcode_pattern.match(msg):
#         channel = softcode_match.group(1)
#         return ("SoftCode", int(channel), 1)  # The value is always 1

#     elif global_timer_trig_match := global_timer_trig_pattern.match(msg):
#         channel = global_timer_trig_match.group(1)
#         return ("_GlobalTimerTrig", int(channel), 1)

#     elif global_timer_cancel_match := global_timer_cancel_pattern.match(msg):
#         channel = global_timer_cancel_match.group(1)
#         return ("_GlobalTimerCancel", int(channel), 1)

#     elif global_counter_reset_match := global_counter_reset_pattern.match(msg):
#         channel = global_counter_reset_match.group(1)
#         return ("_GlobalCounterReset", int(channel), 1)

#     else:
#         raise ValueError(f"Unrecognized message format: {msg}")


# from village.devices.bpod import bpod

# # Ejemplos de uso input:
# print(bpod.parse_message_input("_Tup"))
# print(bpod.parse_message_input("Port1In"))
# print(bpod.parse_message_input("Port2Out"))
# print(bpod.parse_message_input("PA1_Port1In"))
# print(bpod.parse_message_input("PA1_Port3Out"))
# print(bpod.parse_message_input("BNC1High"))
# print(bpod.parse_message_input("BNC2Low"))
# print(bpod.parse_message_input("Wire1High"))
# print(bpod.parse_message_input("Wire2Low"))
# print(bpod.parse_message_input("Serial1_4"))
# print(bpod.parse_message_input("Serial3_12"))
# print(bpod.parse_message_input("SoftCode1"))
# print(bpod.parse_message_input("SoftCode34"))
# print(bpod.parse_message_input("_GlobalTimer1_Start"))
# print(bpod.parse_message_input("_GlobalTimer2_End"))
# print(bpod.parse_message_input("_GlobalCounter3_End"))
# print(bpod.parse_message_input("_Condition1"))


# # output
# print(bpod.parse_message_output(("PWM1", 255)))
# print(bpod.parse_message_output(("PWM2", 0)))
# print(bpod.parse_message_output(("PWM2", 3)))
# print(bpod.parse_message_output(("PWM2", 103)))
# print(bpod.parse_message_output(("PWM1", 26)))
# print(bpod.parse_message_output(("Valve", 4)))
# print(bpod.parse_message_output(("BNC1", 3)))
# print(bpod.parse_message_output(("BNC2", 0)))
# print(bpod.parse_message_output(("Wire1", 3)))
# print(bpod.parse_message_output(("Wire2", 0)))
# print(bpod.parse_message_output(("Serial4", 3)))
# print(bpod.parse_message_output(("Serial2", 31)))
# print(bpod.parse_message_output(("SoftCode", 23)))
# print(bpod.parse_message_output(("SoftCode", 5)))
# print(bpod.parse_message_output(("_GlobalTimerTrig", 1)))
# print(bpod.parse_message_output(("_GlobalTimerCancel", 2)))
# print(bpod.parse_message_output(("_GlobalCounterReset", 3)))


# import time

# from village.classes.task import Event, Output
# from village.devices.bpod import bpod

# # bpod.add_state(
# #     state_name="light_off",
# #     state_timer=5,
# #     state_change_conditions={
# #         Event.Port1In: "light_on",
# #         Event.Tup: "exit",
# #     },
# #     output_actions=[],
# # )

# # bpod.add_state(
# #     state_name="light_on",
# #     state_timer=5,
# #     state_change_conditions={
# #         Event.Port1Out: "light_off",
# #         Event.Tup: "exit",
# #     },
# #     output_actions=[(Output.PWM2, 255), Output.BNC1High],
# # )

# # bpod.send_and_run_state_machine()

# # bpod.close()


# bpod.manual_override_output((Output.PWM2, 255))
# bpod.manual_override_output(Output.Valve1)
# bpod.manual_override_output(Output.SoftCode14)


# bpod.manual_override_input(Event.Port1In)
# time.sleep(1)
# bpod.stop()
# time.sleep(1)
