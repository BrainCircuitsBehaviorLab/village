from village.custom_classes.camera_trigger_base import CameraTriggerBase
from village.devices.camera import Camera
from village.devices.led_strip import led_strip
from village.scripts.time_utils import time_utils


class CameraTrigger(CameraTriggerBase):
    """Reacts to two independent BOX areas, one per no-controller/Bpod demo
    task -- the area that fired is what tells them apart, no task-name
    check needed:

    - Area 1: raspberry_area1_sound.py (no controller). Plays the sound the
      task already loaded (function4, "Play Loaded Sound" in
      direct_functions.py) and lights LED 0 on the strip, once per trial.
    - Area 2: bpod_area2_sound.py (Bpod-governed). Reports the entry to
      Bpod as a softcode -- the running state machine is what actually
      plays the sound and opens the valve (see bpod_area2_sound.py).

    Both use a self.task.areaN_event (created and cleared each trial by the
    running task) the same way: it's what create_trial waits on to know
    when to move on, and what keeps this from re-firing on every single
    frame while the animal stays inside the area (areaN_is_triggered stays
    True the whole time it's in there, not just on entry).
    """

    def __init__(self) -> None:
        super().__init__()

    def trigger(self, cam: Camera) -> None:
        if cam.name != "BOX":
            return

        # getattr guards: this trigger fires for whichever task happens to
        # be running, and area1_event/area2_event only exist on the two
        # tasks that actually use them.
        area1_event = getattr(self.task, "area1_event", None)
        if (
            cam.area1_is_triggered
            and area1_event is not None
            and not area1_event.is_set()
        ):
            self.task.register_raspberry_event(
                "area1_entered", time_utils.now_timestamp()
            )
            self.task.execute_function(4)  # "Play Loaded Sound"

            led_strip.set_led_color(0, 255, 255, 255)
            led_strip.update_strip()

            area1_event.set()

        area2_event = getattr(self.task, "area2_event", None)
        if (
            cam.area2_is_triggered
            and area2_event is not None
            and not area2_event.is_set()
        ):
            self.task.register_raspberry_event(
                "area2_entered", time_utils.now_timestamp()
            )
            # Bpod -> Raspberry Pi direction would be a softcode; this is
            # the reverse (Raspberry Pi -> Bpod), used to wake up a state
            # that's waiting on BpodEvent.SoftCode1 (see bpod_area2_sound.py).
            self.task.bpod.send_softcode_to_bpod(1)
            area2_event.set()
