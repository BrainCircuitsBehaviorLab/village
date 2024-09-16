class TempSensor:
    def __init__(self) -> None:
        self._temp: str = "0"

    def get(self) -> str:
        return self._temp


temp_sensor = TempSensor()
