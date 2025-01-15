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
    SoftCode21 = ("SoftCode", 21)
    SoftCode22 = ("SoftCode", 22)
    SoftCode23 = ("SoftCode", 23)
    SoftCode24 = ("SoftCode", 24)
    SoftCode25 = ("SoftCode", 25)
    SoftCode26 = ("SoftCode", 26)
    SoftCode27 = ("SoftCode", 27)
    SoftCode28 = ("SoftCode", 28)
    SoftCode29 = ("SoftCode", 29)
    SoftCode30 = ("SoftCode", 30)
    SoftCode31 = ("SoftCode", 31)
    SoftCode32 = ("SoftCode", 32)
    SoftCode33 = ("SoftCode", 33)
    SoftCode34 = ("SoftCode", 34)
    SoftCode35 = ("SoftCode", 35)
    SoftCode36 = ("SoftCode", 36)
    SoftCode37 = ("SoftCode", 37)
    SoftCode38 = ("SoftCode", 38)
    SoftCode39 = ("SoftCode", 39)
    SoftCode40 = ("SoftCode", 40)
    SoftCode41 = ("SoftCode", 41)
    SoftCode42 = ("SoftCode", 42)
    SoftCode43 = ("SoftCode", 43)
    SoftCode44 = ("SoftCode", 44)
    SoftCode45 = ("SoftCode", 45)
    SoftCode46 = ("SoftCode", 46)
    SoftCode47 = ("SoftCode", 47)
    SoftCode48 = ("SoftCode", 48)
    SoftCode49 = ("SoftCode", 49)
    SoftCode50 = ("SoftCode", 50)
    SoftCode51 = ("SoftCode", 51)
    SoftCode52 = ("SoftCode", 52)
    SoftCode53 = ("SoftCode", 53)
    SoftCode54 = ("SoftCode", 54)
    SoftCode55 = ("SoftCode", 55)
    SoftCode56 = ("SoftCode", 56)
    SoftCode57 = ("SoftCode", 57)
    SoftCode58 = ("SoftCode", 58)
    SoftCode59 = ("SoftCode", 59)
    SoftCode60 = ("SoftCode", 60)
    SoftCode61 = ("SoftCode", 61)
    SoftCode62 = ("SoftCode", 62)
    SoftCode63 = ("SoftCode", 63)
    SoftCode64 = ("SoftCode", 64)
    SoftCode65 = ("SoftCode", 65)
    SoftCode66 = ("SoftCode", 66)
    SoftCode67 = ("SoftCode", 67)
    SoftCode68 = ("SoftCode", 68)
    SoftCode69 = ("SoftCode", 69)
    SoftCode70 = ("SoftCode", 70)
    SoftCode71 = ("SoftCode", 71)
    SoftCode72 = ("SoftCode", 72)
    SoftCode73 = ("SoftCode", 73)
    SoftCode74 = ("SoftCode", 74)
    SoftCode75 = ("SoftCode", 75)
    SoftCode76 = ("SoftCode", 76)
    SoftCode77 = ("SoftCode", 77)
    SoftCode78 = ("SoftCode", 78)
    SoftCode79 = ("SoftCode", 79)
    SoftCode80 = ("SoftCode", 80)
    SoftCode81 = ("SoftCode", 81)
    SoftCode82 = ("SoftCode", 82)
    SoftCode83 = ("SoftCode", 83)
    SoftCode84 = ("SoftCode", 84)
    SoftCode85 = ("SoftCode", 85)
    SoftCode86 = ("SoftCode", 86)
    SoftCode87 = ("SoftCode", 87)
    SoftCode88 = ("SoftCode", 88)
    SoftCode89 = ("SoftCode", 89)
    SoftCode90 = ("SoftCode", 90)
    SoftCode91 = ("SoftCode", 91)
    SoftCode92 = ("SoftCode", 92)
    SoftCode93 = ("SoftCode", 93)
    SoftCode94 = ("SoftCode", 94)
    SoftCode95 = ("SoftCode", 95)
    SoftCode96 = ("SoftCode", 96)
    SoftCode97 = ("SoftCode", 97)
    SoftCode98 = ("SoftCode", 98)

    #: GlobalTimerTrig
    GlobalTimer1Trig = ("GlobalTimerTrig", 1)
    GlobalTimer2Trig = ("GlobalTimerTrig", 2)
    GlobalTimer3Trig = ("GlobalTimerTrig", 3)
    GlobalTimer4Trig = ("GlobalTimerTrig", 4)
    GlobalTimer5Trig = ("GlobalTimerTrig", 5)

    #: GlobalTimerCancel
    GlobalTimer1Cancel = ("GlobalTimerCancel", 1)
    GlobalTimer2Cancel = ("GlobalTimerCancel", 2)
    GlobalTimer3Cancel = ("GlobalTimerCancel", 3)
    GlobalTimer4Cancel = ("GlobalTimerCancel", 4)
    GlobalTimer5Cancel = ("GlobalTimerCancel", 5)

    #: GlobalCounterReset
    GlobalCounterReset = "GlobalCounterReset"
    GlobalCounter1Reset = ("GlobalCounterReset", 1)
    GlobalCounter2Reset = ("GlobalCounterReset", 2)
    GlobalCounter3Reset = ("GlobalCounterReset", 3)
    GlobalCounter4Reset = ("GlobalCounterReset", 4)
    GlobalCounter5Reset = ("GlobalCounterReset", 5)
