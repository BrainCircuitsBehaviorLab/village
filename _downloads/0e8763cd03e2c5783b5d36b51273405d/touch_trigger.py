from village.custom_classes.touch_trigger_base import TouchTriggerBase


def _inside(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class TouchTrigger(TouchTriggerBase):
    """Dispatches a touch to whichever of the two touchscreen tasks is
    running, purely by which attributes it finds on self.task -- neither
    task needs to be named explicitly here.

    - raspberry_stimulus_menu.py sets self.task.rects (the rectangles of its
      menu, no controller involved): a touch inside rects[i] is reported to
      the task in self.task.touched_index, and the task shows the stimulus
      of that rectangle (see raspberry_stimulus_menu.py).
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
            # only the first touch of each trial counts
            if task.touch_event.is_set():
                return
            for i, rect in enumerate(rects):
                if _inside(x, y, rect):
                    task.touched_index = i
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
