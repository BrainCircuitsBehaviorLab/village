import logging

logger = logging.getLogger(__name__)


class ChannelType(object):
    """
    Define if channel type is input or output.
    These values must be set according to Bpod firmware specification.
    """

    #: Input channel
    INPUT = 1

    #: Output channel
    OUTPUT = 2


class ChannelName(object):
    """
    Available channel names.
    These values must be set according to Bpod firmware specification.
    """

    #: Analog channel with PWM support (e.g. Led)
    PWM = "PWM"

    #: Analog channel for connecting a valve
    VALVE = "Valve"

    #: BNC channel
    BNC = "BNC"

    #: Wire channel
    WIRE = "Wire"

    #: Serial channel
    SERIAL = "Serial"


class EventsPositions(object):
    """ """

    def __init__(self):
        self.Event_USB = 0  # type: int
        self.Event_Port = 0  # type: int
        self.Event_BNC = 0  # type: int
        self.EventWire = 0  # type: int
        self.globalTimerStart = 0  # type: int
        self.globalTimerEnd = 0  # type: int
        self.globalTimerTrigger = 0  # type: int
        self.globalTimerCancel = 0  # type: int
        self.globalCounter = 0  # type: int
        self.condition = 0  # type: int
        self.jump = 0  # type: int
        self.Tup = 0  # type: int
        self.output_USB = 0  # type: int
        self.output_VALVE = 0  # type: int
        self.output_BNC = 0  # type: int
        self.output_Wire = 0  # type: int
        self.output_PWM = 0  # type: int


class Channels(object):
    """
    Bpod main class
    """

    def __init__(self):
        self.event_names = []
        self.input_channel_names = []
        self.output_channel_names = []
        self.events_positions = EventsPositions()

    def setup_input_channels(self, hardware, modules):
        """
        Generate event and input channel names
        """
        Pos = 0
        nUSB = 0
        nUART = 0
        nBNCs = 0
        nWires = 0
        nPorts = 0

        for i in range(len(hardware.inputs)):
            if hardware.inputs[i] == "U":

                nUART += 1
                module = modules[nUART - 1]
                module_name = ""
                if module.connected:
                    module_name = module.name
                    self.input_channel_names += [module_name]
                else:
                    module_name = "Serial" + str(nUART)
                    self.input_channel_names += [module_name]

                n_module_event_names = len(module.event_names)

                for j in range(module.n_serial_events):
                    if j < n_module_event_names:
                        self.event_names += [module_name + "_" + module.event_names[j]]
                    else:

                        self.event_names += [module_name + "_" + str(j + 1)]
                    Pos += 1

            elif hardware.inputs[i] == "X":
                if nUSB == 0:
                    self.events_positions.Event_USB = Pos
                nUSB += 1
                self.input_channel_names += ["USB" + str(nUSB)]
                loops_n = int(hardware.max_serial_events / (len(modules) + 1))
                for j in range(loops_n):
                    self.event_names += ["SoftCode" + str(j + 1)]
                    Pos += 1
            elif hardware.inputs[i] == "P":
                if nPorts == 0:
                    self.events_positions.Event_Port = Pos
                nPorts += 1
                self.input_channel_names += ["Port" + str(nPorts)]
                self.event_names += [self.input_channel_names[-1] + "In"]
                Pos += 1
                self.event_names += [self.input_channel_names[-1] + "Out"]
                Pos += 1
            elif hardware.inputs[i] == "B":
                if nBNCs == 0:
                    self.events_positions.Event_BNC = Pos
                nBNCs += 1
                self.input_channel_names += ["BNC" + str(nBNCs)]
                self.event_names += [self.input_channel_names[-1] + "High"]
                Pos += 1
                self.event_names += [self.input_channel_names[-1] + "Low"]
                Pos += 1
            elif hardware.inputs[i] == "W":
                if nWires == 0:
                    self.events_positions.Event_Wire = Pos
                nWires += 1
                self.input_channel_names += ["Wire" + str(nWires)]
                self.event_names += [self.input_channel_names[-1] + "High"]
                Pos += 1
                self.event_names += [self.input_channel_names[-1] + "Low"]
                Pos += 1

        self.events_positions.globalTimerStart = Pos
        for i in range(hardware.n_global_timers):
            self.event_names += ["_GlobalTimer" + str(i + 1) + "_Start"]
            Pos += 1

        self.events_positions.globalTimerEnd = Pos
        for i in range(hardware.n_global_timers):
            self.event_names += ["_GlobalTimer" + str(i + 1) + "_End"]
            self.input_channel_names += ["_GlobalTimer" + str(i + 1)]
            Pos += 1

        self.events_positions.globalCounter = Pos
        for i in range(hardware.n_global_counters):
            self.event_names += ["_GlobalCounter" + str(i + 1) + "_End"]
            Pos += 1

        self.events_positions.condition = Pos
        for i in range(hardware.n_conditions):
            self.event_names += ["_Condition" + str(i + 1)]
            Pos += 1

        self.event_names += ["_Tup"]
        self.events_positions.Tup = Pos
        Pos += 1

        logger.debug("event_names: %s", self.event_names)
        logger.debug("events_positions: %s", self.events_positions)

    def setup_output_channels(self, hw_outputs, hardware):
        """
        Generate output channel names
        """
        nUSB = 0
        nUART = 0
        nVALVE = 0
        nBNCs = 0
        nWires = 0
        nPorts = 0
        for i in range(len(hw_outputs)):
            if hw_outputs[i] == "U":
                nUART += 1
                self.output_channel_names += ["Serial" + str(nUART)]

            if hw_outputs[i] == "X":
                if nUSB == 0:
                    self.events_positions.output_USB = len(self.output_channel_names)
                nUSB += 1
                self.output_channel_names += ["SoftCode"]

            if hw_outputs[i] == "V":
                if nVALVE == 0:
                    self.events_positions.output_VALVE = len(self.output_channel_names)
                nVALVE += 1
                self.output_channel_names += [
                    "Valve" + str(nVALVE)
                ]  # Assume an SPI shift register mapping bits of a byte to 8 valves

            if hw_outputs[i] == "B":
                if nBNCs == 0:
                    self.events_positions.output_BNC = len(self.output_channel_names)
                nBNCs += 1
                self.output_channel_names += [
                    "BNC" + str(nBNCs)
                ]  # Assume an SPI shift register mapping bits of a byte to 8 valves

            if hw_outputs[i] == "W":
                if nWires == 0:
                    self.events_positions.output_Wire = len(self.output_channel_names)
                nWires += 1
                self.output_channel_names += [
                    "Wire" + str(nWires)
                ]  # Assume an SPI shift register mapping bits of a byte to 8 valves

            if hw_outputs[i] == "P":
                if nPorts == 0:
                    self.events_positions.output_PWM = len(self.output_channel_names)
                nPorts += 1
                self.output_channel_names += [
                    "PWM" + str(nPorts)
                ]  # Assume an SPI shift register mapping bits of a byte to 8 valves

        self.output_channel_names += ["_GlobalTimerTrig"]
        self.events_positions.globalTimerTrigger = len(self.output_channel_names) - 1
        self.output_channel_names += ["_GlobalTimerCancel"]
        self.events_positions.globalTimerCancel = len(self.output_channel_names) - 1
        self.output_channel_names += ["_GlobalCounterReset"]

        logger.debug("output_channel_names: %s", self.output_channel_names)

    def get_event_name(self, event_idx):
        """

        :param event_idx:
        :return:
        """

        try:
            event_name = self.event_names[event_idx]
        except IndexError:
            event_name = "unknown event name"

        return event_name

    def __str__(self):

        buff = "\n****************** EVENTS ******************\n"
        for idx, event in enumerate(self.event_names):
            buff += "{0: >3} : {1: <24}".format(idx, event)
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        buff += "\n\n****************** INPUT CHANNELS ******************\n"
        for idx, channel in enumerate(self.input_channel_names):
            buff += "{0: >3} : {1: <24}".format(idx, channel)
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        buff += "\n\n****************** OUTPUT CHANNELS ******************\n"
        for idx, channel in enumerate(self.output_channel_names):
            buff += "{0: >3} : {1: <24}".format(idx, channel)
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        return "SMA Channels\n" + buff + "\n\n"
