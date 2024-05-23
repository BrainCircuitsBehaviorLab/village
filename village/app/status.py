from village.classes.enums import Cycle, State
from village.classes.subject import Subject
from village.classes.task import Task


class Status:
    def __init__(self) -> None:
        self.subject = Subject()
        self.task = Task()
        self.state = State.WAIT
        self.cycle = Cycle.AUTO


status = Status()
