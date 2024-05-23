import io
import sys

from village.pybpodapi.com.messaging.stderr import StderrMessage


class StderrBuffer(io.StringIO):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def write(self, msg):
        self.session += StderrMessage(msg)

    def flush(self):
        sys.__stderr__.flush()
