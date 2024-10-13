import threading
from collections import deque
from datetime import datetime
from typing import Deque

import serial

from village.classes.enums import Active
from village.data import data
from village.settings import settings
from village.time_utils import time_utils


class Rfid:
    def __init__(self, port="/dev/ttyAMA0", baudrate=9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self.multiple = False
        self.time_detections = settings.get("TIME_BETWEEN_DETECTIONS")

        self.id = ""
        self.id_history: Deque[tuple[str, datetime]] = deque()

        self.s = serial.Serial(self.port, self.baudrate, timeout=0.1)

        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.running = True
        self.thread.start()

    def read_serial(self) -> None:
        while self.running:
            try:
                line = self.s.readline().decode("utf-8")
                if line == "":
                    self.id_history.append((self.id, time_utils.now()))
                    self.clean_old_ids()
                    self.update_multiple()
                    self.id = line
            except UnicodeDecodeError:
                break

    def clean_old_ids(self) -> None:
        current_time = time_utils.now()
        while self.id_history:
            diff = current_time - self.id_history[0][1]
            if diff.total_seconds() > self.time_detections:
                self.id_history.popleft()
            else:
                break

    def update_multiple(self) -> None:
        unique_ids = set(id for id, _ in self.id_history)
        self.multiple = len(unique_ids) >= 2

    def stop(self) -> None:
        self.running = False
        self.s.close()
        self.thread.join()

    def get_id(self) -> tuple[str, bool]:
        if data.tag_reader == Active.ON:
            return (self.id, self.multiple)
        else:
            return ("", False)


rfid = Rfid()
