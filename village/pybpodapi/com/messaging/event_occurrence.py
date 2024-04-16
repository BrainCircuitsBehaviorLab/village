from pybpodapi.com.messaging.base_message import BaseMessage
from pybpodapi.utils import date_parser


class EventOccurrence(BaseMessage):
    """
    Message from board that represents state change (an event)

    :ivar str event_name: name of the event
    :ivar int event_id: index of the event
    :ivar float board_timestamp: timestamp associated with this event (from bpod)

    """

    MESSAGE_TYPE_ALIAS = "EVENT"

    def __init__(self, event_id, event_name, host_timestamp=None):
        """

        :param event_id:
        :param event_name:
        :param host_timestamp:
        """
        super(EventOccurrence, self).__init__(event_name, host_timestamp)
        self._event_id = event_id

    @property
    def event_name(self):
        return self.content

    @property
    def event_id(self):
        return self._event_id

    def tolist(self):
        return [self.host_timestamp, None, self.event_name, None]

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(int(row[4]), row[5], float(row[2]) if row[2] else None)
        obj.pc_timestamp = date_parser.parse(row[1])

        return obj
