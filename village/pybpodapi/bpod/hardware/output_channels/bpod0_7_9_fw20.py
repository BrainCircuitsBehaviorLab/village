import logging

logger = logging.getLogger(__name__)


class OutputChannel(object):
    """
    Available output channels
    These values must be set according to Bpod firmware specification.
    """

    #: LED
    LED = "LED"

    #: Valve1
    Valve1 = "Valve1"

    #: Valve2
    Valve2 = "Valve2"

    #: Valve3
    Valve3 = "Valve3"

    #: Valve4
    Valve4 = "Valve4"

    #: Serial 1
    Serial1 = "Serial1"

    #: Serial 2
    Serial2 = "Serial2"

    #: Serial 3
    Serial3 = "Serial3"

    #: Serial 4
    Serial4 = "Serial4"

    #: Serial 5
    Serial5 = "Serial5"

    #: SoftCode
    SoftCode = "SoftCode"

    #: BNC1
    BNC1 = "BNC1"

    #: BNC2
    BNC2 = "BNC2"

    #: PWM1
    PWM1 = "PWM1"

    #: PWM2
    PWM2 = "PWM2"

    #: PWM3
    PWM3 = "PWM3"

    #: PWM4
    PWM4 = "PWM4"

    #: GlobalTimerTrig
    GlobalTimerTrig = "_GlobalTimerTrig"

    #: GlobalTimerCancel
    GlobalTimerCancel = "_GlobalTimerCancel"

    #: GlobalCounterReset
    GlobalCounterReset = "_GlobalCounterReset"
