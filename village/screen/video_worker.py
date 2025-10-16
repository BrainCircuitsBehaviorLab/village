# video_worker.py
from __future__ import annotations

from typing import Optional

import cv2
from PyQt5.QtCore import QMutex, QObject, pyqtSlot
from PyQt5.QtGui import QImage


class VideoWorker(QObject):
    """
    Reads a video using OpenCV and stores only the latest frame as an RGBA8 QImage.
        •	run(): runs in a QThread
        •	stop(): stops the loop
        •	get_latest_qimage(): returns and consumes the latest QImage, or None
    """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self.cap = None
        self.running = True
        self.mtx = QMutex()
        self._last_img: Optional[QImage] = None

    @pyqtSlot()
    def run(self) -> None:
        try:
            print("trying to open video", self.path)
            self.cap = cv2.VideoCapture(self.path)
            if self.cap is None or not self.cap.isOpened():
                self.running = False
                print("failed to open video", self.path)
                return
            while self.running:
                ok, bgr = self.cap.read()
                if not ok:
                    print("end of video", self.path)
                    break
                print("frame")
                rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
                h, w = rgba.shape[:2]
                img = QImage(rgba.data, w, h, QImage.Format_RGBA8888).copy()
                self.mtx.lock()
                self._last_img = img
                self.mtx.unlock()
        finally:
            if self.cap is not None:
                self.cap.release()
            self.running = False

    def get_latest_qimage(self) -> Optional[QImage]:
        self.mtx.lock()
        img = self._last_img
        self._last_img = None  # consume
        self.mtx.unlock()
        return img

    def stop(self) -> None:
        self.running = False
