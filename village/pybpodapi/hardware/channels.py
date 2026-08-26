import logging

logger = logging.getLogger(__name__)


class ChannelType:
    """
    Define if channel type is input or output.
    These values must be set according to Bpod firmware specification.
    """

    #: Input channel
    INPUT = 1

    #: Output channel
    OUTPUT = 2


class ChannelName:
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


class EventsPositions:
    """ """

    def __init__(self) -> None:
        self.Event_USB = 0
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


class Channels:
    """
    Bpod main class
    """

    def __init__(self):
        self.event_names = []
        self.input_channel_names = []
        self.output_channel_names = []
        self.events_positions = EventsPositions()

    def _pad_event_names_to(self, target):
        """Pads self.event_names with placeholders up to length `target`.

        get_event_name() looks up an incoming event_idx by direct list
        position, so bumping the `Pos` counter alone does nothing -- the
        list itself must actually contain an entry at every index up to
        `target`, or the next real event name appended still lands right
        after whatever was last appended, not at `target`.
        """
        while len(self.event_names) < target:
            self.event_names += ["Reserved" + str(len(self.event_names))]

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
        digital_events_started = False

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
            elif hardware.inputs[i] == "Z" and hardware.firmware_version >= 23:
                # Second USB/App-type serial channel introduced in firmware v23+
                # (grouped with 'U' and 'X' as "serial channels" in the firmware's
                # own hardware description; its event handling in the firmware is
                # a copy of 'X's, using a second SoftEvent counter). On currently
                # observed hardware it claims no event codes of its own, but it
                # does occupy one slot in the physical channel list -- skipping it
                # here silently used to shift every input_channel_names index
                # after it (BNC, Port...) off by one, which broke the manual
                # override / GUI poke simulation for those channels. The version
                # check is belt-and-suspenders: 'Z' cannot appear on v22 hardware
                # anyway, so this branch is unreachable there regardless.
                nUSB += 1
                self.input_channel_names += ["USB" + str(nUSB)]
            elif hardware.inputs[i] == "P":
                if not digital_events_started:
                    if hardware.firmware_version >= 23:
                        self._pad_event_names_to(hardware.max_serial_events)
                        Pos = max(Pos, hardware.max_serial_events)
                    digital_events_started = True
                if nPorts == 0:
                    self.events_positions.Event_Port = Pos
                nPorts += 1
                self.input_channel_names += ["Port" + str(nPorts)]
                self.event_names += [self.input_channel_names[-1] + "In"]
                Pos += 1
                self.event_names += [self.input_channel_names[-1] + "Out"]
                Pos += 1
            elif hardware.inputs[i] == "B":
                # The firmware reserves a flat hardware.max_serial_events-sized
                # budget for all serial-type channels (U/X/Z) combined, and
                # digital event codes (BNC/Port/Wire) always start right after
                # that fixed budget -- regardless of how many of those slots
                # are actually used. Pos, accumulated only from real usage
                # above, can be short of that budget (e.g. when max_serial_events
                # isn't evenly divisible by len(modules)+1, some slots go
                # unused/reserved), so it must jump forward here to match --
                # whichever of P/B/W happens to come first in hardware.inputs.
                # Gated to firmware v23+: on v22 the division is exact (no gap),
                # so this must never touch v22's already-correct, well-tested
                # numbering, even if some future config made the gap reappear.
                if not digital_events_started:
                    if hardware.firmware_version >= 23:
                        self._pad_event_names_to(hardware.max_serial_events)
                        Pos = max(Pos, hardware.max_serial_events)
                    digital_events_started = True
                if nBNCs == 0:
                    self.events_positions.Event_BNC = Pos
                nBNCs += 1
                self.input_channel_names += ["BNC" + str(nBNCs)]
                self.event_names += [self.input_channel_names[-1] + "High"]
                Pos += 1
                self.event_names += [self.input_channel_names[-1] + "Low"]
                Pos += 1
            elif hardware.inputs[i] == "W":
                if not digital_events_started:
                    if hardware.firmware_version >= 23:
                        self._pad_event_names_to(hardware.max_serial_events)
                        Pos = max(Pos, hardware.max_serial_events)
                    digital_events_started = True
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
            self.event_names += ["GlobalTimer" + str(i + 1) + "Start"]
            Pos += 1

        self.events_positions.globalTimerEnd = Pos
        for i in range(hardware.n_global_timers):
            self.event_names += ["GlobalTimer" + str(i + 1) + "End"]
            self.input_channel_names += ["GlobalTimer" + str(i + 1)]
            Pos += 1

        self.events_positions.globalCounter = Pos
        for i in range(hardware.n_global_counters):
            self.event_names += ["GlobalCounter" + str(i + 1) + "End"]
            Pos += 1

        self.events_positions.condition = Pos
        for i in range(hardware.n_conditions):
            self.event_names += ["Condition" + str(i + 1)]
            Pos += 1

        self.event_names += ["Tup"]
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

            if hw_outputs[i] == "Z" and hardware.firmware_version >= 23:
                # See the matching "Z" case in setup_input_channels: occupies one
                # slot in the physical channel list and must be counted here too,
                # or every output_channel_names index after it (BNC, PWM, Valve...)
                # is off by one. Version-gated for the same reason: 'Z' cannot
                # appear on v22 hardware, so this is unreachable there regardless.
                self.output_channel_names += ["SoftCodeB"]

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

        self.output_channel_names += ["GlobalTimerTrig"]
        self.events_positions.globalTimerTrigger = len(self.output_channel_names) - 1
        self.output_channel_names += ["GlobalTimerCancel"]
        self.events_positions.globalTimerCancel = len(self.output_channel_names) - 1
        self.output_channel_names += ["GlobalCounterReset"]

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
            buff += f"{idx: >3} : {event: <24}"
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        buff += "\n\n****************** INPUT CHANNELS ******************\n"
        for idx, channel in enumerate(self.input_channel_names):
            buff += f"{idx: >3} : {channel: <24}"
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        buff += "\n\n****************** OUTPUT CHANNELS ******************\n"
        for idx, channel in enumerate(self.output_channel_names):
            buff += f"{idx: >3} : {channel: <24}"
            if ((idx + 1) % 3) == 0 and idx != 0:
                buff += "\n"

        return "SMA Channels\n" + buff + "\n\n"
