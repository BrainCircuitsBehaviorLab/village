from __future__ import annotations

import threading
import traceback

import evdev

from village.classes.null_classes import NullTouch
from village.scripts.error_queue import error_queue
from village.scripts.log import log
from village.settings import settings


class TouchEvent:
    """A single touch contact point."""

    __slots__ = ("x", "y", "timestamp")

    def __init__(self, x: int, y: int, timestamp: float) -> None:
        self.x = x
        self.y = y
        self.timestamp = timestamp


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

    Touch events are debounced by TOUCH_INTERVAL seconds.
    Captured events are stored in self.events as TouchEvent objects.
    """

    def __init__(self) -> None:
        path = _find_touchscreen_path()
        self.device = evdev.InputDevice(path)
        self.device.set_clock_id(1)  # CLOCK_MONOTONIC — same as time.monotonic()
        self.touch_interval: float = settings.get("TOUCH_INTERVAL")
        touch_resolution_x, touch_resolution_y = settings.get("TOUCH_RESOLUTION")
        self.width_px, self.height_px = settings.get("SCREEN_RESOLUTION")
        self.width_mm, self.height_mm = settings.get("SCREEN_SIZE_MM")
        self._px_per_touch_x: float = self.width_px / touch_resolution_x
        self._px_per_touch_y: float = self.height_px / touch_resolution_y
        self._mm_per_touch_x: float = self.width_mm / touch_resolution_x
        self._mm_per_touch_y: float = self.height_mm / touch_resolution_y
        self.events: list[TouchEvent] = []
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        _x: int = 0
        _y: int = 0
        _last_t: float = 0.0

        try:
            for event in self.device.read_loop():
                if not self._running:
                    break
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
                        with self._lock:
                            self.events.append(TouchEvent(px, py, t))
                        _last_t = t
        except Exception:
            try:
                error_queue.put_nowait(("touchscreen", traceback.format_exc()))
            except Exception:
                pass

    def get_events(self) -> list[TouchEvent]:
        """Returns a snapshot of all captured events and clears the list."""
        with self._lock:
            snapshot = self.events.copy()
            self.events.clear()
        return snapshot

    def clear(self) -> None:
        """Clears all captured events."""
        with self._lock:
            self.events.clear()

    def stop(self) -> None:
        """Stops the reader thread."""
        self._running = False
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
        log.info("Touchscreen successfully initialized")
        return ts
    except Exception:
        log.error("Could not initialize touchscreen", exception=traceback.format_exc())
        return NullTouch()


touch = get_touch()
