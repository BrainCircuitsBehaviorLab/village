from pybpodapi.com.messaging.base_message import BaseMessage


class DebugMessage(BaseMessage):
    """Information line for things like experiment name , task name, board id, etc."""

    MESSAGE_TYPE_ALIAS = "debug"
    MESSAGE_COLOR = (200, 200, 200)
