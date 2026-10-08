import threading

from sound_functions import whitenoise_generator

from village.custom_classes.task_base import TaskBase
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils

TRIAL_TIMEOUT = 60  # seconds to wait for the animal to enter area 1


class RaspberryArea1Sound(TaskBase):
    """No Bpod, no Arduino (BEHAVIOR_CONTROLLER = OTHER): area 1 entry is
    reacted to by a custom CameraTriggerBase (camera_trigger.py, in this
    same code directory), which plays the sound and lights an LED strip LED
    the moment the animal enters. create_trial just waits for that to
    happen (or times out), then ends the trial.

    Required setup (in SETTINGS, not in this file):
    - CAM_BOX_TRACKING_POSITION must be ON.
    - BOX area 1 must be set to TRIGGER status (and positioned/sized as
      wanted) in the box area settings.
    Without both, area1_is_triggered never becomes True and every trial
    will just time out.
    """

    def __init__(self):
        super().__init__()

        self.info = f"""
        Area 1 Sound Task
        ----------------------------------------------------------------
        No controller involved -- driven entirely by camera position
        tracking, reacted to in camera_trigger.py. Each trial:
        - If the animal enters BOX area 1, camera_trigger.py plays a sound
          and lights an LED on the strip; the trial ends right after.
        - Otherwise, the trial ends anyway after {TRIAL_TIMEOUT} seconds.

        Requires CAM_BOX_TRACKING_POSITION ON and BOX area 1 set to TRIGGER
        (see SETTINGS).
        """

    def start(self):
        """Loads the sound once -- camera_trigger.py's function4 call
        replays this same loaded sound every time area 1 is entered, no
        reload needed.
        """

        gain_left = self.calibrations.sound_calibration.get_sound_gain(
            speaker=0, dB=70, sound_name="whitenoise"
        )
        gain_right = self.calibrations.sound_calibration.get_sound_gain(
            speaker=1, dB=70, sound_name="whitenoise"
        )
        sound_left = whitenoise_generator(duration=1, gain=gain_left)
        sound_right = whitenoise_generator(duration=1, gain=gain_right)
        sound_device.load(left=sound_left, right=sound_right)

        if not self.cam_box.tracking:
            print(
                "Warning: CAM_BOX_TRACKING_POSITION is OFF -- "
                "area1 will never trigger."
            )
        if not self.cam_box.areas_trigger[0]:
            print(
                "Warning: BOX area 1 is not set to TRIGGER -- "
                "area1 will never trigger."
            )

        # Set by camera_trigger.py's CameraTrigger.trigger() the moment
        # area 1 is entered; create_trial just waits on it.
        self.area1_event = threading.Event()

    def create_trial(self):
        """Waits for camera_trigger.py to react to area 1, or for
        TRIAL_TIMEOUT seconds to pass -- then ends the trial either way."""

        self.area1_event.clear()

        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)

        deadline = t0 + TRIAL_TIMEOUT
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            if self.area1_event.wait(timeout=0.05):
                break

        self.register_end_trial(time_utils.now_timestamp())

    def after_trial(self):
        self.register_value("entered_area1", self.area1_event.is_set())
        self.register_value("water", 0)

    def close(self):
        pass
