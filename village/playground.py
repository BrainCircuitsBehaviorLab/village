# from village.pybpodapi.protocol import Bpod, StateMachine

# bpod = Bpod()

# sma = StateMachine(bpod)

# sma.add_state(
#     state_name="State0",
#     state_timer=3,
#     state_change_conditions={Bpod.Events.Tup: "exit"},
#     output_actions=[],
# )


# bpod.send_state_machine(sma)
# bpod.run_state_machine(sma)

# # # sma.add_state(
# # #     state_name="State2",
# # #     state_timer=0,
# # #     state_change_conditions={"Port1Out": "State1"},
# # #     output_actions=[],
# # # )


# bpod.send_state_machine(sma)
# bpod.run_state_machine(sma)

# bpod.close()


# import importlib
# import inspect
# import os
# import sys

# from village.classes.task import Task
# from village.settings import settings

# directory = settings.get("CODE_DIRECTORY")
# sys.path.append(directory)


# import virtual_mouse

# print("OK")

# settings = Settings(
#     main_settings,
#     corridor_settings,
#     sound_settings,
#     alarm_settings,
#     directory_settings,
#     screen_settings,
#     touchscreen_settings,
#     telegram_settings,
#     bpod_settings,
#     camera_settings,
#     motor_settings,
#     extra_settings,
# )

# import trial_plotter

# print("OK")

# import follow_the_light

# print("OK")

# import task_runner

# print("OK")

# python_files = []
# tasks = []

# for root, dirs, files in os.walk(directory):
#     for file in files:
#         if file.endswith(".py"):
#             python_files.append(os.path.join(root, file))

# for python_file in python_files:
#     relative_path = os.path.relpath(python_file, directory)
#     module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]
#     print(f"Importing {module_name} from {python_file}")
#     try:
#         module = importlib.import_module(module_name)
#         print("done")
#         clsmembers = inspect.getmembers(module, inspect.isclass)
#         print("clsmembers: ", clsmembers)
#         for _, cls in clsmembers:
#             print("cls: ", cls)
#             if issubclass(cls, Task) and cls != Task:
#                 print("is subclass")
#                 name = cls.__name__
#                 print(name)
#                 new_task = cls()
#                 new_task.name = name
#                 tasks.append(new_task)
#     except Exception as e:
#         print("Error importing " + module_name)
#         continue

# import time

# from gpiozero import Servo


# servo = Servo(
#     18,
#     min_pulse_width=0.5 / 1000,
#     max_pulse_width=2.5 / 1000,
# )

# servo.max()
# time.sleep(2)
# servo.mid()
# time.sleep(2)
# servo.min()
# time.sleep(2)
