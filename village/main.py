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
# 7. continue importing data
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

from village.classes.enums import State
from village.data import data
from village.devices.bpod import bpod
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.devices.telegram_bot import telegram_bot
from village.gui.gui import Gui
from village.log import log

# init
data.task.bpod = bpod
log.telegram_protocol = telegram_bot
log.cam_protocol = cam_corridor
data.import_all_tasks()
cam_corridor.start_record()
cam_box.start_record()
data.errors = bpod.error + cam_corridor.error + cam_box.error + telegram_bot.error
if data.errors == "":
    log.start("VILLAGE")
else:
    log.error(data.errors)
    log.start("VILLAGE_DEBUG")


# create a secondary thread to run some function
def system_run() -> None:

    i = 0
    id = ""
    multiple = False

    while True:
        i += 1
        time.sleep(1)

        if i == 200:
            log.alarm("Alarma de prueba", subject="RAFA")

        if i % 10 == 0:
            log.info("counter: " + str(i) + " textos de prueba")

        match data.state:
            case data.state.WAIT:
                # All subjects are at home, waiting for RFID detection
                if data.tag_reader == data.tag_reader.ON:
                    id, multiple = rfid.get_id()
                    if id != "":
                        data.state = State.DETECTION
            case data.state.DETECTION:
                # Gathering subject data, checking requirements to enter
                if (
                    data.get_subject_from_tag(id)
                    and data.subject.get_data_from_subject_series()
                    and data.subject.minimum_time_ok()
                    and cam_corridor.areas_corridor_ok()
                    and not data.multiple_detections(multiple)
                ):
                    data.state = State.ACCESS
                else:
                    data.state = State.WAIT

            case data.state.ACCESS:
                # Closing door1, opening door2
                motor1.close()
                motor2.open()
                data.state = State.LAUNCH

            case data.state.LAUNCH:
                # Launching the task
                if data.launch_task():
                    data.state = State.RUN_ACTION
                else:
                    data.state = State.STOP

            case data.state.RUN_ACTION:
                # Waiting for the first action in the behavioral box
                id, multiple = rfid.get_id()
                if id == data.subject.tag:
                    log.info(
                        "Subject not allowed to leave. Task has not started yet",
                        subject=data.subject.name,
                    )
                elif id != "":
                    log.alarm(
                        """Another subject detected while main subject is in the box.
                        Disconnecting RFID""",
                        subject=data.subject.name,
                    )
                    data.state = State.STOP
                if data.first_action:
                    data.state = State.CLOSE_DOOR2

            case data.state.CLOSE_DOOR2:
                # Closing door2
                if cam_corridor.area_3_empty():
                    motor2.close()
                    data.state = State.RUN_CLOSED
                else:
                    # telegram_bot.alarm_corridor()
                    data.state = State.ERROR

            case data.state.RUN_CLOSED:
                # Task running, the subject cannot leave yet
                pass

            case data.state.OPEN_DOOR2:
                # Opening door2
                pass

            case data.state.RUN_OPENED:
                # task running, the subject can leave
                pass

            case data.state.EXIT_UNSAVED:
                # Closing door2, opening door1 (data still not saved)
                pass

            case data.state.SAVE_OUTSIDE:
                # Stopping the task, saving the data; the subject is already outside
                pass

            case data.state.SAVE_INSIDE:
                # Stopping the task, saving the data; the subject is still inside
                pass

            case data.state.WAIT_EXIT:
                # Task finished, waiting for the subject to leave
                pass

            case data.state.EXIT_SAVED:
                # Closing door2, opening door1 (data already saved)
                pass

            case data.state.OPEN_DOOR1:
                # Opening door1, a subject is trapped
                pass

            case data.state.CLOSE_DOOR1:
                # Closing door1, the subject is not trapped anymore
                pass

            case data.state.RUN_TRAPPED:
                # Task running, waiting for the trapped subject to return home
                pass

            case data.state.OPEN_DOOR2_STOP:
                # Opening door2, disconnecting RFID
                pass

            case data.state.OPEN_DOORS_STOP:
                # Opening both doors, disconnecting RFID
                pass

            case data.state.ERROR:
                # Manual intervention required
                pass

            case data.state.MANUAL_RUN:
                # Task is running manuallyy
                pass

            case data.state.SETTINGS:
                # Settings are being changed or task is being manually prepared
                pass

            case data.state.EXIT_GUI:
                # In the GUI window, ready to exit the app
                pass


# start the secondary thread (control of the system)
system_state = threading.Thread(target=system_run, daemon=True)
system_state.start()

# start the primary thread (GUI)
gui = Gui()
