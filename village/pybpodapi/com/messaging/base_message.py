from datetime import datetime as datetime_now

from pybpodapi.utils import date_parser


class BaseMessage(object):
    """
    Represents a session message
    It may have been originated from the board of from pc
    """

    MESSAGE_TYPE_ALIAS = "MESSAGE"
    MESSAGE_COLOR = (200, 200, 200)

    def __init__(self, content, host_timestamp=None):
        self.pc_timestamp = datetime_now.now()
        self.host_timestamp = host_timestamp
        self.content = content

    def __str__(self):
        return "host-time:{0} pc-time:{1} {2}".format(
            self.host_timestamp if self.host_timestamp is not None else "",
            (
                self.pc_timestamp.strftime("%Y%m%d%H%M%S")
                if self.pc_timestamp is not None
                else ""
            ),
            self.content,
        )

    @classmethod
    def check_type(cls, typestr):
        """
        Returns True if the typestr represents the class
        """
        return typestr == cls.MESSAGE_TYPE_ALIAS

    def tolist(self):
        return [self.host_timestamp, None, self.content, None]

    @classmethod
    def fromlist(cls, row):
        """
        Returns True if the typestr represents the class
        """
        obj = cls(row[4], float(row[2]) if row[2] else None)
        obj.pc_timestamp = date_parser.parse(row[1])

        return obj
