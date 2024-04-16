import logging

logger = logging.getLogger(__name__)


class SendMessageHeader(object):
    """
    Define names for message headers sent to the Bpod device.

    The message header is the first byte (character) on a message sent.
    """

    #: Request initialization handshake
    HANDSHAKE = "6"

    #: Request firmware build number
    FIRMWARE_VERSION = "F"

    #: Reset session clock
    RESET_CLOCK = "*"

    #: Pause ongoing trial (We recommend using computer-side pauses between trials,
    # to keep data uniform)
    PAUSE_TRIAL = "$"

    #: Return timestamp transmission scheme
    GET_TIMESTAMP_TRANSMISSION = "G"

    #: Request hardware configuration
    HARDWARE_DESCRIPTION = "H"

    #: Request enable input ports
    ENABLE_PORTS = "E"

    #: Set sync channel and sync mode
    SYNC_CHANNEL_MODE = "K"

    #: Send new compressed state matrix
    NEW_STATE_MATRIX = "C"

    #: Request to run state matrix now
    RUN_STATE_MACHINE = "R"

    #: Load serial message
    LOAD_SERIAL_MESSAGE = "L"

    #: Reset serial messages to equivalent byte codes (i.e. message# 4 = one byte, 0x4)
    RESET_SERIAL_MESSAGES = ">"

    #: Override digital hardware state
    OVERRIDE_DIGITAL_HW_STATE = "O"

    #: Send byte to hardware serial channel 1-3
    SEND_TO_HW_SERIAL = "U"

    #: Request end of connection now
    DISCONNECT = "Z"

    #: Get the modules connected to bpod
    GET_MODULES = "M"

    #: Set module relay
    SET_MODULE_RELAY = "J"

    #: Write to the module
    WRITE_TO_MODULE = "T"

    #: Echo soft code
    ECHO_SOFTCODE = "S"

    #: Manual override: execute virtual event
    MANUAL_OVERRIDE_EXEC_EVENT = "V"

    #: Trigger soft code
    TRIGGER_SOFTCODE = "~"

    #: Exit state matrix and return data
    EXIT_AND_RETURN = "X"
