import logging
import math
import socket
import time
from datetime import datetime as datetime_now

from pybpodapi.bpod.hardware.channels import ChannelName, ChannelType
from pybpodapi.bpod.hardware.events import EventName
from pybpodapi.bpod.hardware.hardware import Hardware
from pybpodapi.bpod.hardware.output_channels import OutputChannel
from pybpodapi.com.messaging.event_occurrence import EventOccurrence
from pybpodapi.com.messaging.event_resume import EventResume
from pybpodapi.com.messaging.softcode_occurrence import SoftcodeOccurrence
from pybpodapi.com.messaging.state_transition import StateTransition
from pybpodapi.com.messaging.trial import Trial
from pybpodapi.com.messaging.value import ValueMessage
from pybpodapi.exceptions.bpod_error import BpodErrorException
from pybpodapi.session import Session

from village.settings import settings

from .non_blockingsocketreceive import NonBlockingSocketReceive

logger = logging.getLogger(__name__)


class BpodBase(object):
    """
    API to interact with Bpod

    :ivar Session session: Session for this bpod running experiment
    :ivar Hardware hardware: Hardware object representing Bpod hardware
    :ivar MessageAPI message_api: Abstracts communication with Bpod box
    :ivar bool new_sma_sent: whether a new state machine was already
    uploaded to Bpod box
    """

    class Events(EventName):
        pass

    class OutputChannels(OutputChannel):
        pass

    class ChannelTypes(ChannelType):
        pass

    class ChannelNames(ChannelName):
        pass

    CHECK_STATE_MACHINE_COUNTER = 0

    def __init__(
        self,
        serial_port=None,
        sync_channel=None,
        sync_mode=None,
        net_port=None,
    ):
        self._session = self.create_session()

        self.serial_port = (
            serial_port if serial_port is not None else settings.get("BPOD_SERIAL_PORT")
        )
        self.baudrate = settings.get("BPOD_BAUDRATE")
        self.sync_channel = (
            sync_channel
            if sync_channel is not None
            else settings.get("BPOD_SYNC_CHANNEL")
        )
        self.sync_mode = (
            sync_mode if sync_mode is not None else settings.get("BPOD_SYNC_MODE")
        )
        self.net_port = (
            net_port if net_port is not None else settings.get("BPOD_NET_PORT")
        )
        self._hardware = Hardware()  # type: Hardware
        self.bpod_modules = None
        self.bpod_start_timestamp = None
        self.bpod_start_timepc = None
        self.difference = 0
        self._new_sma_sent = False  # type: bool
        self._skip_all_trials = False

        self._hardware.sync_channel = (
            self.sync_channel
        )  # 255 = no sync, otherwise set to a hardware channel number
        self._hardware.sync_mode = (
            self.sync_mode
        )  # 0 = flip logic every trial, 1 = every state

    # PUBLIC METHODS

    def loop_handler(self):
        """
        handler that will execute on every loop when the bpod is running
        """
        pass

    def open(self):
        """
        Starts Bpod.

        Connect to Bpod board through serial port, test handshake,
        retrieve firmware version,
        retrieve hardware description, enable input ports and configure
        channel synchronization.

        Example:

        .. code-block:: python

            my_bpod = Bpod().open("/dev/tty.usbmodem1293",
            "/Users/John/Desktop/bpod_workspace", "2afc_protocol")

        :param str serial_port: serial port to connect
        :param str workspace_path: path for bpod output files
        (no folders will be created)
        :param str session_name: this name will be used for output files
        :param int baudrate [optional]: baudrate for serial connection
        :param int sync_channel [optional]: Serial synchronization channel:
        255 = no sync, otherwise set to a hardware channel number
        :param int sync_mode [optional]: Serial synchronization mode:
        0 = flip logic every trial, 1 = every state
        :return: Bpod object created
        :rtype: pybpodapi.model.bpod
        """

        logger.info("Starting Bpod")

        print("vamos ", self.serial_port, self.baudrate)

        self._bpodcom_connect(self.serial_port, self.baudrate)

        print("aqui no llego")

        if not self._bpodcom_handshake():
            raise BpodErrorException(
                """Error: Bpod failed to confirm connectivity. 
                Please reset Bpod and try again."""
            )

        print("aqui no llego")

        # check the firmware version
        firmware_version, machine_type = self._bpodcom_firmware_version()

        print("firmware: ", firmware_version)

        if firmware_version < int(settings.get("BPOD_TARGET_FIRMWARE")):
            raise BpodErrorException(
                """Error: Old firmware detected. 
                Please update Bpod 0.7 + firmware and try again."""
            )

        if firmware_version > int(settings.get("BPOD_TARGET_FIRMWARE")):
            raise BpodErrorException(
                """Error: Future firmware detected. 
                Please update the Bpod python software."""
            )

        self._hardware.firmware_version = firmware_version
        self._hardware.machine_type = machine_type

        self._bpodcom_hardware_description(self._hardware)

        if not self._bpodcom_enable_ports(self._hardware):
            raise BpodErrorException("Error: Failed to enable Bpod inputs.")

        if not self._bpodcom_set_sync_channel_and_mode(
            sync_channel=self.sync_channel, sync_mode=self.sync_mode
        ):
            raise BpodErrorException("Error: Failed to configure synchronization.")

        # check if any module is connected
        self.bpod_modules = self._bpodcom_get_modules_info(self._hardware)

        self._hardware.setup(self.bpod_modules)

        # initialise the server to handle commands
        if self.net_port is not None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(("0.0.0.0", self.net_port))
            self.socketin = NonBlockingSocketReceive(self.sock)
        else:
            self.sock = None
            self.socketin = None

        return self

    def close(self):
        """
        Close connection with Bpod
        """
        # if hasattr(settings, 'PYBPOD_VARSNAMES'):
        #     for varname in settings.PYBPOD_VARSNAMES:
        #         self.session += ValueMessage(varname, getattr(settings, varname))

        self._bpodcom_disconnect()

        del self._session

        if self.socketin is not None:
            self.socketin.close()
            self.sock.close()

    def stop_trial(self):
        self._bpodcom_stop_trial()

    def pause(self):
        self._bpodcom_pause_trial()

    def resume(self):
        self._bpodcom_resume_trial()

    def refresh_modules(self):
        # check if any module is connected
        self.bpod_modules = self._bpodcom_get_modules_info(self._hardware)
        self._hardware.setup(self.bpod_modules)

    def register_value(self, name, value):
        self._session += ValueMessage(name, value)

    def send_state_machine(self, sma, run_asap=None):
        """
        Builds message and sends state machine to Bpod

        :param pybpodapi.model.state_machine sma: initialized state machine
        """
        if not self.bpod_com_ready:
            raise Exception("Bpod connection is closed")

        if self._skip_all_trials is True:
            return

        logger.info("Sending state machine")

        sma.update_state_numbers()

        state_machine_body = (
            sma.build_message()
            + sma.build_message_global_timer()
            + sma.build_message_32_bits()
        )

        self._bpodcom_send_state_machine(
            sma.build_header(run_asap, len(state_machine_body)) + state_machine_body
        )

        self._new_sma_sent = True

    def run_state_machine(self, sma):
        """

        Adds a new trial to current session and runs state machine on Bpod box.

        While state machine is running, messages are processed accordingly.

        When state machine stops, timestamps are updated and trial events are processed.

        Finally, data is released for registered data consumers / exporters.

        .. seealso::

            Send command "run state machine":
            :meth:`pybpodapi.bpod.bpod_base.BpodBase.run_state_machine`.

            Process opcode:
            :meth:`pybpodapi.bpod.bpod_base.BpodBase._BpodBase__process_opcode`.

            Update timestamps:
            :meth:`pybpodapi.bpod.bpod_base.BpodBase._BpodBase__update_timestamps`.

        :param (:class:`pybpodapi.state_machine.StateMachine`) sma:
        initialized state machine
        """
        if not self.bpod_com_ready:
            raise Exception("Bpod connection is closed")

        if self._skip_all_trials is True:
            return False

        self.session += Trial(sma)

        logger.info("Running state machine, trial %s", len(self.session.trials))

        self.trial_timestamps = (
            []
        )  # Store the trial timestamps in case bpod is using live_timestamps

        self._bpodcom_run_state_machine()

        if self._new_sma_sent:
            try:
                status = self._bpodcom_state_machine_installation_status()
                if status:
                    # self._session += ValueMessage('GOOD', 'normal')
                    self._new_sma_sent = False
                else:
                    self._session += ValueMessage("BPODCRASH", "waiting 100 ms")
                    time.sleep(0.1)
                    self.send_state_machine(sma)
                    self._bpodcom_run_state_machine()
                    self._new_sma_sent = False
                    self.trial_start_timestamp = (
                        self._bpodcom_get_trial_timestamp_start()
                    )
            except:  # noqa: E722
                self._session += ValueMessage("BPODCRASH", "waiting 100 ms")
                time.sleep(0.1)
                self.send_state_machine(sma)
                self._bpodcom_run_state_machine()
                self._new_sma_sent = False
                self.trial_start_timestamp = self._bpodcom_get_trial_timestamp_start()

        trial_start_timestamp = self._bpodcom_get_trial_timestamp_start()
        self.trial_start_timepc = datetime_now.now()

        if self.bpod_start_timestamp is None:
            self.bpod_start_timestamp = trial_start_timestamp
            self.bpod_start_timepc = datetime_now.fromtimestamp(0)

        self.trial_start_timestamp = (
            self.trial_start_timepc - self.bpod_start_timepc
        ).total_seconds()
        self.difference = trial_start_timestamp - self.trial_start_timestamp

        self._session += StateTransition(sma.state_names[0], self.trial_start_timestamp)

        # create a list of executed states
        state_change_indexes = []

        # flags used to stop a trial (or all trials)
        interrupt_task = False
        kill_task = False

        sma.is_running = True
        while sma.is_running:

            # read commands from a net socket
            if self.socketin is not None:
                inline = self.socketin.readline()

                if inline is not None:
                    inline = inline.decode().strip()
                    interrupt_task, kill_task = self.handle_inline(inline, sma)

            if self.data_available():
                opcode, data = self._bpodcom_read_opcode_message()
                self.__process_opcode(sma, opcode, data, state_change_indexes)

            self.loop_handler()

            if interrupt_task or kill_task:
                self._skip_all_trials = True
                break

        if not interrupt_task:
            self.__update_timestamps(sma, state_change_indexes)
            self.session.add_trial_events()

        logger.info("Publishing Bpod trial")

        if interrupt_task and kill_task:
            self.close()
            exit(0)

        return not interrupt_task

    def handle_inline(self, inline, sma):
        interrupt_task = False
        kill_task = False
        if inline.startswith("pause-trial"):
            self.pause()
        elif inline.startswith("resume-trial"):
            self.resume()
        elif inline.startswith("stop-trial"):
            self.stop_trial()
        elif inline.startswith("close"):
            self.stop_trial()
            interrupt_task = True
        elif inline.startswith("kill"):
            self.stop_trial()
            interrupt_task = kill_task = True
        elif inline.startswith("SoftCode"):
            softcode = int(inline[-1]) - 1
            self.trigger_softcode(softcode)
        elif inline.startswith("trigger_input:"):
            tdata = inline.split(":")
            chn_name = tdata[1]
            evt_data = tdata[2]

            channel_number = sma.hardware.channels.input_channel_names.index(chn_name)
            self.trigger_input(channel_number, evt_data)
        elif inline.startswith("trigger_output:"):
            tdata = inline.split(":")
            chn_name = tdata[1]
            evt_data = tdata[2]

            channel_number = sma.hardware.channels.output_channel_names.index(chn_name)
            self.trigger_output(channel_number, evt_data)
        elif inline.startswith("message:"):
            tdata = inline.split(":")
            module_index = int(tdata[1])
            msg = tdata[2]
            final_msg = []
            msg_elems = msg.split()
            if msg_elems[0].startswith("'"):
                final_msg.append(ord(msg_elems[0][1]))
            for x in msg_elems[1:]:
                final_msg.append(int(x))
            self.load_message(module_index, final_msg)

        return interrupt_task, kill_task

    def load_serial_message(self, serial_channel, message_ID, serial_message):
        """
        Load serial message on Bpod

        :param int serial_channel: Serial port to send, 1, 2 or 3
        :param int message_ID: Unique id for the message. Should be between 1 and 255
        :param list(int) serial_message: Message to send.
        The message should be bigger than 3 bytes.
        """
        response = self._bpodcom_load_serial_message(
            serial_channel, message_ID, serial_message, 1
        )

        if not response:
            raise BpodErrorException("Error: Failed to set serial message.")

    def reset_serial_messages(self):
        """
        Reset serial messages to equivalent byte codes (i.e. message# 4 = one byte, 0x4)
        """
        response = self._bpodcom_reset_serial_messages()

        if not response:
            raise BpodErrorException("Error: Failed to reset serial message library.")

    def softcode_handler_function(self, data):
        """
        Users can override this function directly on the protocol
        to handle a softcode from Bpod

        :param int data: soft code number
        """
        pass

    def echo_softcode(self, softcode):
        return self._bpodcom_echo_softcode(softcode)

    def trigger_event(self, event_index, event_data):
        return self._bpodcom_manual_override_exec_event(event_index, event_data)

    def trigger_input(self, channel_number, value):
        return self._bpodcom_override_input_state(channel_number, value)

    def trigger_output(self, channel_number, value):
        return self._bpodcom_override_digital_hardware_state(channel_number, value)

    def trigger_softcode(self, softcode):
        return self._bpodcom_send_softcode(softcode)

    def load_message(self, module_index, msg):
        # get module reference
        module = [x for x in self.modules if x.serial_port == module_index]
        # call module_write. on module reference
        if module:
            self._bpodcom_module_write(module_index - 1, msg)

    # PRIVATE METHODS
    def create_session(self):
        return Session()

    def __process_opcode(self, sma, opcode, data, state_change_indexes):
        """
        Process data from bpod board given an opcode

        In original bpod, sma.raw_data == raw_events

        :param sma: state machine object
        :param int opcode: opcode number
        :param data: data from bpod board
        :param state_change_indexes:
        :return:
        """

        current_trial = self.session.current_trial

        if opcode == 1:  # Read events
            n_current_events = data
            current_events = self._bpodcom_read_current_events(n_current_events)
            transition_event_found = False

            if self.hardware.live_timestamps:
                event_timestamp = self._bpodcom_read_event_timestamp()
            else:
                event_timestamp = None

            for event_id in current_events:
                if event_id == 255:
                    sma.is_running = False
                else:
                    self._session += EventOccurrence(
                        event_id,
                        sma.hardware.channels.get_event_name(event_id),
                        event_timestamp + self.trial_start_timestamp,
                    )
                    self.trial_timestamps.append(event_timestamp)

                    # input matrix
                    if not transition_event_found:
                        logger.debug("transition event not found")
                        logger.debug("Current state: %s", sma.current_state)
                        for transition in sma.input_matrix[sma.current_state]:
                            logger.debug("Transition: %s", transition)
                            if transition[0] == event_id:
                                if sma.use_255_back_signal and transition[1] == 255:
                                    sma.current_state = current_trial.states[-2]
                                else:
                                    sma.current_state = transition[1]

                                if not math.isnan(sma.current_state):
                                    logger.debug("adding states input matrix")
                                    current_trial.states.append(sma.current_state)
                                    state_change_indexes.append(
                                        len(current_trial.events_occurrences) - 1
                                    )

                                transition_event_found = True

                    # state timer matrix
                    if not transition_event_found:
                        this_state_timer_transition = sma.state_timer_matrix[
                            sma.current_state
                        ]
                        if event_id == sma.hardware.channels.events_positions.Tup:
                            if not (this_state_timer_transition == sma.current_state):
                                if (
                                    sma.use_255_back_signal
                                    and this_state_timer_transition == 255
                                ):
                                    sma.current_state = current_trial.states[-2]
                                else:
                                    sma.current_state = this_state_timer_transition

                                if not math.isnan(sma.current_state):
                                    logger.debug("adding states state timer matrix")
                                    current_trial.states.append(sma.current_state)
                                    state_change_indexes.append(
                                        len(current_trial.events_occurrences) - 1
                                    )
                                transition_event_found = True

                    # global timers start matrix
                    if not transition_event_found:
                        for transition in sma.global_timers.start_matrix[
                            sma.current_state
                        ]:
                            if transition[0] == event_id:
                                if sma.use_255_back_signal and transition[1] == 255:
                                    sma.current_state = current_trial.states[-2]
                                else:
                                    sma.current_state = transition[1]

                                if not math.isnan(sma.current_state):
                                    logger.debug(
                                        "adding states global timers start matrix"
                                    )
                                    current_trial.states.append(sma.current_state)
                                    state_change_indexes.append(
                                        len(current_trial.events_occurrences) - 1
                                    )
                                transition_event_found = True

                    # global timers end matrix
                    if not transition_event_found:
                        for transition in sma.global_timers.end_matrix[
                            sma.current_state
                        ]:
                            if transition[0] == event_id:

                                if sma.use_255_back_signal and transition[1] == 255:
                                    sma.current_state = current_trial.states[-2]
                                else:
                                    sma.current_state = transition[1]

                                if not math.isnan(sma.current_state):
                                    logger.debug(
                                        "adding states global timers end matrix"
                                    )
                                    current_trial.states.append(sma.current_state)
                                    state_change_indexes.append(
                                        len(current_trial.events_occurrences) - 1
                                    )
                                transition_event_found = True

                logger.debug("States indexes: %s", current_trial.states)

            if transition_event_found and not math.isnan(sma.current_state):
                state_name = sma.state_names[sma.current_state]
                try:
                    time = event_timestamp + self.trial_start_timestamp
                except:  # noqa: E722
                    time = 10000
                self._session += StateTransition(state_name, time)

        elif opcode == 2:  # Handle soft code
            my_time = (datetime_now.now() - self.bpod_start_timepc).total_seconds()
            self._session += SoftcodeOccurrence(data, my_time)
            self.softcode_handler_function(data)

    def __update_timestamps(self, sma, state_change_indexes):
        """
        Read timestamps from Bpod and update state machine info

        :param StateMachine sma:
        :param list state_change_indexes:
        """

        current_trial = self.session.current_trial
        current_trial.trial_start_timestamp = (
            self.trial_start_timestamp
        )  # start timestamp of first trial
        current_trial.bpod_start_timestamp = self.bpod_start_timestamp
        current_trial.difference = self.difference

        trial_end_timestamp, discrepancy = self._bpodcom_read_timestamps()
        current_trial.trial_end_timestamp = trial_end_timestamp

        if self.hardware.live_timestamps:
            timestamps = self.trial_timestamps
        else:
            timestamps = self._bpodcom_read_alltimestamps()
            timestamps = [
                float(t) * self._hardware.times_scale_factor for t in timestamps
            ]

            # update the timestamps of the events
            for event, timestamp in zip(current_trial.events_occurrences, timestamps):
                event.host_timestamp = timestamp
                e = EventResume(
                    event.event_id, event.event_name, host_timestamp=timestamp
                )
                self.session += e

        current_trial.event_timestamps = timestamps
        current_trial.state_timestamps += [timestamps[i] for i in state_change_indexes]
        current_trial.state_timestamps += timestamps[-1:]

    def find_module_by_name(self, name):
        """
        Search for a module by name
        """
        for m in self.modules:
            if m.name == name:
                return m
        return None

    # PROPERTIES
    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def hardware(self):
        return self._hardware

    @property
    def modules(self):
        return [m for m in self.bpod_modules if m.connected]

    @property
    def skip_all_trials(self) -> bool:
        return self._skip_all_trials
