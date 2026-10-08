import math
import threading

from sound_functions import whitenoise_generator

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
from village.devices.sound_device import sound_device

TRIAL_TIMEOUT = 60  # seconds to wait for the animal to enter area 2


class BpodArea2Sound(TaskBase):
    """Same idea as raspberry_area1_sound.py, but Bpod-governed and using
    BOX area 2 instead of area 1 -- and water is delivered together with
    the sound, not just a sound.

    Area 2 entry is reacted to by camera_trigger.py (in this same code
    directory), which reports it to Bpod as a softcode
    (self.task.bpod.send_softcode_to_bpod(1)) the moment the animal enters.
    create_trial's state machine waits on that softcode, then plays the
    sound (via another softcode, Bpod -> Raspberry Pi this time, triggering
    direct_functions.py's function4) and opens the reward valve in the same
    state, so both start together.

    Required setup (in SETTINGS, not in this file):
    - CAM_BOX_TRACKING_POSITION must be ON.
    - BOX area 2 must be set to TRIGGER status (and positioned/sized as
      wanted) in the box area settings.
    Without both, area2_is_triggered never becomes True and every trial
    will just time out.
    """

    def __init__(self):
        super().__init__()

        self.info = f"""
        Area 2 Sound + Water Task (Bpod)
        ----------------------------------------------------------------
        Driven by camera position tracking (reacted to in
        camera_trigger.py) and a Bpod state machine. Each trial:
        - If the animal enters BOX area 2, camera_trigger.py tells Bpod via
          a softcode; the state machine then plays a sound and opens the
          reward valve at the same time. The trial ends right after.
        - Otherwise, the trial ends anyway after {TRIAL_TIMEOUT} seconds,
          with no reward.

        Requires CAM_BOX_TRACKING_POSITION ON and BOX area 2 set to TRIGGER
        (see SETTINGS).
        """

    def start(self):
        """Loads the sound once -- the "deliver" state's softcode replays
        this same loaded sound every trial, no reload needed -- and looks
        up the reward valve's opening time for self.settings.reward_volume.
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

        self.valve_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )

        if not self.cam_box.tracking:
            print(
                "Warning: CAM_BOX_TRACKING_POSITION is OFF -- "
                "area2 will never trigger."
            )
        if not self.cam_box.areas_trigger[1]:
            print(
                "Warning: BOX area 2 is not set to TRIGGER -- "
                "area2 will never trigger."
            )

        # Set by camera_trigger.py's CameraTrigger.trigger() the moment
        # area 2 is entered; the state machine below just waits on it.
        self.area2_event = threading.Event()

    def create_trial(self):
        """Waits (via Bpod) for camera_trigger.py to report area 2 entry,
        then plays the sound and delivers water together; times out with
        no reward if the animal never enters.
        """

        self.area2_event.clear()

        self.bpod.add_state(
            state_name="wait_area2",
            state_timer=TRIAL_TIMEOUT,
            state_change_conditions={
                BpodEvent.SoftCode1: "deliver",
                BpodEvent.Tup: "exit",
            },
            output_actions=[],
        )

        # SoftCode4 (Bpod -> Raspberry Pi) triggers direct_functions.py's
        # function4 ("Play Loaded Sound"); the valve opens in the same
        # state, so the sound and the water start at the same time.
        self.bpod.add_state(
            state_name="deliver",
            state_timer=self.valve_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[BpodOutput.SoftCode4, BpodOutput.Valve1],
        )

    def after_trial(self):
        # Bpod lists a state that was not visited as [nan]
        t_deliver = self.trial_data.get("STATE_deliver_START", [math.nan])[0]
        entered = not math.isnan(t_deliver)
        self.register_value("entered_area2", entered)
        self.register_value("water", self.settings.reward_volume if entered else 0)

    def close(self):
        pass
