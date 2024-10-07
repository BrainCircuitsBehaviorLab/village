import logging

logger = logging.getLogger(__name__)


class InputName(object):
    """
    Input channels available on Bpod box
    These values must be set according to Bpod firmware specification.
    """

    #: Serial1
    Serial1 = "Serial1"

    #: Serial2
    Serial2 = "Serial2"

    #: Serial1_3
    Serial3 = "Serial3"

    #: Serial1_4
    USB1 = "USB1"

    #: BNC1
    BNC1 = "BNC1"

    #: BNC2
    BNC2 = "BNC2"

    #: Wire1
    Wire1 = "Wire1"

    #: Wire2
    Wire2 = "Wire2"

    #: Input port 1
    Port1 = "Port1"

    #: Input port 2
    Port2 = "Port2"

    #: Input port 3
    Port3 = "Port3"

    #: Input port 4
    Port4 = "Port4"

    #: Input port 5
    Port5 = "Port5"

    #: Input port 6
    Port6 = "Port6"

    #: Input port 7
    Port7 = "Port7"

    #: Input port 8
    Port8 = "Port8"
