from threading import Lock

lock = Lock()


class Rfid:
    def __init__(self) -> None:
        self.id: str = ""

    def read(self) -> None:
        # in a thread update the value of self.id
        with lock:
            pass

    def get(self) -> str:
        with lock:
            return self.id


rfid = Rfid()
