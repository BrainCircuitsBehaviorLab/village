# mypy: ignore-errors
import logging

from village.pybpodapi.hardware.channels import Channels

logger = logging.getLogger(__name__)


class Hardware:
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

    def setup(self, modules):
        """
        Set up hardware based on hardware description obtained from Bpod device

        :param HardwareInfoContainer hw_info_container: hardware parameters
        received from Bpod
        """

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
            f"Max states: {self.max_states}\n"
            f"Cycle period: {self.cycle_period}\n"
            f"Cycle frequency: {self.cycle_frequency}\n"
            f"Number of events per serial channel: {self.max_serial_events}\n"
            f"Number of global timers: {self.n_global_timers}\n"
            f"Number of global counters: {self.n_global_counters}\n"
            f"Number of conditions: {self.n_conditions}\n"
            f"Inputs ({len(self.inputs)}): {self.inputs}\n"
            f"Outputs ({len(self.outputs)}): {self.outputs}\n"
            f"Enabled inputs "
            f"({len([idx for idx in self.inputs_enabled if idx == 1])}): "
            f"{self.inputs_enabled}\n"
        )

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
            f"BNC{i}" for i, input_type in enumerate(self.inputs) if input_type == "B"
        ]

    @property
    def wired_inputports_names(self):
        return [
            f"Wire{i}" for i, input_type in enumerate(self.inputs) if input_type == "W"
        ]

    @property
    def behavior_inputports_names(self):
        return [
            f"Port{i}" for i, input_type in enumerate(self.inputs) if input_type == "P"
        ]
