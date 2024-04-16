import logging

from pybpodapi.bpod.hardware.channels import Channels

logger = logging.getLogger(__name__)


class Hardware(object):
    """
    Represents an hardware description based on information received
    from the current connected Bpod deviced.
    """

    DEFAULT_FREQUENCY_DIVIDER = 1000000

    def __init__(self):

        self.inputs = None
        self.outputs = None
        self.channels = None

        self.max_states = None
        self.max_serial_events = None

        self.inputs_enabled = None
        self.cycle_period = None

        self.n_global_timers = None
        self.n_global_counters = None
        self.n_conditions = None
        self.n_uart_channels = None

        self.firmware_version = None
        self.machine_type = None

        self.live_timestamps = (
            True  # The state machine will end timestamps during the execution
        )

        self.pos_global_timer_trig = 0

    ##################################################
    #################### METHODS #####################
    ##################################################

    def setup(self, modules):
        """
        Set up hardware based on hardware description obtained from Bpod device

        :param HardwareInfoContainer hw_info_container: hardware parameters
        received from Bpod
        """

        self.outputs = self.outputs  # + ['G', 'G', 'G']

        self.n_uart_channels = len([idx for idx in self.inputs if idx == "U"])

        # set up channels
        self.channels = Channels()  # type: Channels
        self.channels.setup_input_channels(self, modules)
        self.channels.setup_output_channels(self.outputs, self)

        logger.debug(self.channels)

        logger.debug(str(self))

    def __str__(self):
        return (
            "Hardware Configuration\n"
            "Max states: {max_states}\n"
            "Cycle period: {cycle_period}\n"
            "Cycle frequency: {cycle_frequency}\n"
            "Number of events per serial channel: {max_serial_events}\n"
            "Number of global timers: {n_global_timers}\n"
            "Number of global counters: {n_global_counters}\n"
            "Number of conditions: {n_conditions}\n"
            "Inputs ({n_inputs}): {inputs}\n"
            "Outputs ({n_outputs}): {outputs}\n"
            "Enabled inputs ({n_inputs_enabled}): {inputs_enabled}\n"
            "".format(
                max_states=self.max_states,
                cycle_period=self.cycle_period,
                cycle_frequency=self.cycle_frequency,
                max_serial_events=self.max_serial_events,
                n_global_timers=self.n_global_timers,
                n_global_counters=self.n_global_counters,
                n_conditions=self.n_conditions,
                inputs=self.inputs,
                n_inputs=len(self.inputs),
                outputs=self.outputs,
                n_outputs=len(self.outputs),
                inputs_enabled=self.inputs_enabled,
                n_inputs_enabled=len([idx for idx in self.inputs_enabled if idx == 1]),
            )
        )

    ##################################################
    #################### PROPERTIES ##################
    ##################################################

    @property
    def cycle_frequency(self):
        return int(self.DEFAULT_FREQUENCY_DIVIDER / self.cycle_period)

    @property
    def times_scale_factor(self):
        return float(self.cycle_period) / float(self.DEFAULT_FREQUENCY_DIVIDER)

    @property
    def bnc_inputports_indexes(self):
        return [i for i, input_type in enumerate(self.inputs) if input_type == "B"]

    @property
    def wired_inputports_indexes(self):
        return [i for i, input_type in enumerate(self.inputs) if input_type == "W"]

    @property
    def behavior_inputports_indexes(self):
        return [i for i, input_type in enumerate(self.inputs) if input_type == "P"]

    @property
    def bnc_inputports_names(self):
        return [
            "BNC{0}".format(i)
            for i, input_type in enumerate(self.inputs)
            if input_type == "B"
        ]

    @property
    def wired_inputports_names(self):
        return [
            "Wire{0}".format(i)
            for i, input_type in enumerate(self.inputs)
            if input_type == "W"
        ]

    @property
    def behavior_inputports_names(self):
        return [
            "Port{0}".format(i)
            for i, input_type in enumerate(self.inputs)
            if input_type == "P"
        ]
