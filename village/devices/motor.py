class Motor:
    def __init__(self, name: int, pin: int) -> None:
        self.name = name
        self.pin = pin
        self.time_open = 200
        self.time_close = 200

    def open(self) -> None:
        print("Opening door")

    def close(self) -> None:
        print("Closing door")


motor1 = Motor(1, 12)
motor2 = Motor(2, 13)
