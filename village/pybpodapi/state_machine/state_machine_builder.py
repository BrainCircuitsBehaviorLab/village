import logging
import math

from pybpodapi.com.arcom import ArduinoTypes
from pybpodapi.com.protocol.send_msg_headers import SendMessageHeader
from pybpodapi.state_machine.state_machine_base import StateMachineBase

logger = logging.getLogger(__name__)


class StateMachineBuilder(StateMachineBase):
    """
    Extend state machine with builder logic

    .. warning:: A lot of data structures are kept here for compatibility
    with original matlab library which are not so python-like.
    Anyone is welcome to enhance this class but keep in mind that it
    will affect the whole pybpodapi library.
    """

    def update_state_numbers(self):
        """
        Replace undeclared states (at the time they were referenced)
        with actual state numbers
        """
        for i in range(len(self.undeclared)):
            undeclaredStateNumber = i + 10000
            thisStateNumber = self.manifest.index(self.undeclared[i])
            for j in range(self.total_states_added):
                if self.state_timer_matrix[j] == undeclaredStateNumber:
                    self.state_timer_matrix[j] = thisStateNumber

                # input matrix
                inputTransitions = self.input_matrix[j]
                for k in range(0, len(inputTransitions)):
                    thisTransition = inputTransitions[k]
                    if thisTransition[1] == undeclaredStateNumber:
                        inputTransitions[k] = (
                            thisTransition[0],
                            thisStateNumber,
                        )
                self.input_matrix[j] = inputTransitions

                # start matrix
                inputTransitions = self.global_timers.start_matrix[j]
                for k in range(0, len(inputTransitions)):
                    thisTransition = inputTransitions[k]
                    if thisTransition[1] == undeclaredStateNumber:
                        inputTransitions[k] = (
                            thisTransition[0],
                            thisStateNumber,
                        )
                self.global_timers.start_matrix[j] = inputTransitions

                # end matrix
                inputTransitions = self.global_timers.end_matrix[j]
                for k in range(0, len(inputTransitions)):
                    thisTransition = inputTransitions[k]
                    if thisTransition[1] == undeclaredStateNumber:
                        inputTransitions[k] = (
                            thisTransition[0],
                            thisStateNumber,
                        )
                self.global_timers.end_matrix[j] = inputTransitions

                # global counters
                inputTransitions = self.global_counters.matrix[j]
                for k in range(0, len(inputTransitions)):
                    thisTransition = inputTransitions[k]
                    if thisTransition[1] == undeclaredStateNumber:
                        inputTransitions[k] = (
                            thisTransition[0],
                            thisStateNumber,
                        )
                self.global_counters.matrix[j] = inputTransitions

                # conditions
                inputTransitions = self.conditions.matrix[j]
                for k in range(0, len(inputTransitions)):
                    thisTransition = inputTransitions[k]
                    if thisTransition[1] == undeclaredStateNumber:
                        inputTransitions[k] = (
                            thisTransition[0],
                            thisStateNumber,
                        )
                self.conditions.matrix[j] = inputTransitions

        # Check to make sure all states in manifest exist
        logger.debug(
            "Total states added: %s | Manifested states: %s",
            self.total_states_added,
            len(self.manifest),
        )
        if len(self.manifest) > self.total_states_added:
            raise StateMachineBuilderError(
                "Error: some states were referenced by name, but not declared."
            )

    def build_header(self, run_asap=None, statemachine_body_size=0):
        message = [ord(SendMessageHeader.NEW_STATE_MATRIX)]
        message += [0 if run_asap is None else 1]
        message += [1 if self.use_255_back_signal else 0]

        return ArduinoTypes.get_uint8_array(message) + ArduinoTypes.get_uint16_array(
            [statemachine_body_size]
        )

    def build_message(self):
        """
        Builds state machine to send to Bpod box

        :rtype: list(int)
        """
        self.highest_used_global_counter = self.global_counters.get_max_index_used()
        self.highest_used_global_timer = self.global_timers.get_max_index_used()
        self.highest_used_global_condition = self.conditions.get_max_index_used()

        self.highest_used_global_counter = (
            0
            if self.highest_used_global_counter is None
            else self.highest_used_global_counter + 1
        )
        self.highest_used_global_timer = (
            0
            if self.highest_used_global_timer is None
            else self.highest_used_global_timer + 1
        )
        self.highest_used_global_condition = (
            0
            if self.highest_used_global_condition is None
            else self.highest_used_global_condition + 1
        )

        message = [
            self.total_states_added,
            self.highest_used_global_timer,
            self.highest_used_global_counter,
            self.highest_used_global_condition,
        ]

        # STATE TIMER MATRIX
        # Send state timer transitions (for all states)
        tmp = []
        for i in range(self.total_states_added):
            tmp += [
                (
                    self.total_states_added
                    if math.isnan(self.state_timer_matrix[i])
                    else self.state_timer_matrix[i]
                )
            ]

        message += tmp
        logger.debug("STATE TIMER MATRIX: %s", tmp)

        # INPUT MATRIX
        # Send event-triggered transitions (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):

            state_transitions = self.input_matrix[i]
            n_transitions = len(state_transitions)
            tmp += [n_transitions]
            for transition in state_transitions:
                tmp += [transition[0]]
                dest_state = transition[1]
                tmp += [
                    (self.total_states_added if math.isnan(dest_state) else dest_state)
                ]
        message += tmp
        logger.debug("INPUT MATRIX: %s", tmp)

        # OUTPUT MATRIX
        # Send hardware states (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):
            hw_state = self.output_matrix[i]
            hw_state = [
                evt
                for evt in hw_state
                if evt[0] < self.hardware.channels.events_positions.globalTimerTrigger
            ]
            n_differences = len(hw_state)
            tmp += [n_differences]
            for hw_conf in hw_state:
                tmp += hw_conf[:2]
        message += tmp
        logger.debug("OUTPUT MATRIX: %s", tmp)

        # GLOBAL_TIMER_START_MATRIX
        # Send global timer-start triggered transitions
        # (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):
            state_transitions = self.global_timers.start_matrix[i]
            n_transitions = len(state_transitions)
            tmp += [n_transitions]
            for transition in state_transitions:
                dest_state = transition[1]
                tmp += [
                    transition[0]
                    - self.hardware.channels.events_positions.globalTimerStart
                ]
                tmp += [
                    (self.total_states_added if math.isnan(dest_state) else dest_state)
                ]
        message += tmp
        logger.debug("GLOBAL_TIMER_START_MATRIX: %s", tmp)

        # GLOBAL_TIMER_END_MATRIX
        # Send global timer-end triggered transitions
        # (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):
            state_transitions = self.global_timers.end_matrix[i]
            n_transitions = len(state_transitions)
            tmp += [n_transitions]
            for transition in state_transitions:
                dest_state = transition[1]
                tmp += [
                    transition[0]
                    - self.hardware.channels.events_positions.globalTimerEnd
                ]
                tmp += [
                    (self.total_states_added if math.isnan(dest_state) else dest_state)
                ]
        message += tmp
        logger.debug("GLOBAL_TIMER_END_MATRIX: %s", tmp)

        # GLOBAL_COUNTER_MATRIX
        # Send global counter triggered transitions
        # (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):
            state_transitions = self.global_counters.matrix[i]
            n_transitions = len(state_transitions)
            tmp += [n_transitions]
            for transition in state_transitions:
                dest_state = transition[1]
                tmp += [
                    transition[0]
                    - self.hardware.channels.events_positions.globalCounter
                ]
                tmp += [
                    (self.total_states_added if math.isnan(dest_state) else dest_state)
                ]
        message += tmp
        logger.debug("GLOBAL_COUNTER_MATRIX: %s", tmp)

        # CONDITION_MATRIX
        # Send condition triggered transitions
        # (where they are different from default)
        tmp = []
        for i in range(self.total_states_added):
            state_transitions = self.conditions.matrix[i]
            n_transitions = len(state_transitions)
            tmp += [n_transitions]
            for transition in state_transitions:
                dest_state = transition[1]
                tmp += [
                    transition[0] - self.hardware.channels.events_positions.condition
                ]
                tmp += [
                    (self.total_states_added if math.isnan(dest_state) else dest_state)
                ]

        message += tmp
        logger.debug("CONDITION_MATRIX: %s", tmp)

        # GLOBAL_TIMER_CHANNELS
        tmp = []
        for i in range(self.highest_used_global_timer):
            tmp += [self.global_timers.channels[i]]
        message += tmp
        logger.debug("GLOBAL_TIMER_CHANNELS: %s", tmp)

        # GLOBAL_TIMER_ON_MESSAGES
        tmp = []
        for i in range(self.highest_used_global_timer):
            v = self.global_timers.on_messages[i]
            tmp += [255 if v == 0 else v]
        message += tmp
        logger.debug("GLOBAL_TIMER_ON_MESSAGES: %s", tmp)

        # GLOBAL_TIMER_OFF_MESSAGES
        tmp = []
        for i in range(self.highest_used_global_timer):
            v = self.global_timers.off_messages[i]
            tmp += [255 if v == 0 else v]
        message += tmp
        logger.debug("GLOBAL_TIMER_OFF_MESSAGES: %s", tmp)

        # GLOBAL_TIMER_LOOP_MODE
        tmp = []
        for i in range(self.highest_used_global_timer):
            tmp += [self.global_timers.loop_mode[i]]
        message += tmp
        logger.debug("GLOBAL_TIMER_LOOP_MODE: %s", tmp)

        # GLOBAL_TIMER_EVENTS
        tmp = []
        for i in range(self.highest_used_global_timer):
            tmp += [self.global_timers.send_events[i]]
        message += tmp
        logger.debug("GLOBAL_TIMER_EVENTS: %s", tmp)

        # GLOBAL_COUNTER_ATTACHED_EVENTS
        tmp = []
        for i in range(self.highest_used_global_counter):
            tmp += [self.global_counters.attached_events[i]]
        message += tmp
        logger.debug("GLOBAL_COUNTER_ATTACHED_EVENTS: %s", tmp)

        # CONDITIONS_CHANNELS
        tmp = []
        for i in range(self.highest_used_global_condition):
            tmp += [self.conditions.channels[i]]
        message += tmp
        logger.debug("CONDITIONS_CHANNELS: %s", tmp)

        # CONDITIONS VALUES
        tmp = []
        for i in range(self.highest_used_global_condition):
            tmp += [self.conditions.values[i]]
        message += tmp
        logger.debug("CONDITIONS VALUES: %s", tmp)

        # GLOBAL_COUNTER_RESETS
        tmp = []
        for i in range(self.total_states_added):
            tmp += [self.global_counters.reset_matrix[i]]
        message += tmp
        logger.debug("GLOBAL_COUNTER_RESETS: %s", tmp)

        self.state_timers = self.state_timers[: self.total_states_added]

        return ArduinoTypes.get_uint8_array(message)

    def build_message_global_timer(self):

        message = []

        for i in range(self.total_states_added):
            message += (self.global_timers.triggers_matrix[i],)

        for i in range(self.total_states_added):
            message += (self.global_timers.cancels_matrix[i],)

        for i in range(self.highest_used_global_timer):
            message += (self.global_timers.onset_matrix[i],)

        if self.hardware.n_global_timers > 16:
            return ArduinoTypes.get_uint32_array(message)
        elif self.hardware.n_global_timers > 8:
            return ArduinoTypes.get_uint16_array(message)
        else:
            return ArduinoTypes.get_uint8_array(message)

    def build_message_32_bits(self):
        """
        Builds a 32 bit message to send to Bpod box

        :rtype: list(float)
        """
        # TODO find how many global timers are used

        used_timers = range(self.highest_used_global_timer)
        used_counters = range(self.highest_used_global_counter)

        thirty_two_bit_message = (
            [t * self.hardware.cycle_frequency for t in self.state_timers]
            + [
                self.global_timers.timers[i] * self.hardware.cycle_frequency
                for i in used_timers
            ]
            + [
                self.global_timers.on_set_delays[i] * self.hardware.cycle_frequency
                for i in used_timers
            ]
            + [
                self.global_timers.loop_intervals[i] * self.hardware.cycle_frequency
                for i in used_timers
            ]
            + [self.global_counters.thresholds[i] for i in used_counters]
        )

        return ArduinoTypes.get_uint32_array(thirty_two_bit_message)


class StateMachineBuilderError(Exception):
    pass
