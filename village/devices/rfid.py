import threading
import time
from collections import deque
from typing import Tuple

import serial


class Rfid:
    def __init__(self, port="/dev/serial0", baudrate=9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self.multiple = False
        self.running = False

        self.id = ""
        self.id_history: deque = deque()

        self.s = serial.Serial(self.port, self.baudrate, timeout=0.1)

        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.running = True
        self.thread.start()

    def read_serial(self) -> None:
        while self.running:
            # print("reading")
            try:
                line = self.s.readline().decode("utf-8").strip()
                # print(line)

                if line:
                    self.id_history.append((self.id, time.time()))
                    self.clean_old_ids()
                    self.update_multiple()
                    self.id = line

            except UnicodeDecodeError:
                break

    def clean_old_ids(self) -> None:
        current_time = time.time()
        while self.id_history and current_time - self.id_history[0][1] > 15:
            self.id_history.popleft()

    def update_multiple(self) -> None:
        unique_ids = set(id for id, _ in self.id_history)
        self.multiple = len(unique_ids) >= 2

    def stop(self) -> None:
        self.running = False
        self.s.close()
        self.thread.join()

    def get_id(self) -> Tuple[str, bool]:
        return (self.id, self.multiple)


rfid = Rfid()
