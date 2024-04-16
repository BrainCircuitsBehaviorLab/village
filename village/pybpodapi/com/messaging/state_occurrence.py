import logging

from pybpodapi.com.messaging.base_message import BaseMessage
from pybpodapi.utils import date_parser

logger = logging.getLogger(__name__)


class StateOccurrence(BaseMessage):
    """
    Store timestamps for a specific state occurrence of the state machine

    :ivar str name: name of the state
    :ivar list(StateDuration) timestamps: a list of timestamps (start and end)
    that corresponds to occurrences of this state
    """

    MESSAGE_TYPE_ALIAS = "STATE"
    MESSAGE_COLOR = (0, 100, 0)

    def __init__(self, state_name, host_timestamp, end_timestamp):
        """

        :param str name: name of the state
        """
        super(StateOccurrence, self).__init__(state_name, host_timestamp)

        self.start_timestamp = host_timestamp
        self.end_timestamp = end_timestamp

    def tolist(self):
        return [self.start_timestamp, self.end_timestamp, self.show_name, None]

    @property
    def show_name(self):
        return "STATE_" + self.content

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(
            row[4],
            float(row[2]) if row[2] else None,
            float(row[3]) if row[3] else None,
        )
        obj.pc_timestamp = date_parser.parse(row[1])

        return obj

    @property
    def state_name(self):
        return self.content
