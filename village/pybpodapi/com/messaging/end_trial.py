from pybpodapi.com.messaging.base_message import BaseMessage


class EndTrial(BaseMessage):
    """
    Stderr message from the server process

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.board_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "END-TRIAL"
    MESSAGE_COLOR = (0, 100, 200)
