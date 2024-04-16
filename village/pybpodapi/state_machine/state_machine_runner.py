import logging

from pybpodapi.state_machine.state_machine_builder import StateMachineBuilder

logger = logging.getLogger(__name__)


class StateMachineRunner(StateMachineBuilder):
    """
    Extends state machine with running logic

    :ivar bool is_running: Whether this state machine is being run on bpod hardware
    :ivar int current_state: Holds state machine current state while running
    """

    def __init__(self, bpod):
        StateMachineBuilder.__init__(self, bpod)

        self.is_running = False  # type: bool

        self.current_state = 0  # type: int

    #########################################
    ############## PROPERTIES ###############
    #########################################

    @property
    def is_running(self):
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value


class StateMachineRunnerError(Exception):
    pass
