import traceback

from village.classes.protocols import PyBpodProtocol
from village.log import log
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
        log.info("Bpod successfully initialized")
        return bpod
    except Exception:
        log.error("Could not initialize bpod", exception=traceback.format_exc())
        return PyBpodProtocol()


bpod = get_bpod()
