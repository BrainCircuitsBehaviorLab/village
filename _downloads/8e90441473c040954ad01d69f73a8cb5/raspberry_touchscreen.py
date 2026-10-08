import threading

from village.custom_classes.task_base import TaskBase
from village.devices.screen import screen
from village.scripts.time_utils import time_utils

TRIAL_TIMEOUT = 60  # seconds to wait for a touch
N_RECTS = 6
RECT_WIDTH = 150
RECT_HEIGHT = 150
RECT_Y = 200
RECT_GAP = 40  # horizontal gap between rectangles


class RaspberryTouchscreen(TaskBase):
    """No Bpod, no Arduino (BEHAVIOR_CONTROLLER = OTHER): 6 rectangles are
    laid out horizontally across the touchscreen (function18, "Show
    Touchscreen Menu" in direct_functions.py). Touching one of them runs a
    different video_functions.py stimulus, reacted to in touch_trigger.py --
    the 6 non-rectangle draw generators (circle, moving circle, triangle,
    image, image with alpha, video), in that order. Each trial just waits
    for any touch, or a timeout.

    Required setup (in SETTINGS, not in this file):
    - Touchscreen must be enabled and configured (see Screen Integration
      docs).
    """

    def __init__(self):
        super().__init__()

        self.info = f"""
        Touchscreen Menu Task
        ----------------------------------------------------------------
        No controller involved -- driven entirely by touch position,
        reacted to in touch_trigger.py. Each trial:
        - 6 rectangles are shown side by side; touching one plays a
          different visual stimulus (see touch_trigger.py) and the trial
          ends right after.
        - Otherwise, the trial ends anyway after {TRIAL_TIMEOUT} seconds.
        """

    def start(self):
        """Lays out the 6 rectangles evenly across the screen width and
        draws them once -- touch_trigger.py reads self.rects on every touch
        to work out which one (if any) was hit.
        """

        screen_width = screen.width_px
        total_width = N_RECTS * RECT_WIDTH + (N_RECTS - 1) * RECT_GAP
        start_x = (screen_width - total_width) // 2

        self.rects = [
            (start_x + i * (RECT_WIDTH + RECT_GAP), RECT_Y, RECT_WIDTH, RECT_HEIGHT)
            for i in range(N_RECTS)
        ]

        # Set by touch_trigger.py's TouchTrigger.trigger() the moment one
        # of self.rects is touched; create_trial just waits on it.
        self.touch_event = threading.Event()
        self.touched_index: int | None = None

        self.execute_function(18)  # "Show Touchscreen Menu"

    def create_trial(self):
        """Waits for touch_trigger.py to react to a touch, or for
        TRIAL_TIMEOUT seconds to pass -- then ends the trial either way."""

        self.touch_event.clear()
        self.touched_index = None

        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)

        deadline = t0 + TRIAL_TIMEOUT
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            if self.touch_event.wait(timeout=0.05):
                break

        self.register_end_trial(time_utils.now_timestamp())

    def after_trial(self):
        self.register_value("touched", self.touch_event.is_set())
        self.register_value("water", 0)

    def close(self):
        pass
