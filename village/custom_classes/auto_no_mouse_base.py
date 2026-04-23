import threading
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from village.custom_classes.task import Task


class AutoNoMouse_Base:
    """Base class for automated task execution without a real animal.

    To be subclassed in task folder.
    """

    def __init__(self, task: "Task") -> None:
        self.task = task
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.trace: deque = deque(maxlen=25 * 5)
        self.position: tuple | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self.trace.clear()
        self.position = None
        self._set_overlay(self)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._set_overlay(None)
        self.trace.clear()
        self.position = None

    def _set_overlay(self, instance: "AutoNoMouse_Base | None") -> None:
        try:
            itd = self.task.cam_box.items_to_draw
            itd["auto_no_mouse"] = instance is not None
            itd["auto_instance"] = instance
        except AttributeError:
            pass

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while (not self._stop_event.is_set() and
               self.task.current_trial <= self.task.maximum_number_of_trials):
            self.run_trial()

    def run_trial(self) -> None:
        """Override in subclass. Sequence of actions to perform for
        one trial, e.g. pokes and position updates. """
        self.wait(1.0)

    def inject_trial(self, p_correct_left: float = 1.0,
                     p_correct_right: float = 1.0) -> None:
        """Override in subclass.
        Append one mock trial row directly to session_df."""
        pass

    def inject_trials(self, n: int, p_correct_left: float = 1.0,
                      p_correct_right: float = 1.0) -> None:
        for _ in range(n):
            self.inject_trial(p_correct_left, p_correct_right)

    def poke(self, port: int, duration: float = 0.1) -> None:
        """Simulate a nose-poke in and out on port."""
        self.task.bpod.manual_override_input(f"Port{port}In")
        self._stop_event.wait(duration)
        self.task.bpod.manual_override_input(f"Port{port}Out")

    def set_position(self, x: float, y: float) -> None:
        """Update the virtual animal's position and trace."""
        self.task.current_x = x
        self.task.current_y = y
        pt = (int(x), int(y))
        self.position = pt
        self.trace.append(pt)

    def wait(self, seconds: float) -> None:
        """Sleep for *seconds*, waking early if stop() is called."""
        self._stop_event.wait(seconds)
