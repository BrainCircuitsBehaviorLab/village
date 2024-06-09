from threading import Thread

from village.devices.camera import cam_box, cam_corridor
from village.gui.gui import Gui


# create a secondary thread to run some functions
def system_run() -> None:
    # start the recording of the camera corridor
    cam_corridor.start_record()
    cam_box.start_record()


# start the secondary thread (control of the system)
system_state = Thread(target=system_run)
system_state.start()

# start the primary thread (GUI)
gui = Gui()
