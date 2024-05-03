class Motor:
    def __init__(self) -> None:
        self.speed = 30

    def open_door1(self) -> None:
        print("Opening door 1")

    def open_door2(self) -> None:
        print("Opening door 2")

    def close_door1(self) -> None:
        print("Closing door 1")

    def close_door2(self) -> None:
        print("Closing door 2")


motor = Motor()
