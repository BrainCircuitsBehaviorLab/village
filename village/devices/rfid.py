import threading
from collections import deque
from datetime import datetime
from typing import Deque

import serial

from village.classes.enums import Active
from village.manager import manager
from village.scripts import time_utils
from village.settings import settings


class Rfid:
    def __init__(self, port="/dev/ttyAMA0", baudrate=9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self.multiple = False
        self.time_detections = settings.get("TIME_BETWEEN_DETECTIONS")

        self.id = ""
        self.id_history: Deque[tuple[str, datetime]] = deque()
        self.reading = True

        self.s = serial.Serial(self.port, self.baudrate, timeout=0.1)

        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.running = True
        self.thread.start()

    def read_serial(self) -> None:
        while self.running:
            try:
                line = self.s.readline().decode("utf-8").strip()
                line = "".join(char for char in line if char.isprintable())
                if len(line) < 8:
                    continue
                self.id = line[-10:]
                # print(self.id)
                self.id_history.append((self.id, time_utils.now()))
                self.clean_old_ids()
                self.update_multiple()
            except UnicodeDecodeError:
                pass

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
        self.multiple = len(unique_ids) > 1

    def stop(self) -> None:
        self.running = False
        self.s.close()
        self.thread.join()

    def get_id(self) -> tuple[str, bool]:
        if manager.rfid_reader == Active.ON:
            value = (self.id, self.multiple)
            self.id = ""
            self.multiple = False
            return value
        else:
            self.id = ""
            self.multiple = False
            return ("", False)


rfid = Rfid()
