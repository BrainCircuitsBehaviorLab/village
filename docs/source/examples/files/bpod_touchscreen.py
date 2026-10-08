import math

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
from village.devices.screen import screen

RECT_WIDTH = 200
RECT_HEIGHT = 200
RECT_Y = 200
RECT_GAP = 100


class BpodTouchscreen(TaskBase):
    """Two rectangles on the touchscreen, one shown for longer than the
    other -- touching the one that stays up longer gives water, touching
    the other one (or the response window running out) doesn't.

    Both rectangles appear at the same time (function19, "Show Long/Short
    Rectangles" in direct_functions.py, triggered by SoftCode19 the moment
    "show_rects" starts), but self.short_duration is shorter than
    self.long_duration, so the short one disappears first while the long
    one (and the response window, which lasts the full long_duration) is
    still running. A touch on either rectangle is reported by
    touch_trigger.py as a softcode (1 for the long one, 2 for the short
    one) -- see the touchscreen docs for that pattern.
    """

    def __init__(self):
        super().__init__()

        self.info = """
        Long/Short Touchscreen Task (Bpod)
        ----------------------------------------------------------------
        Two rectangles appear together; one (green) stays up for the full
        response window, the other (red) disappears sooner.
        - Touching the long one (even after the short one has already
          disappeared) delivers water.
        - Touching the short one, or not touching either before the
          response window ends, delivers nothing.
        """

    def start(self):
        """Lays out the two rectangles side by side and looks up the
        reward valve's opening time for self.settings.reward_volume.
        """

        screen_width = screen.width_px
        total_width = 2 * RECT_WIDTH + RECT_GAP
        start_x = (screen_width - total_width) // 2

        self.long_rect = (start_x, RECT_Y, RECT_WIDTH, RECT_HEIGHT)
        self.short_rect = (
            start_x + RECT_WIDTH + RECT_GAP,
            RECT_Y,
            RECT_WIDTH,
            RECT_HEIGHT,
        )
        self.long_duration = self.settings.long_duration
        self.short_duration = self.settings.short_duration

        self.valve_time = self.calibrations.water_calibration.get_valve_time(
            port=2, volume=self.settings.reward_volume
        )

    def create_trial(self):
        # Both rectangles are drawn together (SoftCode19 -> function19);
        # this state's own timer is the full response window, spanning the
        # long rectangle's whole time on screen.
        self.bpod.add_state(
            state_name="show_rects",
            state_timer=self.long_duration,
            state_change_conditions={
                BpodEvent.SoftCode1: "reward",  # touched the long rectangle
                BpodEvent.SoftCode2: "no_reward",  # touched the short one
                BpodEvent.Tup: "miss",
            },
            output_actions=[BpodOutput.SoftCode19],
        )

        self.bpod.add_state(
            state_name="reward",
            state_timer=self.valve_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[BpodOutput.Valve2],
        )

        self.bpod.add_state(
            state_name="no_reward",
            state_timer=0,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

        self.bpod.add_state(
            state_name="miss",
            state_timer=0,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        def visited(state: str) -> bool:
            # Bpod lists a state that was not visited as [nan]
            t = self.trial_data.get(f"STATE_{state}_START", [math.nan])[0]
            return not math.isnan(t)

        if visited("reward"):
            outcome = "correct"
            water = self.settings.reward_volume
        elif visited("no_reward"):
            outcome = "incorrect"
            water = 0
        else:
            outcome = "miss"
            water = 0

        self.register_value("outcome", outcome)
        self.register_value("water", water)

    def close(self):
        pass
