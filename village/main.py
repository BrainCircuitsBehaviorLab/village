# VARIABLES WE CAN IMPORT IN ANY FILE
# settings (no dependencies)
# utils (no dependencies)
# data (depends on settings and utils)
#   contains subject, task,
#   subjects, events, sessions_summary, water_calibration, sound_calibration

# DEVICES WE CAN IMPORT IN ANY FILE (depend on settings and utils)
# bpod
# cam_box
# cam_corridor
# motor1
# motor2
# rfid
# sound_device
# temp_scale


# When launching the application the following processes are executed:
# 1. start importing data from village.data.py
#               this causes the import of settings and utils
# 2. import settings from village.settings.py
#               if they don't exist they are automatically created from factory settings
# 3. import utils from village.utils.py
# 4. continue importing data
#               read the path setting for the project directory
#               if the directory doesn't exist create it and its subdirectories
# 5. continue importing data
#               read the data from project directory (events, sessions_summary,
#               subjects, water_calibration, sound_calibration)
#               if the files don't exist create them
# 6. continue importing data
#               if the project directory is the demo directory and the code is empty,
#               download the code from the github repository
# 7. continue importing data
#               set the logprotocol to the events collection
# 8. continue importing data
#               log that the village has started
# 9. try import bpod from village.devices.bpod.py and log the result
# 10. try to import cam_corridor and cam_box from village.devices.camera.py and
#               log the result
# 11. assign the bpod to the task in data
# 12. import all tasks from the code directory and log the result


import time
from threading import Thread

from village.classes.enums import State
from village.data import data
from village.devices.bpod import bpod
from village.devices.camera import cam_box, cam_corridor
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.gui.gui import Gui
from village.utils import utils

# init
data.task.bpod = bpod
data.import_all_tasks()


# create a secondary thread to run some function
def system_run() -> None:

    cam_corridor.start_record()
    cam_box.start_record()

    i = 0
    while True:
        i += 1
        time.sleep(1)
        if i % 10 == 0:
            utils.log("counter: " + str(i) + " es un texto largo que yo quiero poner a")

        match data.state:
            case data.state.WAIT:
                # all subjects at home, waiting for rfid detection
                if data.tag_reader == data.tag_reader.ON:
                    tag: str = rfid.get()
                    if tag != "":
                        data.state = State["DETECTION"]

            case data.state.DETECTION:
                # getting subject name and task, checking areas and minimum time
                if (
                    data.get_subject_from_tag(tag)
                    and data.subject.get_data_from_subject_series()
                    and cam_corridor.areas_corridor_ok()
                ):
                    # data.security_chrono.reset()
                    data.state = State["SECURITY_CHECK"]
                else:
                    data.state = State["SECURITY_WAIT"]

            # case data.state.SECURITY_CHECK:
            #     # corridor empty for some time after detection

            case data.state.ACCESS:
                # closing door1, opening door2
                motor1.close()
                motor2.open()

            case data.state.LAUNCH:
                # launching the task
                pass
            case data.state.ACTION:
                # waiting for first action in behavioral box
                pass
            case data.state.CLOSE:
                # closing door2
                pass
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
system_state = Thread(target=system_run)
system_state.start()

# start the primary thread (GUI)
gui = Gui()
