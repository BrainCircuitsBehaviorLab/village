import logging

logger = logging.getLogger(__name__)


class ReceiveMessageHeader(object):
    """
    Define names for message headers received from the Bpod device.

    The message header is the first byte (character) on a message received.
    """

    #: Success code from HANDSHAKE command
    HANDSHAKE_OK = "5"

    #: Success code from ENABLE_PORTS command
    ENABLE_PORTS_OK = 1

    #: Success code from SYNC_CHANNEL_MODE command
    SYNC_CHANNEL_MODE_OK = 1

    #: Success code from RUN_STATE_MACHINE command
    STATE_MACHINE_INSTALLATION_STATUS = 1

    #: Success code from LOAD_SERIAL_MESSAGE command
    LOAD_SERIAL_MESSAGE_OK = 1

    #: Success code from RESET_SERIAL_MESSAGES command
    RESET_SERIAL_MESSAGES = 1

    #: Module requested event
    MODULE_REQUESTED_EVENT = ord("#")

    #: Module events names
    MODULE_EVENT_NAMES = ord("E")
