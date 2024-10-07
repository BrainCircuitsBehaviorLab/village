import logging

logger = logging.getLogger(__name__)


class OutputChannel(object):
    """
    Available output channels
    These values must be set according to Bpod firmware specification.
    """

    # PWM
    PWM1 = "PWM1"
    PWM2 = "PWM2"
    PWM3 = "PWM3"
    PWM4 = "PWM4"
    PWM5 = "PWM5"
    PWM6 = "PWM6"
    PWM7 = "PWM7"
    PWM8 = "PWM8"

    #: Valve
    Valve = "Valve"
    Valve1 = ("Valve", 1)
    Valve2 = ("Valve", 2)
    Valve3 = ("Valve", 3)
    Valve4 = ("Valve", 4)

    #: BNC
    BNC1High = ("BNC1", 3)
    BNC1Low = ("BNC1", 0)
    BNC2High = ("BNC2", 3)
    BNC2Low = ("BNC2", 0)

    #: Wire
    Wire1High = ("Wire1", 3)
    Wire1Low = ("Wire1", 0)
    Wire2High = ("Wire2", 3)
    Wire2Low = ("Wire2", 0)
    Wire3High = ("Wire3", 3)
    Wire3Low = ("Wire3", 0)
    Wire4High = ("Wire4", 3)
    Wire4Low = ("Wire4", 0)

    #: Serial
    Serial1 = "Serial1"
    Serial2 = "Serial2"
    Serial3 = "Serial3"
    Serial4 = "Serial4"
    Serial5 = "Serial5"

    #: SoftCode
    SoftCode1 = ("SoftCode", 1)
    SoftCode2 = ("SoftCode", 2)
    SoftCode3 = ("SoftCode", 3)
    SoftCode4 = ("SoftCode", 4)
    SoftCode5 = ("SoftCode", 5)
    SoftCode6 = ("SoftCode", 6)
    SoftCode7 = ("SoftCode", 7)
    SoftCode8 = ("SoftCode", 8)
    SoftCode9 = ("SoftCode", 9)
    SoftCode10 = ("SoftCode", 10)
    SoftCode11 = ("SoftCode", 11)
    SoftCode12 = ("SoftCode", 12)
    SoftCode13 = ("SoftCode", 13)
    SoftCode14 = ("SoftCode", 14)
    SoftCode15 = ("SoftCode", 15)
    SoftCode16 = ("SoftCode", 16)
    SoftCode17 = ("SoftCode", 17)
    SoftCode18 = ("SoftCode", 18)
    SoftCode19 = ("SoftCode", 19)
    SoftCode20 = ("SoftCode", 20)

    #: GlobalTimerTrig
    GlobalTimer1Trig = ("_GlobalTimerTrig", 1)
    GlobalTimer2Trig = ("_GlobalTimerTrig", 2)
    GlobalTimer3Trig = ("_GlobalTimerTrig", 3)
    GlobalTimer4Trig = ("_GlobalTimerTrig", 4)
    GlobalTimer5Trig = ("_GlobalTimerTrig", 5)

    #: GlobalTimerCancel
    GlobalTimer1Cancel = ("_GlobalTimerCancel", 1)
    GlobalTimer2Cancel = ("_GlobalTimerCancel", 2)
    GlobalTimer3Cancel = ("_GlobalTimerCancel", 3)
    GlobalTimer4Cancel = ("_GlobalTimerCancel", 4)
    GlobalTimer5Cancel = ("_GlobalTimerCancel", 5)

    #: GlobalCounterReset
    GlobalCounterReset = "_GlobalCounterReset"
    GlobalCounter1Reset = ("_GlobalCounterReset", 1)
    GlobalCounter2Reset = ("_GlobalCounterReset", 2)
    GlobalCounter3Reset = ("_GlobalCounterReset", 3)
    GlobalCounter4Reset = ("_GlobalCounterReset", 4)
    GlobalCounter5Reset = ("_GlobalCounterReset", 5)
