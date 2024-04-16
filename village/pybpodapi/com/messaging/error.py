from pybpodapi.com.messaging.base_message import BaseMessage


class ErrorMessage(BaseMessage):
    """
    Stderr message from the server process

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.board_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "error"
    MESSAGE_COLOR = (240, 0, 0)
