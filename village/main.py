# This file is part of the Training Village repository.
# Copyright (C) [2024] [BRAIN CIRCUITS AND BEHAVIOR LAB]
#
# This program is licensed under the GNU General Public License v3 (GPLv3).
# See the LICENSE.md file in the root of this repository for full license text.
# For more details, see <http://www.gnu.org/licenses/>.

import os

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

import gc
import threading
import time

import numpy as np
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QWidget

from village.classes.enums import Active, State
from village.devices.bpod import bpod
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.devices.scale import real_weight_inference, scale
from village.devices.sound_device import sound_device
from village.devices.telegram_bot import telegram_bot
from village.devices.temp_sensor import temp_sensor
from village.gui.gui import Gui
from village.log import log
from village.manager import manager
from village.scripts import time_utils
from village.settings import settings

# to debug segfaults uncomment the following lines
# import faulthandler
# faulthandler.enable()


fmt = QSurfaceFormat()
fmt.setSwapInterval(1)  # try 0
fmt.setVersion(2, 0)  # OpenGL ES 3.1
fmt.setRenderableType(QSurfaceFormat.OpenGL)

fmt.setDepthBufferSize(0)
fmt.setStencilBufferSize(0)
fmt.setSamples(0)
fmt.setAlphaBufferSize(0)

QSurfaceFormat.setDefaultFormat(fmt)

# automatic garbage collection disabled, we will use it manually when no task is running
gc.disable()

# init
manager.task.bpod = bpod
log.telegram_bot = telegram_bot
log.cam = cam_corridor
manager.import_all_tasks()
manager.errors = (
    bpod.error
    + cam_corridor.error
    + cam_box.error
    + scale.error
    + temp_sensor.error
    + sound_device.error
    + telegram_bot.error
)
if manager.errors == "":
    log.start("VILLAGE")
else:
    log.error(manager.errors)
    log.start("VILLAGE_DEBUG")


# create a secondary thread
def system_run(bevavior_window: QWidget) -> None:

    # TESTING
    # i = 0
    # TESTING

    id = ""
    multiple = False
    checking_subject_requirements = True
    trial = 0
    detection_timer = time_utils.Timer(settings.get("DETECTION_DURATION"))
    tare_timer = time_utils.Timer(settings.get("REPEAT_TARE_TIME"))
    plot_timer = time_utils.Timer(settings.get("UPDATE_TIME_TABLE"))

    cam_corridor.start_record()

    corridor_video_duration = float(settings.get("CORRIDOR_VIDEO_DURATION"))
    weight_threshold = float(settings.get("WEIGHT_THRESHOLD"))

    while True:
        time.sleep(0.001)

        # if the task is not running, enable garbage collection
        if manager.state == State.WAIT:
            gc.enable()
        else:
            gc.disable()

        if cam_corridor.chrono.get_seconds() > corridor_video_duration:
            cam_corridor.stop_record()
            cam_corridor.start_record()

        if manager.online_plot_figure_manager.active:
            if manager.task.current_trial > trial and plot_timer.has_elapsed():
                trial = manager.task.current_trial
                try:
                    manager.online_plot_figure_manager.update_canvas(
                        manager.task.session_df
                    )
                except Exception:
                    pass
        else:
            trial = 0

        if manager.hour_change_detector.has_hour_changed():
            manager.hourly_checks()

        if manager.cycle_change_detector.has_cycle_changed():
            manager.cycle_checks()

        if manager.taring_scale:
            scale.tare()
            manager.taring_scale = False
        elif manager.getting_weights:
            weight = scale.get_weight()
            if manager.log_weight:
                weight_str = "weight: {:.2f} g".format(weight)
                log.info(weight_str)
                manager.log_weight = False
        else:
            weight = 0.0

        if manager.state != State.DETECTION:
            id, multiple = rfid.get_id()

        match manager.state:
            case State.WAIT:
                # All subjects are at home, waiting for RFID detection
                if not manager.previous_state_wait:
                    id, multiple = rfid.get_id()
                    manager.reset_subject_task_training()

                # TESTING
                # i += 1
                # if i == 10000:
                #     manager.behavior_window.set_active(True)
                # elif i == 20000:
                #     i = 0
                #     manager.behavior_window.set_active(False)
                # TESTING

                if id != "":
                    log.info("Tag detected: " + id)
                    manager.detection_change = True
                    checking_subject_requirements = True
                    manager.state = State.DETECTION
            case State.DETECTION:
                # Gathering subject data, checking requirements to enter
                manager.previous_state_wait = False
                if checking_subject_requirements:
                    manager.detections.add_timestamp()
                    if (
                        manager.get_subject_from_tag(id)
                        and manager.subject.create_from_subject_series(id)
                        and manager.subject.minimum_time_ok()
                        and cam_corridor.areas_corridor_ok()
                        and not manager.multiple_detections(multiple)
                    ):
                        checking_subject_requirements = False
                        detection_timer.reset()
                    else:
                        manager.state = State.WAIT
                else:
                    if detection_timer.has_elapsed():
                        manager.state = State.ACCESS
                    else:
                        if not cam_corridor.areas_corridor_ok():
                            manager.state = State.WAIT

            case State.ACCESS:
                # Closing door1, opening door2
                motor1.close()
                motor2.open()
                manager.state = State.LAUNCH_AUTO

            case State.LAUNCH_AUTO:
                # Automatically launching the task
                if manager.launch_task_auto(cam_box):
                    manager.detection_change = True
                    manager.state = State.RUN_FIRST
                    log.info("Going to RUN_FIRST State")
                else:
                    manager.state = State.OPEN_DOOR2_STOP
                    log.info("Going to OPEN_DOOR2_STOP State")

            case State.RUN_FIRST:
                # Task running, waiting for the corridor to become empty"
                if id != manager.subject.tag and id != "":
                    log.alarm(
                        "Wrong RFID detection: "
                        + id
                        + " Another subject detected while main subject is in the box."
                        + " Opening door2 and disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                    log.info("Going to OPEN_DOOR2_STOP State")
                elif (
                    cam_corridor.area_2_empty()
                    and cam_corridor.area_3_empty()
                    and cam_corridor.area_4_empty()
                    and manager.task.chrono.get_seconds() > 1
                ):
                    manager.state = State.CLOSE_DOOR2

            case State.CLOSE_DOOR2:
                # Closing door2
                motor2.close()
                log.info("Going to RUN_CLOSED State")
                manager.state = State.RUN_CLOSED

            case State.RUN_CLOSED:
                # Task running, the subject cannot leave yet
                if id != "":
                    log.alarm(
                        "Wrong RFID detection: "
                        + id
                        + " Subject detected in the corridor while main"
                        + " subject should be in the box."
                        + " Opening door2 and disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                    log.info("Going to OPEN_DOOR2_STOP State")
                elif (
                    manager.task.chrono.get_seconds()
                    >= manager.task.settings.minimum_duration
                ):
                    log.info(
                        "Minimum time reached, subject can leave.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2

            case State.OPEN_DOOR2:
                # Opening door2
                scale.tare()
                tare_timer.reset()
                motor2.open()
                manager.state = State.RUN_OPENED
                log.info("Going to RUN_OPENED State")

            case State.RUN_OPENED:
                # task running, the subject can leave
                manager.getting_weights = True
                if cam_corridor.area_2_empty() and cam_corridor.area_3_empty():
                    if tare_timer.has_elapsed():
                        scale.tare()

                if id != manager.subject.tag and id != "":
                    log.alarm(
                        "Wrong RFID detection: "
                        + id
                        + " Another subject detected while main subject is in the box."
                        + " Opening door2 and disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                    log.info("Going to OPEN_DOOR2_STOP State")
                elif (
                    manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                ):
                    log.info(
                        "Maximum time reached, stopping the task.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.SAVE_INSIDE
                elif manager.task.force_stop:
                    manager.task.force_stop = False
                    log.info(
                        "Condition to stop the task met, stopping the task.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.SAVE_INSIDE
                elif weight > weight_threshold:
                    manager.measuring_weight_list.append(weight)
                    print(manager.measuring_weight_list)
                    if (
                        real_weight_inference(
                            manager.measuring_weight_list,
                            weight_threshold,
                        )
                        or len(manager.measuring_weight_list) >= 100
                    ):
                        manager.weight = round(
                            np.median(manager.measuring_weight_list[-5:]), 2
                        )
                        manager.getting_weights = False
                        manager.measuring_weight_list = []
                        manager.state = State.EXIT_UNSAVED
                        log.info(
                            "Subject back home: " + str(manager.weight) + " g",
                            subject=manager.subject.name,
                        )
                    else:
                        time.sleep(0.1)

            case State.EXIT_UNSAVED:
                # Closing door2, opening door1; data still not saved
                motor2.close()
                motor1.open()
                manager.state = State.SAVE_OUTSIDE

            case State.SAVE_OUTSIDE:
                # Stopping the task, saving the data; the subject is already outside
                manager.disconnect_and_save("Auto")
                manager.detection_change = True
                manager.state = State.SYNC
                log.info("Going to SYNC State")

            case State.SAVE_INSIDE:
                # Stopping the task, saving the data; the subject is still inside
                manager.disconnect_and_save("Auto")
                manager.detection_change = True
                manager.state = State.WAIT_EXIT
                log.info("Going to WAIT_EXIT State")

            case State.WAIT_EXIT:
                # Task finished, waiting for the subject to leave
                manager.getting_weights = True
                if (
                    manager.task.chrono.get_seconds()
                    > manager.task.settings.maximum_duration
                    + manager.max_time_counter * 3600
                ):
                    text = (
                        "The subject has been in the box for "
                        + str(manager.task.chrono.get_seconds())
                        + " seconds. "
                    )
                    if manager.max_time_counter == 1:
                        text += "1 hour since the task ended."
                    else:
                        text += (
                            str(manager.max_time_counter)
                            + " hours since the task ended."
                        )
                    log.alarm(text, subject=manager.subject.name)
                    manager.max_time_counter += 1
                if weight > weight_threshold:
                    log.info(
                        "Weight detected " + str(weight) + " g",
                        subject=manager.subject.name,
                    )
                    manager.getting_weights = False
                    manager.weight = weight
                    manager.state = State.EXIT_SAVED

            case State.EXIT_SAVED:
                # Closing door2, opening door1 (data already saved)
                log.info("The subject has returned home.", subject=manager.subject.name)
                motor2.close()
                motor1.open()
                manager.sessions_summary.change_last_entry("weight", manager.weight)
                manager.state = State.SYNC
                log.info("Going to SYNC State")

            case State.OPEN_DOOR2_STOP:
                # Opening door2, disconnecting RFID
                motor2.open()
                manager.rfid_reader = Active.OFF
                manager.rfid_changed = True
                manager.state = State.SAVE_INSIDE

            case State.MANUAL_MODE:
                # Settings are being changed or task is being manually prepared
                manager.previous_state_wait = False

            case State.LAUNCH_MANUAL:
                # Manually launching the task
                if manager.launch_task_manual(cam_box):
                    manager.detection_change = True
                    manager.state = State.RUN_MANUAL
                    log.info("Going to RUN_MANUAL State")
                else:
                    manager.detection_change = True
                    manager.state = State.WAIT
                    log.info("Going to WAIT State")

            case State.RUN_MANUAL:
                # Task running manually
                if (
                    manager.task.current_trial > manager.task.maximum_number_of_trials
                    or manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                    or manager.task.force_stop
                ):
                    manager.state = State.SAVE_MANUAL

            case State.SAVE_MANUAL:
                # Stopping the task, saving the data; the task was manually stopped
                manager.disconnect_and_save("Manual")
                manager.detection_change = True
                if manager.calibrating:
                    manager.calibrating = False
                    manager.state = State.WAIT
                    log.info("Going to WAIT State")
                else:
                    manager.state = State.SYNC
                    log.info("Going to SYNC State")

            case State.EXIT_GUI:
                # In the GUI window, ready to exit the app
                manager.previous_state_wait = False

            case State.SYNC:
                # Synchronizing data with the server or doing user-defined tasks
                if manager.after_session_run_flag:
                    manager.after_session_run_flag = False
                    manager.after_session_run.run()
                if manager.change_cycle_run_flag:
                    manager.change_cycle_run_flag = False
                    manager.change_cycle_run.run()
                manager.state = State.WAIT
                log.info("Going to WAIT State")


# create the GUI that will run in the main thread
gui = Gui()
manager.behavior_window = gui.behavior_window

# start the secondary thread (control of the system)
system_state = threading.Thread(
    target=system_run, args=(manager.behavior_window,), daemon=True
)
system_state.start()

# start the GUI
gui.q_app.exec()
