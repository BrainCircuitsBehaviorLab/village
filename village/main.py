# This file is part of the Training Village repository.
# Copyright (C) [2024] [BRAIN CIRCUITS AND BEHAVIOR LAB]
#
# This program is licensed under the GNU General Public License v3 (GPLv3).
# See the LICENSE.md file in the root of this repository for full license text.
# For more details, see <http://www.gnu.org/licenses/>.


import gc
import threading
import time

from PyQt5.QtWidgets import QWidget

from village.classes.enums import Active, State
from village.devices.bpod import bpod
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.devices.scale import scale
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

# automatic garbage collection disabled, we will use it manually when no task is running
gc.disable()

# init
manager.task.bpod = bpod
log.telegram_protocol = telegram_bot
log.cam_protocol = cam_corridor
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

    i = 0
    id = ""
    multiple = False
    checking_subject_requirements = True
    trial = 0
    detection_timer = time_utils.Timer(settings.get("DETECTION_DURATION"))
    tare_timer = time_utils.Timer(settings.get("REPEAT_TARE_TIME"))

    cam_corridor.start_record()

    while True:
        i += 1
        time.sleep(0.001)

        # if i == 2000:
        #     bpod.receive_softcode(1)
        #     log.alarm("Alarma de prueba", subject="RAFA")
        #     behavior_window.toggle_animation()

        if manager.state == State.WAIT:
            gc.enable()
        else:
            gc.disable()

        if cam_corridor.chrono.get_seconds() > float(
            settings.get("CORRIDOR_VIDEO_DURATION")
        ):
            cam_corridor.stop_record()
            cam_corridor.start_record()

        if manager.online_plot_figure_manager.active:
            if manager.task.current_trial > trial:
                trial = manager.task.current_trial
                manager.online_plot_figure_manager.update_plot(manager.task.session_df)
        else:
            trial = 0

        if manager.hour_change_detector.has_hour_changed():
            manager.hourly_checks()

        if manager.cycle_change_detector.has_cycle_changed():
            manager.cycle_checks()
            # TODO: delete data

        match manager.state:
            case State.WAIT:
                # All subjects are at home, waiting for RFID detection
                manager.reset_subject_task_training()
                id, multiple = rfid.get_id()
                if id != "":
                    log.info("Tag detected: " + id)
                    manager.detection_change = True
                    checking_subject_requirements = True
                    manager.state = State.DETECTION
            case State.DETECTION:
                # Gathering subject data, checking requirements to enter
                if checking_subject_requirements:
                    manager.detections.add_timestamp()
                    if (
                        manager.get_subject_from_tag(id)
                        and manager.subject.create_from_subject_series(auto=True)
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
                else:
                    manager.state = State.OPEN_DOOR2_STOP

            case State.RUN_FIRST:
                # Task running, waiting for the corridor to become empty"
                id, multiple = rfid.get_id()
                if id != manager.subject.tag and id != "":
                    log.alarm(
                        "Wrong RFID detection."
                        + " Another subject detected while main subject is in the box."
                        + " Disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                elif (
                    manager.task.chrono.get_seconds()
                    >= manager.task.settings.minimum_duration
                ):
                    log.alarm(
                        "Minimum time reached and areas 3 or 4 were never empty."
                        + " Disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP

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
                manager.state = State.RUN_CLOSED

            case State.RUN_CLOSED:
                # Task running, the subject cannot leave yet
                id, multiple = rfid.get_id()
                if id != "":
                    log.alarm(
                        "Wrong RFID detection."
                        + " Subject detected in the corridor while main"
                        + " subject should be in the box."
                        + " Disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
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
                time.sleep(0.5)
                motor2.open()
                manager.state = State.RUN_OPENED

            case State.RUN_OPENED:
                # task running, the subject can leave
                if (
                    tare_timer.has_elapsed()
                    and cam_corridor.area_2_empty()
                    and cam_corridor.area_3_empty()
                ):
                    scale.tare()

                id, multiple = rfid.get_id()
                if id != "" and id != manager.subject.tag:
                    log.alarm(
                        "Wrong RFID detection."
                        + " Another subject detected while main subject is in the box."
                        + " Disconnecting RFID reader.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                elif (
                    manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                ):
                    log.info(
                        "Maximum time reached, stopping the task.",
                        subject=manager.subject.name,
                    )
                    manager.state = State.SAVE_INSIDE
                else:
                    weight = scale.get_weight()
                    if weight > settings.get("WEIGHT_THRESHOLD"):
                        log.info(
                            "Weight detected " + str(weight) + " g",
                            subject=manager.subject.name,
                        )
                        manager.weight = weight
                        manager.state = State.EXIT_UNSAVED

            case State.EXIT_UNSAVED:
                # Closing door2, opening door1; data still not saved
                log.info("The subject has returned home.", subject=manager.subject.name)
                motor2.close()
                motor1.open()
                manager.state = State.SAVE_OUTSIDE

            case State.SAVE_OUTSIDE:
                # Stopping the task, saving the data; the subject is already outside
                manager.disconnect_and_save("Auto")
                manager.detection_change = True
                manager.state = State.WAIT

            case State.SAVE_INSIDE:
                # Stopping the task, saving the data; the subject is still inside
                manager.disconnect_and_save("Auto")
                manager.detection_change = True
                manager.state = State.WAIT_EXIT

            case State.WAIT_EXIT:
                # Task finished, waiting for the subject to leave
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
                weight = scale.get_weight()
                if weight > settings.get("WEIGHT_THRESHOLD"):
                    log.info(
                        "Weight detected " + str(weight) + " g",
                        subject=manager.subject.name,
                    )
                    manager.sessions_summary.change_last_entry("weight", weight)
                    manager.state = State.EXIT_SAVED

            case State.EXIT_SAVED:
                # Closing door2, opening door1 (data already saved)
                log.info("The subject has returned home.", subject=manager.subject.name)
                motor2.close()
                motor1.open()
                manager.state = State.WAIT

            case State.OPEN_DOOR2_STOP:
                # Opening door2, disconnecting RFID
                log.alarm(
                    "Door2 opened and RFID deactivated, check the system.",
                    subject=manager.subject.name,
                )
                motor2.open()
                manager.rfid_reader = Active.OFF
                manager.rfid_changed = True
                manager.state = State.SAVE_INSIDE

            case State.MANUAL_MODE:
                # Settings are being changed or task is being manually prepared
                pass

            case State.LAUNCH_MANUAL:
                # Manually launching the task
                if manager.launch_task_manual(cam_box):
                    manager.detection_change = True
                    manager.state = State.RUN_MANUAL
                else:
                    manager.detection_change = True
                    manager.state = State.WAIT

            case State.RUN_MANUAL:
                # Task running manually
                if (
                    manager.task.current_trial > manager.task.maximum_number_of_trials
                    or manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                ):
                    manager.state = State.SAVE_MANUAL

            case State.SAVE_MANUAL:
                # Stopping the task, saving the data; the task was manually stopped
                manager.disconnect_and_save("Manual")
                manager.detection_change = True
                manager.state = State.WAIT

            case State.EXIT_GUI:
                # In the GUI window, ready to exit the app
                pass


# create the GUI that will run in the main thread
gui = Gui()
behavior_window = gui.behavior_window

# start the secondary thread (control of the system)
system_state = threading.Thread(target=system_run, args=(behavior_window,), daemon=True)
system_state.start()

# start the GUI
gui.q_app.exec()
