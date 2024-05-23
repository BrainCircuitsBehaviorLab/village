import io
import sys

from village.pybpodapi.com.messaging.stdout import StdoutMessage


class StdoutBuffer(io.StringIO):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def write(self, msg):
        self.session += StdoutMessage(msg)

    def flush(self):
        sys.__stdout__.flush()
