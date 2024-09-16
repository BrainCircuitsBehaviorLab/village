class Scale:
    def __init__(self) -> None:
        self.calibration: float = 4.0
        self.weight: float = 0.0

    def get(self) -> float:
        return self.weight


scale = Scale()
