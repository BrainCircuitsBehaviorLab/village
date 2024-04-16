from pybpodapi.com.messaging.base_message import BaseMessage
from pybpodapi.utils import date_parser


class StderrMessage(BaseMessage):
    """
    Stderr message from the server process

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.base_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "stderr"
    MESSAGE_COLOR = (255, 0, 0)

    def __init__(self, content, host_timestamp=None):
        super(StderrMessage, self).__init__(str(content), host_timestamp)

    def __str__(self):
        return "host-time:{0} pc-time:{1} {2}".format(
            self.host_timestamp if self.host_timestamp is not None else "",
            (self.pc_timestamp.strftime("%Y%m%d%H%M%S") if self.pc_timestamp else ""),
            self.content,
        )

    def tolist(self):
        return [
            self.MESSAGE_TYPE_ALIAS,
            str(self.pc_timestamp),
            self.host_timestamp,
            self.content,
            None,
            None,
        ]

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(row[3], float(row[2]) if row[2] else None)
        obj.pc_timestamp = date_parser.parse(row[1])

        return obj
