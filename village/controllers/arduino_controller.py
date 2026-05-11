from village.controllers.trial_recorder import TrialRecorder


class ArduinoController:
    def __init__(self) -> None:
        super().__init__()

        self.connected = False
        self.recorder = TrialRecorder(same_clock=False)

    def check_connection(self) -> None:
        self.error = ""

    def connect(self) -> None:
        """Connects to the Arduino and initializes session."""
        self.connected = True

    def close(self) -> None:
        """Closes the Arduino connection and session."""
        self.connected = False


arduino = ArduinoController()
