from pybpodapi.com.messaging.base_message import BaseMessage


class UntaggedMessage(BaseMessage):
    """
    Stderr message from the server process

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.board_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "UNTAGGED"
    MESSAGE_COLOR = (230, 230, 230)

    @classmethod
    def check_type(cls, typestr):
        return True
