class Rfid:
    def __init__(self) -> None:
        self.id: str = ""

    def read(self) -> None:
        self.id = "1234567890"

    def get_id(self) -> str | None:
        return self.id


rfid = Rfid()
