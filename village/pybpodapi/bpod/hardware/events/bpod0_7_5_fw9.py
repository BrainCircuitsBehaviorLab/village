import logging

from pybpodapi.bpod.hardware.events.base_eventname import BaseEventName

logger = logging.getLogger(__name__)


class EventName(BaseEventName):
    """
    Input event codes
    These values must be set according to Bpod firmware specification.
    """

    #: Serial1_1
    Serial1_1 = "Serial1_1"

    #: Serial1_2
    Serial1_2 = "Serial1_2"

    #: Serial1_3
    Serial1_3 = "Serial1_3"

    #: Serial1_4
    Serial1_4 = "Serial1_4"

    #: Serial1_5
    Serial1_5 = "Serial1_5"

    #: Serial1_6
    Serial1_6 = "Serial1_6"

    #: Serial1_7
    Serial1_7 = "Serial1_7"

    #: Serial1_8
    Serial1_8 = "Serial1_8"

    #: Serial1_9
    Serial1_9 = "Serial1_9"

    #: Serial1_10
    Serial1_10 = "Serial1_10"

    #: Serial2_1
    Serial2_1 = "Serial2_1"

    #: Serial2_2
    Serial2_2 = "Serial2_2"

    #: Serial2_3
    Serial2_3 = "Serial2_3"

    #: Serial2_4
    Serial2_4 = "Serial2_4"

    #: Serial2_5
    Serial2_5 = "Serial2_5"

    #: Serial2_6
    Serial2_6 = "Serial2_6"

    #: Serial2_7
    Serial2_7 = "Serial2_7"

    #: Serial2_8
    Serial2_8 = "Serial2_8"

    #: Serial2_9
    Serial2_9 = "Serial2_9"

    #: Serial2_10
    Serial2_10 = "Serial2_10"

    #: Serial3_1
    Serial3_1 = "Serial3_1"

    #: Serial3_2
    Serial3_2 = "Serial3_2"

    #: Serial3_3
    Serial3_3 = "Serial3_3"

    #: Serial3_4
    Serial3_4 = "Serial3_4"

    #: Serial3_5
    Serial3_5 = "Serial3_5"

    #: Serial3_6
    Serial3_6 = "Serial3_6"

    #: Serial3_7
    Serial3_7 = "Serial3_7"

    #: Serial3_8
    Serial3_8 = "Serial3_8"

    #: Serial3_9
    Serial3_9 = "Serial3_9"

    #: Serial3_10
    Serial3_10 = "Serial3_10"

    #: SoftCode1
    SoftCode1 = "SoftCode1"

    #: SoftCode2
    SoftCode2 = "SoftCode2"

    #: SoftCode3
    SoftCode3 = "SoftCode3"

    #: SoftCode4
    SoftCode4 = "SoftCode4"

    #: SoftCode5
    SoftCode5 = "SoftCode5"

    #: SoftCode6
    SoftCode6 = "SoftCode6"

    #: SoftCode7
    SoftCode7 = "SoftCode7"

    #: SoftCode8
    SoftCode8 = "SoftCode8"

    #: SoftCode9
    SoftCode9 = "SoftCode9"

    #: SoftCode10
    SoftCode10 = "SoftCode10"

    #: BNC1In
    BNC1In = "BNC1In"

    #: BNC1Out
    BNC1Out = "BNC1Out"

    #: BNC2In
    BNC2In = "BNC2In"

    #: BNC2Out
    BNC2Out = "BNC2Out"

    #: Wire1In
    Wire1In = "Wire1In"

    #: Wire1Out
    Wire1Out = "Wire1Out"

    #: Wire2In
    Wire2In = "Wire2In"

    #: Wire2Out
    Wire2Out = "Wire2Out"

    #: Input port 1
    Port1In = "Port1In"

    #: Output port 1
    Port1Out = "Port1Out"

    #: Input port 2
    Port2In = "Port2In"

    #: Output port 2
    Port2Out = "Port2Out"

    #: Input port 3
    Port3In = "Port3In"

    #: Output port 3
    Port3Out = "Port3Out"

    #: Input port 4
    Port4In = "Port4In"

    #: Output port 4
    Port4Out = "Port4Out"

    #: Input port 5
    Port5In = "Port5In"

    #: Output port 5
    Port5Out = "Port5Out"

    #: Input port 6
    Port6In = "Port6In"

    #: Output port 6
    Port6Out = "Port6Out"

    #: Input port 7
    Port7In = "Port7In"

    #: Output port 7
    Port7Out = "Port7Out"

    #: Input port 8
    Port8In = "Port8In"

    #: Output port 8
    Port8Out = "Port8Out"

    #: GlobalTimer1_Start
    GlobalTimer1_Start = "_GlobalTimer1_Start"

    #: GlobalTimer2_Start
    GlobalTimer2_Start = "_GlobalTimer2_Start"

    #: GlobalTimer3_Start
    GlobalTimer3_Start = "_GlobalTimer3_Start"

    #: GlobalTimer4_Start
    GlobalTimer4_Start = "_GlobalTimer4_Start"

    #: GlobalTimer5_Start
    GlobalTimer5_Start = "_GlobalTimer5_Start"

    #: GlobalTimer1_End
    GlobalTimer1_End = "_GlobalTimer1_End"

    #: GlobalTimer2_End
    GlobalTimer2_End = "_GlobalTimer2_End"

    #: GlobalTimer3_End
    GlobalTimer3_End = "_GlobalTimer3_End"

    #: GlobalTimer4_End
    GlobalTimer4_End = "_GlobalTimer4_End"

    #: GlobalTimer5_End
    GlobalTimer5_End = "_GlobalTimer5_End"

    #: GlobalCounter1_End
    GlobalCounter1_End = "_GlobalCounter1_End"

    #: GlobalCounter2_End
    GlobalCounter2_End = "_GlobalCounter2_End"

    #: GlobalCounter3_End
    GlobalCounter3_End = "_GlobalCounter3_End"

    #: GlobalCounter4_End
    GlobalCounter4_End = "_GlobalCounter4_End"

    #: GlobalCounter5_End
    GlobalCounter5_End = "_GlobalCounter5_End"

    #: Condition1
    Condition1 = "_Condition1"

    #: Condition2
    Condition2 = "_Condition2"

    #: Condition3
    Condition3 = "_Condition3"

    #: Condition4
    Condition4 = "_Condition4"

    #: Condition5
    Condition5 = "_Condition5"

    #: Serial1Jump
    Serial1Jump = "Serial1Jump"

    #: Serial2Jump
    Serial2Jump = "Serial2Jump"

    #: Serial3Jump
    Serial3Jump = "Serial3Jump"

    #: SoftJump
    SoftJump = "SoftJump"

    #: Tup
    Tup = "_Tup"
