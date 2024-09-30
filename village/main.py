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
                # all subjects at home, waiting for a not empty rfid detection
                if data.tag_reader == data.tag_reader.ON:
                    id, multiple = rfid.get_id()
                    if id != "":
                        data.state = State["DETECTION"]
            case data.state.DETECTION:
                # getting subject data, checking areas and minimum time
                if (
                    data.get_subject_from_tag(id)
                    and data.subject.get_data_from_subject_series()
                    and data.subject.minimum_time_ok()
                    and cam_corridor.areas_corridor_ok()
                    and not data.multiple_detections(multiple)
                ):
                    data.state = State["ACCESS"]
                else:
                    data.state = State["WAIT"]

            case data.state.ACCESS:
                # closing door1, opening door2
                motor1.close()
                motor2.open()
                data.state = State["LAUNCH"]

            case data.state.LAUNCH:
                # launching the task
                if data.launch_task():
                    data.state = State["ACTION"]
                else:
                    data.state = State["STOP"]

            case data.state.ACTION:
                # waiting for first action in behavioral box
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
                    data.state = State["STOP"]
                if data.first_action:
                    data.state = State["CLOSE"]
            case data.state.CLOSE:
                if cam_corridor.area_3_empty():
                    motor2.close()
                    data.state = State["RUN_CLOSED"]
                else:
                    # telegram_bot.alarm_corridor()
                    data.state = State["ERROR"]

            case data.state.RUN_CLOSED:
                # task running, subject can not leave
                pass
            case data.state.OPEN:
                # opening door2
                pass
            case data.state.RUN_OPENED:
                # task running, subject can leave
                pass
            case data.state.EXIT_UNSAVED:
                # closing door2, opening door1
                pass
            case data.state.SAVE_OUTSIDE:
                # stopping the task, saving the data
                pass
            case data.state.SAVE_INSIDE:
                # stopping the task, saving the data
                pass
            case data.state.WAIT_EXIT:
                # waiting for the subject to leave
                pass
            case data.state.EXIT_SAVED:
                # closing door2, opening door1
                pass
            case data.state.OPEN_TRAPPED:
                # opening door2, subject trapped
                pass
            case data.state.CLOSE_TRAPPED:
                # closing door2, subject trapped
                pass
            case data.state.RUN_TRAPPED:
                # task running, waiting for the trapped subject to go home
                pass
            case data.state.STOP:
                # opening door2, disconnecting rfid
                pass
            case data.state.PREPARATION:
                # task being prepared manually
                pass
            case data.state.MANUAL:
                # task running manually
                pass
            case data.state.SETTINGS:
                # settings being changed manually
                pass
            case data.state.SETTINGS_CHANGED:
                # settings changed manually
                pass
            case data.state.EXIT_APP:
                # exiting the app
                pass
            case data.state.END:
                # end
                break


# start the secondary thread (control of the system)
system_state = threading.Thread(target=system_run)
system_state.start()

# start the primary thread (GUI)
gui = Gui()
