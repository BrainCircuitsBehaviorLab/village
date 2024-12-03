# This file is part of the Training Village repository.
# Copyright (C) [2024] [BRAIN CIRCUITS AND BEHAVIOR LAB]
#
# This program is licensed under the GNU General Public License v3 (GPLv3).
# See the LICENSE.md file in the root of this repository for full license text.
# For more details, see <http://www.gnu.org/licenses/>.


# VARIABLES WE CAN IMPORT IN ANY FILE
# settings (no dependencies)
# time_utils (no dependencies)
# log (depens on time_utils in init and later
#       it depens on data for the events and telegram_bot for the alarms)
# data (depends on settings, time_utils and log)
#   contains subject, task,
#   subjects, events, sessions_summary, water_calibration, sound_calibration
# DEVICES WE CAN IMPORT IN ANY FILE (depend on settings and utils)
# bpod
# cam_box
# cam_corridor
# motor1
# motor2
# rfid
# scale
# sound_device
# telegram_bot
# temp_sensor


# When launching the application the following processes are executed:
# 1. start importing data from village.data.py
#       this causes the import of settings and time_utils
# 2. import settings from village.settings.py
#       if they don't exist they are automatically created from factory settings
#       the extra settings are read from the code every time the application is launched
# 3. import time_utils from village.time_utils.py
# 4. continue importing data
#       read the path setting for the project directory
#       if the directory doesn't exist create it and its subdirectories
# 5. continue importing data
#       read the data from project directory (events, sessions_summary,
#       subjects, water_calibration, sound_calibration)
#       if the files don't exist create them
# 6. continue importing data
#       if the project directory is the demo directory and the code is empty,
#       download the code from the github repository
# 7. continue importing datadata.rfid_reader
#       set the logprotocol to the events collection
# 8. continue importing data
#       log that the village has started
# 9. try import bpod from village.devices.bpod.py and log the result
# 10. try to import cam_corridor and cam_box from village.devices.camera.py and
#       log the result
# 11. assign the bpod to the task in data
# 12. import all tasks from the code directory and log the result


import threading
import time

from village.classes.enums import Active, State
from village.devices.bpod import bpod
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.devices.scale import scale
from village.devices.telegram_bot import telegram_bot
from village.devices.temp_sensor import temp_sensor
from village.gui.gui import Gui
from village.log import log
from village.manager import manager

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
    + telegram_bot.error
)
if manager.errors == "":
    log.start("VILLAGE")
else:
    log.error(manager.errors)
    log.start("VILLAGE_DEBUG")


# create a secondary thread
def system_run() -> None:

    i = 0
    id = ""
    multiple = False

    cam_corridor.start_record()

    while True:
        i += 1
        time.sleep(0.01)

        if i == 20000:
            log.alarm("Alarma de prueba", subject="RAFA")

        if i % 60000 == 0:
            log.info("counter: " + str(i) + " textos de prueba")

        if cam_corridor.chrono.get_seconds() > 1800:
            cam_corridor.stop_record()
            cam_corridor.start_record()

        match manager.state:
            case State.WAIT:
                # All subjects are at home, waiting for RFID detection
                id, multiple = rfid.get_id()
                if id != "":
                    manager.state = State.DETECTION
            case State.DETECTION:
                # Gathering subject data, checking requirements to enter
                if (
                    manager.get_subject_from_tag(id)
                    and manager.subject.create_from_subject_series()
                    and manager.subject.minimum_time_ok()
                    and cam_corridor.areas_corridor_ok()
                    and not manager.multiple_detections(multiple)
                ):
                    manager.state = State.ACCESS
                else:
                    manager.state = State.WAIT

            case State.ACCESS:
                # Closing door1, opening door2
                motor1.close()
                motor2.open()
                manager.state = State.LAUNCH_AUTO

            case State.LAUNCH_AUTO:
                # Automatically launching the task
                if manager.launch_task_auto():
                    manager.task.cam_box = cam_box
                    manager.state = State.RUN_FIRST
                else:
                    manager.state = State.OPEN_DOOR2_STOP

            case State.RUN_FIRST:
                # Task running, waiting for the corridor to become empty"
                id, multiple = rfid.get_id()
                if id == manager.subject.tag:
                    log.info(
                        "Subject not allowed to leave. Task has not started yet",
                        subject=manager.subject.name,
                    )
                elif id != "":
                    log.alarm(
                        """Another subject detected while main subject is in the box.
                        Disconnecting RFID reader.""",
                        subject=manager.subject.name,
                    )
                    manager.state = State.OPEN_DOOR2_STOP
                if (
                    manager.task.current_trial
                    >= manager.task.settings.maximum_number_of_trials
                    or manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                    or manager.task.force_stop
                ):
                    manager.state = State.OPEN_DOOR2_STOP

            case State.CLOSE_DOOR2:
                # Closing door2
                if cam_corridor.area_3_empty():
                    motor2.close()
                    manager.state = State.RUN_CLOSED
                else:
                    pass

            case State.RUN_CLOSED:
                # Task running, the subject cannot leave yet
                id, multiple = rfid.get_id()
                if id == manager.subject.tag:
                    log.info(
                        "Subject not allowed to leave. Task has not started yet",
                        subject=manager.subject.name,
                    )
                elif id != "":
                    log.alarm(
                        """Another subject detected in the corridor while
                        main subject is in the box.
                        """,
                        subject=manager.subject.name,
                    )
                if (
                    manager.task.current_trial
                    >= manager.task.settings.maximum_number_of_trials
                    or manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                    or manager.task.force_stop
                ):
                    manager.state = State.OPEN_DOOR2_STOP

            case State.OPEN_DOOR2:
                # Opening door2
                pass

            case State.RUN_OPENED:
                # task running, the subject can leave
                pass

            case State.EXIT_UNSAVED:
                # Closing door2, opening door1; data still not saved
                pass

            case State.SAVE_OUTSIDE:
                # Stopping the task, saving the data; the subject is already outside
                manager.task.disconnect_and_save()
                manager.reset_subject_task_training()
                manager.state = State.WAIT

            case State.SAVE_INSIDE:
                # Stopping the task, saving the data; the subject is still inside
                manager.task.disconnect_and_save()
                manager.reset_subject_task_training()
                manager.state = State.WAIT_EXIT

            case State.WAIT_EXIT:
                # Task finished, waiting for the subject to leave
                pass

            case State.EXIT_SAVED:
                # Closing door2, opening door1 (data already saved)
                pass

            case State.OPEN_DOOR2_STOP:
                # Opening door2, disconnecting RFID
                motor2.open()
                manager.rfid_reader = Active.OFF
                manager.state = State.SAVE_INSIDE

            case State.MANUAL_MODE:
                # Settings are being changed or task is being manually prepared
                pass

            case State.LAUNCH_MANUAL:
                # Manually launching the task
                if manager.launch_task_manual():
                    manager.task.cam_box = cam_box
                    manager.state = State.RUN_MANUAL
                else:
                    pass

            case State.RUN_MANUAL:
                # Task running manually
                if (
                    manager.task.current_trial
                    >= manager.task.settings.maximum_number_of_trials
                    or manager.task.chrono.get_seconds()
                    >= manager.task.settings.maximum_duration
                    or manager.task.force_stop
                ):
                    manager.state = State.SAVE_MANUAL

            case State.SAVE_MANUAL:
                # Stopping the task, saving the data; the task was manually stopped
                manager.task.disconnect_and_save()
                manager.reset_subject_task_training()
                manager.state = State.WAIT

            case State.EXIT_GUI:
                # In the GUI window, ready to exit the app
                pass


# start the secondary thread (control of the system)
system_state = threading.Thread(target=system_run, daemon=True)
system_state.start()

# start the primary thread (GUI)
gui = Gui()
