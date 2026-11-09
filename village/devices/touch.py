from __future__ import annotations

import threading
import time
import traceback

import evdev

from village.classes.null_classes import NullTouch
from village.manager import manager
from village.scripts.error_queue import error_queue
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import settings

# Seconds to wait before trying to open a disconnected touchscreen again: the
# first wait, doubled after every failed attempt up to the maximum.
RECONNECT_FIRST_S = 5
RECONNECT_MAX_S = 60


def _find_touchscreen_path() -> str:
    """Returns the path of the device whose name matches TOUCHSCREEN_DEVICE."""
    name = settings.get("TOUCHSCREEN_DEVICE")
    for path in evdev.list_devices():
        try:
            if evdev.InputDevice(path).name == name:
                return path
        except Exception:
            continue
    raise RuntimeError(f"Touchscreen device '{name}' not found.")


class Touch:
    """Reads touch events from a Linux input device via evdev.

    Works with both single-touch (ABS_X/ABS_Y) and multi-touch
    (ABS_MT_POSITION_X/Y) devices, treating all contacts as a single pointer.

    Touch events are debounced by TOUCH_INTERVAL seconds. Each event that
    passes the debounce filter is forwarded directly to
    manager.touch_trigger.trigger(x, y).

    If the device fails while Village runs (e.g. it is disconnected), an alarm
    is sent and it is opened again as soon as it is back (see _reconnect).
    """

    def __init__(self) -> None:
        path = _find_touchscreen_path()
        self.device = evdev.InputDevice(path)
        self.device.grab()  # exclusive access to the device
        self.touch_interval: float = settings.get("TOUCH_INTERVAL")
        touch_resolution_x, touch_resolution_y = settings.get("TOUCH_RESOLUTION")
        self.width_px, self.height_px = settings.get("SCREEN_RESOLUTION")
        self._px_per_touch_x: float = self.width_px / touch_resolution_x
        self._px_per_touch_y: float = self.height_px / touch_resolution_y
        self._running = True
        self._stop_event = threading.Event()
        self.error = ""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        """Reads the touchscreen until stop(). If the device fails (e.g. the USB
        is disconnected), it is closed and opened again as soon as it is back."""
        while self._running:
            try:
                self._read_events()
            except Exception:
                if not self._running:
                    break  # closed by stop()
                try:
                    error_queue.put_nowait(
                        (
                            "touchscreen",
                            "Touchscreen disconnected, trying to reconnect",
                            traceback.format_exc(),
                        )
                    )
                except Exception:
                    pass
                self._reconnect()

    def _read_events(self) -> None:
        """Reads the events of the device and handles every touch. Returns when
        stop() is called; raises if the device fails."""
        _x: int = 0
        _y: int = 0
        _last_t: float = 0.0

        for event in self.device.read_loop():
            if not self._running:
                return
            if event.type == evdev.ecodes.EV_ABS:
                if event.code in (
                    evdev.ecodes.ABS_X,
                    evdev.ecodes.ABS_MT_POSITION_X,
                ):
                    _x = event.value
                elif event.code in (
                    evdev.ecodes.ABS_Y,
                    evdev.ecodes.ABS_MT_POSITION_Y,
                ):
                    _y = event.value
            elif event.type == evdev.ecodes.EV_SYN:
                t = event.timestamp()
                if t - _last_t >= self.touch_interval:
                    px = int(_x * self._px_per_touch_x)
                    py = int(_y * self._px_per_touch_y)
                    _last_t = t
                    if manager.triggers_active():
                        ts = t - (time.time() - time_utils.now_timestamp())
                        self._handle_touch(px, py, ts)

    def _reconnect(self) -> None:
        """Closes the failed device and opens it again once it is back.

        Tries every RECONNECT_FIRST_S seconds, twice as long after every failed
        attempt (up to RECONNECT_MAX_S), so a device that stays disconnected is
        not looked for in a loop. The device is found again by its name
        (TOUCHSCREEN_DEVICE): its path (/dev/input/eventN) may change when it
        is plugged in again.
        """
        try:
            self.device.close()
        except Exception:
            pass
        delay = RECONNECT_FIRST_S
        while not self._stop_event.wait(delay):
            try:
                device = evdev.InputDevice(_find_touchscreen_path())
                device.grab()  # exclusive access to the device
            except Exception:
                delay = min(delay * 2, RECONNECT_MAX_S)
                continue
            self.device = device
            log.info("Touchscreen reconnected")
            return

    def _handle_touch(self, px: int, py: int, ts: float) -> None:
        """Records the touch in the trial data and calls the touch trigger.

        An error here (usually in the trigger written by the user) is reported
        and this touch is skipped, but the touchscreen keeps being read.
        """
        try:
            manager.task.recorder.add_raspberry_event(f"touch_{px}_{py}", ts)
            manager.touch_trigger.trigger(px, py, ts)
        except Exception:
            try:
                error_queue.put_nowait(
                    (
                        "touchscreen",
                        "Error in the touch trigger",
                        traceback.format_exc(),
                    )
                )
            except Exception:
                pass

    def stop(self) -> None:
        """Stops the reader thread."""
        self._running = False
        self._stop_event.set()
        try:
            self.device.close()
        except Exception:
            pass


def get_touch() -> Touch | NullTouch:
    from village.classes.enums import ScreenActive

    if settings.get("USE_SCREEN") != ScreenActive.TOUCHSCREEN:
        return NullTouch()
    try:
        ts = Touch()
        return ts
    except Exception:
        null_touch = NullTouch()
        null_touch.error = log.clean_text(
            traceback.format_exc(), "Could not initialize touchscreen"
        )
        return null_touch


touch = get_touch()
