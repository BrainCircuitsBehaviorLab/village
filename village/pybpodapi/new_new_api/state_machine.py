import math
import struct


class StateMachine:
    def __init__(self, bpod):
        self.bpod = bpod
        self.hardware = bpod.hardware_info
        self.manifest = []  # List of state names
        self.states = []  # List of state dictionaries

        # Matrices to be sent to Bpod
        self.state_timer_matrix = []
        self.input_matrix = []
        self.output_matrix = []

        # Initialize matrices with default values
        max_states = self.hardware.get("max_states", 256)
        for _ in range(max_states):
            self.state_timer_matrix.append(float("nan"))
            self.input_matrix.append([])
            self.output_matrix.append([])

    def add_state(self, name, timer, state_change_conditions, output_actions):
        """
        Add a state to the state machine.

        :param name: State name (str)
        :param timer: State timer duration in seconds (float)
        :param state_change_conditions: Dict of {Event: DestinationState}
        :param output_actions: List of tuples [(Output, Value), ...]
        """
        if name in self.manifest:
            raise Exception(f"State '{name}' already exists.")

        self.manifest.append(name)
        state_index = len(self.manifest) - 1

        # Store timer duration (will be sent in 32-bit message)
        if not hasattr(self, "state_timers"):
            self.state_timers = [0.0] * self.hardware.get("max_states", 256)
        self.state_timers[state_index] = timer

        # Process State Change Conditions
        for event_name, destination_state in state_change_conditions.items():
            event_code = self._get_event_code(event_name)

            if event_name == "Tup":
                self.state_timer_matrix[state_index] = destination_state
            else:
                self.input_matrix[state_index].append((event_code, destination_state))

        # Process Output Actions
        for action_name, action_value in output_actions:
            output_code = self._get_output_code(action_name)
            self.output_matrix[state_index].append((output_code, action_value))

    def _get_event_code(self, event_name):
        if event_name == "Tup":
            return -1

        # Get event list from Bpod
        event_list = self.bpod.get_event_names()

        try:
            return event_list.index(event_name)
        except ValueError:
            raise Exception(f"Unknown event: {event_name}")

    def _get_output_code(self, output_name):
        outputs = self.hardware.get("outputs", [])
        output_list = []

        n_uart = 0
        n_usb = 0
        n_valve = 0
        n_bnc = 0
        n_wire = 0
        n_pwm = 0

        for output_type in outputs:
            if output_type == "U":
                n_uart += 1
                output_list.append(f"Serial{n_uart}")
            elif output_type == "X":
                n_usb += 1
                output_list.append("SoftCode")
            elif output_type == "V":
                n_valve += 1
                output_list.append(f"Valve{n_valve}")
            elif output_type == "B":
                n_bnc += 1
                output_list.append(f"BNC{n_bnc}")
            elif output_type == "W":
                n_wire += 1
                output_list.append(f"Wire{n_wire}")
            elif output_type == "P":
                n_pwm += 1
                output_list.append(f"PWM{n_pwm}")

        output_list.append("GlobalTimerTrig")
        output_list.append("GlobalTimerCancel")
        output_list.append("GlobalCounterReset")

        try:
            return output_list.index(output_name)
        except ValueError:
            raise Exception(f"Unknown output: {output_name}")

    def build(self):
        self._resolve_state_indices()

        n_states = len(self.manifest)
        n_global_timers = self.hardware.get("n_global_timers", 0)
        n_global_counters = self.hardware.get("n_global_counters", 0)
        n_conditions = self.hardware.get("n_conditions", 0)

        body = []
        body.append(n_states)
        body.append(n_global_timers)
        body.append(n_global_counters)
        body.append(n_conditions)

        # State Timer Matrix
        for i in range(n_states):
            dest = self.state_timer_matrix[i]
            if math.isnan(dest):
                body.append(n_states)
            else:
                body.append(int(dest))

        # Input Matrix
        for i in range(n_states):
            transitions = self.input_matrix[i]
            body.append(len(transitions))
            for event_code, dest in transitions:
                body.append(event_code)
                if math.isnan(dest):
                    body.append(n_states)
                else:
                    body.append(int(dest))

        # Output Matrix
        for i in range(n_states):
            outputs = self.output_matrix[i]
            body.append(len(outputs))
            for output_code, value in outputs:
                body.append(output_code)
                body.append(value)

        # Fill remaining matrices with defaults
        for _ in range(n_states):
            body.append(0)  # GlobalTimerStart
        for _ in range(n_states):
            body.append(0)  # GlobalTimerEnd
        for _ in range(n_states):
            body.append(0)  # GlobalCounter
        for _ in range(n_states):
            body.append(0)  # Condition

        for _ in range(n_global_timers):
            body.append(255)  # Channel
        for _ in range(n_global_timers):
            body.append(255)  # On Message
        for _ in range(n_global_timers):
            body.append(255)  # Off Message
        for _ in range(n_global_timers):
            body.append(0)  # Loop Mode
        for _ in range(n_global_timers):
            body.append(0)  # Send Events
        for _ in range(n_global_counters):
            body.append(255)  # Attached Events
        for _ in range(n_conditions):
            body.append(255)  # Channels
        for _ in range(n_conditions):
            body.append(0)  # Values
        for _ in range(n_states):
            body.append(0)  # Global Counter Resets

        return bytes(body)

    def build_32bit_message(self):
        # Timers are sent in a separate 32-bit message
        # Format: StateTimers + GlobalTimers + OnSetDelays +
        # LoopIntervals + GlobalCounterThresholds
        # All times converted to timer cycles (seconds * cycle_frequency)

        cycle_freq = 1000000 / self.hardware.get("cycle_period", 100)  # Default 10kHz

        msg = []

        # State Timers
        for i in range(len(self.manifest)):
            seconds = self.state_timers[i]
            cycles = int(seconds * cycle_freq)
            msg.append(cycles)

        # Global Timers (Defaults)
        n_global_timers = self.hardware.get("n_global_timers", 0)
        for _ in range(n_global_timers):
            msg.append(0)  # Timers
        for _ in range(n_global_timers):
            msg.append(0)  # OnSetDelays
        for _ in range(n_global_timers):
            msg.append(0)  # LoopIntervals

        # Global Counters (Defaults)
        n_global_counters = self.hardware.get("n_global_counters", 0)
        for _ in range(n_global_counters):
            msg.append(0)  # Thresholds

        return struct.pack(f"<{len(msg)}I", *msg)

    def _resolve_state_indices(self):
        for i in range(len(self.manifest)):
            # State Timer Matrix
            dest = self.state_timer_matrix[i]
            if isinstance(dest, str):
                self.state_timer_matrix[i] = self._resolve_name(dest)

            # Input Matrix
            new_transitions = []
            for event_code, dest in self.input_matrix[i]:
                if isinstance(dest, str):
                    dest_idx = self._resolve_name(dest)
                    new_transitions.append((event_code, dest_idx))
            self.input_matrix[i] = new_transitions

    def _resolve_name(self, name):
        if name == "exit":
            return float("nan")
        try:
            return self.manifest.index(name)
        except ValueError:
            raise Exception(f"Unknown state: {name}")
