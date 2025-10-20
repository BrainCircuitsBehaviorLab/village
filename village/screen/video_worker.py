from __future__ import annotations

import queue
import time
import traceback
from typing import Optional

import cv2
from PyQt5.QtCore import QMutex, QObject, pyqtSlot
from PyQt5.QtGui import QImage

from village.scripts.error_queue import error_queue


class VideoWorker(QObject):

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self.cap = None
        self.running = True
        self.mtx = QMutex()

        self._latest_img: Optional[QImage] = None
        self._latest_idx: int = -1

        self._served_img: Optional[QImage] = None
        self._served_idx: int = -1

        self._fps: float = 0.0
        self._frame_dt: float = 0.0
        self._play_start: float = 0.0
        self._started: bool = False

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.cap = cv2.VideoCapture(self.path)
            if self.cap is None or not self.cap.isOpened():
                self.running = False
                return

            try:
                fps = float(self.cap.get(cv2.CAP_PROP_FPS))
                print("fps:", fps)
            except Exception:
                fps = 30.0

            self._fps = fps
            self._frame_dt = 1.0 / fps
            self._play_start = time.monotonic()
            self._started = True

            produced_idx = -1

            while self.running:
                ok, bgr = self.cap.read()
                if not ok:
                    break

                rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
                h, w = rgba.shape[:2]
                img = QImage(rgba.data, w, h, QImage.Format_RGBA8888).copy()

                produced_idx += 1
                self.mtx.lock()
                self._latest_img = img
                self._latest_idx = produced_idx
                self.mtx.unlock()

        except Exception:
            try:
                error_queue.put_nowait(("video", traceback.format_exc()))
            except queue.Full:
                pass
        finally:
            if self.cap is not None:
                self.cap.release()
            self.running = False

    def get_latest_qimage(self) -> Optional[QImage]:
        if not self._started:
            return None

        now = time.monotonic()
        target_idx = (
            int((now - self._play_start) / self._frame_dt) if self._frame_dt > 0 else 0
        )

        print(target_idx)

        if self._served_idx == target_idx and self._served_img is not None:
            return self._served_img

        self.mtx.lock()
        latest_img = self._latest_img
        latest_idx = self._latest_idx
        self.mtx.unlock()

        if latest_img is None or latest_idx < 0:
            return self._served_img

        if latest_idx >= target_idx:
            self._served_idx = target_idx
            self._served_img = latest_img
            return self._served_img

        return self._served_img

    def stop(self) -> None:
        self.running = False
