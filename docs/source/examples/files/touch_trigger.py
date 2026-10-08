from village.custom_classes.touch_trigger_base import TouchTriggerBase

# Direct function numbers behind each of the 6 clickable rectangles in
# raspberry_touchscreen.py's menu, in the same order the rectangles are
# laid out (rects[0] -> FUNCTION_IDS[0], etc.). These are exactly
# direct_functions.py's function8/10-14 -- the 6 video_functions.py draw
# generators, skipping function9 (the plain rectangle, since that's what
# the menu itself is drawn with).
FUNCTION_IDS = [8, 10, 11, 12, 13, 14]


def _inside(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class TouchTrigger(TouchTriggerBase):
    """Dispatches a touch to whichever of the two touchscreen tasks is
    running, purely by which attributes it finds on self.task -- neither
    task needs to be named explicitly here.

    - raspberry_touchscreen.py sets self.task.rects (a list of 6 rectangle
      bounds, no controller involved): a touch inside rects[i] runs
      direct_functions.py's function FUNCTION_IDS[i] directly.
    - bpod_touchscreen.py sets self.task.long_rect/short_rect (Bpod-driven):
      a touch inside either one is reported to Bpod as a softcode, and the
      running state machine decides what happens (see bpod_touchscreen.py).
    """

    def __init__(self) -> None:
        super().__init__()

    def trigger(self, x: int, y: int, timestamp: float) -> None:
        task = self.task

        rects = getattr(task, "rects", None)
        if rects is not None:
            for i, rect in enumerate(rects):
                if _inside(x, y, rect):
                    task.execute_function(FUNCTION_IDS[i])
                    task.touch_event.set()
                    return
            return

        long_rect = getattr(task, "long_rect", None)
        short_rect = getattr(task, "short_rect", None)
        if long_rect is not None and short_rect is not None:
            if _inside(x, y, long_rect):
                task.bpod.send_softcode_to_bpod(1)
            elif _inside(x, y, short_rect):
                task.bpod.send_softcode_to_bpod(2)
            return

        super().trigger(x, y, timestamp)
