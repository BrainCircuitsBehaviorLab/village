from village.app.utils import utils
from village.classes.protocols import PyBpodProtocol
from village.pybpodapi.protocol import Bpod, StateMachine


class PyBpod(PyBpodProtocol):
    def __init__(self) -> None:
        self.bpod = Bpod()
        self.sma = StateMachine(self.bpod)

    def create_state_machine(self) -> None:
        self.sma = StateMachine(self.bpod)

    def send_and_run_state_machine(self) -> None:
        self.bpod.send_state_machine(self.sma)
        self.bpod.run_state_machine(self.sma)


def get_bpod() -> PyBpodProtocol:
    try:
        bpod = PyBpod()
        utils.log("Successfully imported bpod")
        return bpod
    except Exception as e:
        utils.log("Could not create bpod", exception=e)
        return PyBpodProtocol()


bpod = get_bpod()
