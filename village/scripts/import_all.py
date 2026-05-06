import importlib
import importlib.util
import inspect
import os
import sys
import traceback

from village.custom_classes.after_session_base import AfterSessionBase
from village.custom_classes.auto_no_mouse_base import AutoNoMouse_Base
from village.custom_classes.camera_draw_base import CameraDrawBase
from village.custom_classes.camera_trigger_base import CameraTriggerBase
from village.custom_classes.change_cycle_base import ChangeCycleBase
from village.custom_classes.online_plot_base import OnlinePlotBase
from village.custom_classes.session_plot_base import SessionPlotBase
from village.custom_classes.subject_plot_base import SubjectPlotBase
from village.custom_classes.task import Task
from village.custom_classes.training_protocol_base import TrainingProtocolBase
from village.scripts.log import log
from village.settings import settings


def import_all(manager) -> None:
    directory = settings.get("CODE_DIRECTORY")
    sys.path.append(directory)

    python_files: list[str] = []
    tasks = dict()
    training_found = 0
    session_plot_found = 0
    subject_plot_found = 0
    online_plot_found = 0
    after_session_found = 0
    change_cycle_found = 0
    camera_trigger_found = 0
    camera_draw_found = 0
    auto_no_mouse_found = 0
    training_correct = False
    session_plot_correct = False
    subject_plot_correct = False
    online_plot_correct = False
    after_session_correct = False
    change_cycle_correct = False
    camera_trigger_correct = False
    camera_draw_correct = False
    auto_no_mouse_correct = False
    functions_path = ""
    sound_path = ""

    for root, _, files in os.walk(directory):
        for file in files:
            if file == "softcode_functions.py":
                functions_path = os.path.join(root, file)
            if file == "sound_functions.py":
                sound_path = os.path.join(root, file)
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if os.path.exists(functions_path):
        module_name = "custom_module"
        spec = importlib.util.spec_from_file_location(module_name, functions_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                for i in range(1, 100):
                    func_name = f"function{i}"
                    if hasattr(module, func_name):
                        manager.functions[i] = getattr(module, func_name)
            except Exception:
                log.error(
                    "Couldn't import softcode functions",
                    exception=traceback.format_exc(),
                )

    if os.path.exists(sound_path):
        module_name = "custom_module2"
        spec = importlib.util.spec_from_file_location(module_name, sound_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, "sound_calibration_functions"):
                    manager.sound_calibration_functions = getattr(
                        module, "sound_calibration_functions"
                    )
            except Exception:
                log.error(
                    "Couldn't import sound calibration functions",
                    exception=traceback.format_exc(),
                )

    for python_file in python_files:
        relative_path = os.path.relpath(python_file, directory)
        module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]
        try:
            module = importlib.import_module(module_name)
            clsmembers = inspect.getmembers(module, inspect.isclass)
            for _, cls in clsmembers:
                if cls.__module__ != module_name:
                    continue

                if issubclass(cls, Task) and cls != Task:
                    name = cls.__name__
                    _ = cls()
                    if name not in tasks:
                        tasks[name] = cls
                elif (
                    issubclass(cls, TrainingProtocolBase)
                    and cls != TrainingProtocolBase
                ):
                    training_found += 1
                    if training_found == 1:
                        t = cls()
                        t.copy_settings()
                        manager.training = t
                        training_correct = True
                elif issubclass(cls, SessionPlotBase) and cls != SessionPlotBase:
                    session_plot_found += 1
                    if session_plot_found == 1:
                        p = cls()
                        manager.session_plot = p
                        session_plot_correct = True
                elif issubclass(cls, SubjectPlotBase) and cls != SubjectPlotBase:
                    subject_plot_found += 1
                    if subject_plot_found == 1:
                        s = cls()
                        manager.subject_plot = s
                        subject_plot_correct = True
                elif issubclass(cls, OnlinePlotBase) and cls != OnlinePlotBase:
                    online_plot_found += 1
                    if online_plot_found == 1:
                        o = cls()
                        manager.online_plot = o
                        online_plot_correct = True
                elif issubclass(cls, AfterSessionBase) and cls != AfterSessionBase:
                    after_session_found += 1
                    if after_session_found == 1:
                        a = cls()
                        manager.after_session = a
                        after_session_correct = True
                elif issubclass(cls, ChangeCycleBase) and cls != ChangeCycleBase:
                    change_cycle_found += 1
                    if change_cycle_found == 1:
                        y = cls()
                        manager.change_cycle = y
                        change_cycle_correct = True
                elif issubclass(cls, CameraTriggerBase) and cls != CameraTriggerBase:
                    camera_trigger_found += 1
                    if camera_trigger_found == 1:
                        z = cls()
                        manager.camera_trigger = z
                        camera_trigger_correct = True
                elif issubclass(cls, CameraDrawBase) and cls != CameraDrawBase:
                    camera_draw_found += 1
                    if camera_draw_found == 1:
                        c = cls()
                        manager.camera_draw = c
                        camera_draw_correct = True
                elif issubclass(cls, AutoNoMouse_Base) and cls != AutoNoMouse_Base:
                    auto_no_mouse_found += 1
                    if auto_no_mouse_found == 1:
                        d = cls()
                        manager.auto_no_mouse = d
                        auto_no_mouse_correct = True

        except Exception:
            log.error(
                "Couldn't import " + module_name, exception=traceback.format_exc()
            )
            continue
    if training_found == 0:
        log.error("Training protocol not found")
    elif training_found == 1 and training_correct:
        log.info("Training protocol successfully imported")
    elif training_found > 1:
        log.error("Multiple training protocols found")

    items = [
        ("Session plot", session_plot_found, session_plot_correct),
        ("Subject plot", subject_plot_found, subject_plot_correct),
        ("Online plot", online_plot_found, online_plot_correct),
        ("After Session Run", after_session_found, after_session_correct),
        ("Change Cycle Run", change_cycle_found, change_cycle_correct),
        ("Camera Trigger", camera_trigger_found, camera_trigger_correct),
        ("Camera Draw", camera_draw_found, camera_draw_correct),
        ("Auto No Mouse", auto_no_mouse_found, auto_no_mouse_correct),
    ]

    defaults, customs = [], []
    for name, found, correct in items:
        if found > 1:
            log.error("Multiple %s found", name)
        elif found == 0:
            defaults.append(name)
        elif correct:
            customs.append(name)

    if defaults:
        log.info("Using default: " + ", ".join(defaults))
    if customs:
        log.info("Using custom: " + ", ".join(customs))

    manager.tasks = dict(sorted(tasks.items()))
    number_of_tasks = len(tasks)
    if number_of_tasks == 0:
        log.error("No tasks could be imported")
    elif number_of_tasks == 1:
        log.info("1 task successfully imported")
    else:
        log.info(str(number_of_tasks) + " tasks successfully imported")
