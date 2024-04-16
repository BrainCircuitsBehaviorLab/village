from pybpodapi.com.messaging.base_message import BaseMessage


class StdoutMessage(BaseMessage):
    """
    Print statement on bpod protocol

    .. seealso::

        :py:class:`pybpodgui_plugin.com.messaging.base_message.BoardMessage`

    """

    MESSAGE_TYPE_ALIAS = "stdout"
    MESSAGE_COLOR = (150, 150, 150)
