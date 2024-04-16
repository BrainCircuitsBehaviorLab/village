import logging

logger = logging.getLogger(__name__)


class OutputChannel(object):
    """
    Available output channels
    These values must be set according to Bpod firmware specification.
    """

    #: LED
    LED = "LED"

    #: Valve
    Valve = "Valve"

    #: Serial 1
    Serial1 = "Serial1"

    #: Serial 2
    Serial2 = "Serial2"

    #: Serial 3
    Serial3 = "Serial3"

    #: SoftCode
    SoftCode = "SoftCode"

    #: ValveState
    ValveState = "ValveState"

    #: BNC1
    BNC1 = "BNC1"

    #: BNC2
    BNC2 = "BNC2"

    #: Wire1
    Wire1 = "Wire1"

    #: Wire2
    Wire2 = "Wire2"

    #: Wire3
    Wire3 = "Wire3"

    #: Wire3
    Wire4 = "Wire4"

    #: PWM1
    PWM1 = "PWM1"

    #: PWM2
    PWM2 = "PWM2"

    #: PWM3
    PWM3 = "PWM3"

    #: PWM4
    PWM4 = "PWM4"

    #: PWM5
    PWM5 = "PWM5"

    #: PWM6
    PWM6 = "PWM6"

    #: PWM7
    PWM7 = "PWM7"

    #: PWM8
    PWM8 = "PWM8"

    #: GlobalTimerTrig
    GlobalTimerTrig = "_GlobalTimerTrig"

    #: GlobalTimerCancel
    GlobalTimerCancel = "_GlobalTimerCancel"

    #: GlobalCounterReset
    GlobalCounterReset = "_GlobalCounterReset"
