import logging

from pybpodapi.com.messaging.base_message import BaseMessage
from pybpodapi.utils import date_parser

logger = logging.getLogger(__name__)


class StateTransition(BaseMessage):
    """
    Store timestamps for a specific state occurrence of the state machine

    :ivar str name: name of the state
    :ivar list(StateDuration) timestamps: a list of timestamps (start and end)
    that corresponds to occurrences of this state
    """

    MESSAGE_TYPE_ALIAS = "TRANSITION"
    MESSAGE_COLOR = (0, 200, 0)

    def __init__(self, state_name, host_timestamp):
        """

        :param str name: name of the state

        """
        super().__init__(state_name, host_timestamp)

    def tolist(self):
        return [
            self.host_timestamp,
            None,
            self.show_name,
            None,
        ]

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(row[4], float(row[2]) if row[2] else None)
        obj.pc_timestamp = date_parser.parse(row[1])

        return obj

    @property
    def show_name(self):
        return "_Transition_to_" + self.content
