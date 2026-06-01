import bisect
from collections import deque
from dataclasses import dataclass
from threading import Event as ThEvent
from threading import Thread

from village.custom_classes.task import Task
from village.scripts.time_utils import time_utils


@dataclass
class AutonomouseParam:
    """Descriptor for a single inject_trial keyword argument."""

    name: str  # name passed to inject_trial
    type_: type  # float or int for now TODO: support bool, str, etc. if needed, or infer from default
    default: float  # default value
    label: str  # UI label text
    min_val: float = 0.0
    max_val: float = 1.0
    tooltip: str = ""

    def clamp(self, val):
        if self.type_ is bool:
            return bool(val)
        return max(self.min_val, min(self.max_val, self.type_(val)))


class AutoNoMouse_Base:
    """Base class for automated task execution without a real animal.

    To be subclassed in task folder.
    """

    TASK_NAME: str = ""  # to be set in subclass to restrict to a specific task
    PARAMS: list[AutonomouseParam] = []

    def __init__(self, task: Task = None) -> None:
        self.task = task
        self._thread: Thread | None = None
        self._inject_thread: Thread | None = None
        self._stop_event = ThEvent()
        self._inject_stop_event = ThEvent()
        self.trace: deque = deque(maxlen=25 * 5)
        self.position: tuple | None = None
        self._position_log: list[tuple[float, int, int]] = []
        for param in self.PARAMS:
            setattr(self, param.name, param.default)

    def start(self) -> None:
        self._stop_event.clear()
        self.trace.clear()
        self.position = None
        self._position_log.clear()
        self._set_overlay(self)
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._stop_event.is_set() and self.position is None:
            return
        self._stop_event.set()
        self._set_overlay(None)
        self.trace.clear()
        self.position = None
        self.inject_positions()

    def inject_positions(self) -> None:
        """Hacky: (I did not want to modify cam_box code to support this)
        Replaces cam_box position (x, y) lists with AutoNoMouse positions.
        Called when AutoNoMouse stops, just before cam_box.stop_recording(),
        so cam_box.save_csv() picks them up and records them."""
        cam = self.task.cam_box
        if not self._position_log or not hasattr(cam, "camera_timestamps"):
            return

        ts_log = [t for t, _, _ in self._position_log]
        xs_log = [x for _, x, _ in self._position_log]
        ys_log = [y for _, _, y in self._position_log]

        # match each virtual position timestamp to nearest
        # cam ts, then inject (x, y).
        new_x, new_y = [], []
        for ts in cam.camera_timestamps:
            i = bisect.bisect_right(ts_log, ts) - 1
            if i >= 0:
                new_x.append(xs_log[i])
                new_y.append(ys_log[i])
            else:
                new_x.append(-1)
                new_y.append(-1)

        cam.x_positions = new_x
        cam.y_positions = new_y

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

    @property
    def injecting(self) -> bool:
        return self._inject_thread is not None and self._inject_thread.is_alive()

    def stop_inject(self) -> None:
        self._inject_stop_event.set()

    def _run(self) -> None:
        while (
            not self._stop_event.is_set()
            and self.task.current_trial <= self.task.maximum_number_of_trials
        ):
            self.run_trial()
        self.stop()

    def update_params(self, **kwargs) -> None:
        """Update param attributes on a running instance."""
        for param in self.PARAMS:
            if param.name in kwargs:
                setattr(self, param.name, param.clamp(kwargs[param.name]))

    def run_trial(self) -> None:
        """Override in subclass. Sequence of actions to perform for
        one trial, e.g. pokes and position updates."""
        self.wait(1.0)

    def inject_trial(self, *args, **kwargs) -> None:
        """Override in subclass.
        Append one mock trial row directly to session_df."""
        pass

    def inject_trials(self, n: int, interval: float = 1.0, **kwargs) -> None:
        def _run():
            self._inject_stop_event.clear()
            for _ in range(n):
                if self._inject_stop_event.is_set():
                    break
                self.inject_trial(**kwargs)
                self._inject_stop_event.wait(interval)

        self._inject_thread = Thread(target=_run, daemon=True)
        self._inject_thread.start()

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
        self._position_log.append((time_utils.now_timestamp(), pt[0], pt[1]))

    def wait(self, seconds: float) -> None:
        """Sleep for *seconds*, waking early if stop() is called."""
        self._stop_event.wait(seconds)
