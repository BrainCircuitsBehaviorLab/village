import logging

from pybpodapi.com.messaging.debug import DebugMessage
from pybpodapi.com.messaging.error import ErrorMessage
from pybpodapi.com.messaging.stderr import StderrMessage
from pybpodapi.com.messaging.stdout import StdoutMessage
from pybpodapi.com.messaging.warning import WarningMessage

logger = logging.getLogger(__name__)


class MessageParser(object):

    COLUMN_SEPARATOR = ";"

    MESSAGES_TYPES_CLASSES = [
        ErrorMessage,
        DebugMessage,
        StderrMessage,
        StdoutMessage,
        WarningMessage,
    ]

    def fromlist(self, row):
        """
        Parses messages saved on session history file

        .. seealso::

            :py:meth:
            `pybpodgui_plugin.api.models.session.session_io.SessionIO.load_contents`


        :param str txtline: file line entry
        :returns: list of history messages
        :rtype: list(BaseMessage)
        """
        if row is None or len(row) == 0:
            return ErrorMessage("Parse error: line is empty")

        msg = None
        try:
            msgtype = row[0]

            for msgtype_class in self.MESSAGES_TYPES_CLASSES:
                if msgtype_class.check_type(msgtype):
                    msg = msgtype_class.fromlist(row)
                    break
        except Exception:
            logger.warning(
                "Could not parse bpod message: {0}".format(str(row)),
                exc_info=True,
            )
            return ErrorMessage(row)  # default case

        return msg
