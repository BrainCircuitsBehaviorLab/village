from pybpodapi.com.messaging.base_message import BaseMessage
from pybpodapi.utils import date_parser


class SessionInfo(BaseMessage):
    """
    Stderr message from the server process

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.board_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "INFO"
    MESSAGE_COLOR = (150, 150, 255)

    def __init__(self, infoname, infovalue=None, start_time=None, end_time=None):
        super(SessionInfo, self).__init__(infoname, host_timestamp=start_time)
        self._infovalue = infovalue
        self._endtime = end_time

    def tolist(self):
        return [
            self.MESSAGE_TYPE_ALIAS,
            self.pc_timestamp,
            self.host_timestamp,
            self._endtime,
            self.content,
            self._infovalue,
        ]

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(row[4], float(row[2]) if row[2] else None)
        obj.pc_timestamp = date_parser.parse(row[1])
        obj._infovalue = row[5] if len(row) > 5 else None
        return obj

    @property
    def infoname(self):
        return self.content

    @property
    def infovalue(self):
        return self._infovalue
