import logging
import struct

import serial

logger = logging.getLogger(__name__)


class Bpod:
    def __init__(self, serial_port, baudrate=115200, timeout=1):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_object = None
        self.firmware_version = None
        self.hardware_info = {}

    def connect(self):
        """
        Connect to the Bpod device, perform handshake, and retrieve initial info.
        """
        try:
            print(f"Connecting to Bpod on {self.serial_port}...")
            self.serial_object = serial.Serial(
                self.serial_port, baudrate=self.baudrate, timeout=self.timeout
            )

            # Reset buffers to clear any previous data (like discovery bytes)
            self.serial_object.reset_input_buffer()
            self.serial_object.reset_output_buffer()

            # Handshake
            if not self._handshake():
                print("Handshake failed.")
                self.close()
                return False

            print("Handshake successful.")

            # Get Firmware Version
            self.firmware_version = self._get_firmware_version()
            print(f"Firmware Version: {self.firmware_version}")

            # Get Hardware Description
            self.hardware_info = self._get_hardware_description()
            print(f"Hardware Info: {self.hardware_info}")

            # Enable Ports
            if self._enable_ports():
                print("Ports enabled.")
            else:
                print("Failed to enable ports.")

            return True

        except Exception as e:
            print(f"Error connecting to Bpod: {e}")
            self.close()
            return False

    def close(self):
        if self.serial_object and self.serial_object.is_open:
            self.serial_object.close()
            print("Connection closed.")

    def _handshake(self):
        # Send '6', expect '5'
        # Handle discovery byte 0xDE (222)
        self.serial_object.write(b"6")

        max_retries = 20
        for _ in range(max_retries):
            byte = self.serial_object.read(1)
            if byte == b"5":
                return True
            elif byte == b"\xde":
                continue  # Ignore discovery byte
            elif byte == b"":
                continue  # Timeout, try again
            else:
                print(f"Unexpected handshake response: {byte}")

        return False

    def _get_firmware_version(self):
        # Send 'F', expect version (uint32)
        self.serial_object.write(b"F")
        response = self.serial_object.read(4)
        if len(response) == 4:
            # Assuming Little Endian based on typical microcontroller structs
            # But original code might treat it differently.
            # Let's check if it's just a number.
            # Original code: version = self._arcom.read_uint32()
            version = struct.unpack("<I", response)[0]
            return version
        return None

    def _get_hardware_description(self):
        # Send 'H', expect hardware description
        self.serial_object.write(b"H")

        # Header:
        # MaxStates (uint16)
        # CyclePeriod (uint16)
        # MaxSerialEvents (uint8)
        # nGlobalTimers (uint8)
        # nGlobalCounters (uint8)
        # nConditions (uint8)
        # nInputs (uint8)

        header_size = 2 + 2 + 1 + 1 + 1 + 1 + 1
        header = self.serial_object.read(header_size)

        if len(header) != header_size:
            print("Failed to read hardware header.")
            return None

        info = {}
        (
            info["max_states"],
            info["cycle_period"],
            info["max_serial_events"],
            info["n_global_timers"],
            info["n_global_counters"],
            info["n_conditions"],
            n_inputs,
        ) = struct.unpack("<HHBBBBB", header)

        # Read Inputs (n_inputs bytes)
        inputs = self.serial_object.read(n_inputs)
        info["inputs"] = [chr(b) for b in inputs]

        # Read nOutputs (uint8)
        n_outputs_byte = self.serial_object.read(1)
        if len(n_outputs_byte) != 1:
            return None
        n_outputs = struct.unpack("<B", n_outputs_byte)[0]

        # Read Outputs (n_outputs bytes)
        outputs = self.serial_object.read(n_outputs)
        info["outputs"] = [chr(b) for b in outputs]

        return info

    def _enable_ports(self):
        # Send 'E' followed by enable status for each input (1=enabled, 0=disabled)
        # We enable all inputs by default for now.
        if "inputs" not in self.hardware_info:
            print("Cannot enable ports: Hardware info not loaded.")
            return False

        n_inputs = len(self.hardware_info["inputs"])
        # Create message: 'E' + [1, 1, ..., 1]
        msg = [ord("E")] + [1] * n_inputs

        self.serial_object.write(bytes(msg))

        # Expect 1 (0x01) confirmation
        response = self.serial_object.read(1)
        return response == b"\x01"

    def send_state_machine(self, sma):
        """
        Send state machine definition to Bpod.
        """
        print("Sending State Machine...")

        # 1. Get components
        body_msg = sma.build()
        time_msg = sma.build_32bit_message()

        # 2. Construct Header
        # 'C' + RunASAP(0) + Use255Back(0) + TotalSize(uint16)
        total_size = len(body_msg) + len(time_msg)
        header = struct.pack("<BBBH", ord("C"), 0, 0, total_size)

        # 3. Send everything
        full_message = header + body_msg + time_msg
        self.serial_object.write(full_message)

        # DO NOT wait for confirmation here.
        # The confirmation comes after 'R' command.

        print("State Machine sent (waiting for Run to confirm).")
        return True

    def run_state_machine(self):
        """
        Run the currently loaded state machine.
        """
        print("Running State Machine...")
        self.serial_object.write(b"R")

        # Read confirmation byte (1 = Success, 0 = Fail)
        confirmation = self.serial_object.read(1)
        if confirmation == b"\x01":
            print("State Machine installation confirmed. Running...")
        elif confirmation == b"\x00":
            print("State Machine installation FAILED.")
            return
        else:
            print(f"Unexpected confirmation: {confirmation}")
            # Continue anyway? No, probably failed.

        # Event Loop
        try:
            while True:
                if self.serial_object.in_waiting >= 2:
                    # Read Opcode and Data
                    header = self.serial_object.read(2)
                    opcode = header[0]
                    data = header[1]

                    if opcode == 1:  # Read Events
                        n_events = data
                        events = self.serial_object.read(n_events)
                        timestamp_bytes = self.serial_object.read(4)
                        timestamp = struct.unpack("<I", timestamp_bytes)[0]

                        # Decode events
                        # We need the event list from the state machine to decode names
                        # For now, we'll just yield/print raw codes if
                        # we don't have the map
                        # But we can try to use a callback or just print

                        # Check for exit code 255
                        if b"\xff" in events:
                            print("State Machine finished.")
                            break

                        # Print human-readable events
                        event_names = self.get_event_names()
                        readable_events = []
                        for e in events:
                            if e == 255:
                                continue  # Already handled exit
                            if e < len(event_names):
                                readable_events.append(event_names[e])
                            else:
                                readable_events.append(f"Unknown({e})")

                        text = f"Time: {timestamp/10000.0:.4f}s | "
                        text += f"Events: {readable_events}"
                        print(text)

                    elif opcode == 2:  # Soft Code
                        print(f"Soft Code: {data}")

        except KeyboardInterrupt:
            print("Stopping...")
            self.serial_object.write(b"X")

    def get_event_names(self):
        """
        Generate the list of event names based on the hardware configuration.
        The index in this list corresponds to the event code.

        NOTE: Serial/USB events are skipped because we don't have module information.
        In the original API, these events are only added if modules are connected
        and configured with specific n_serial_events.
        """
        events = []
        inputs = self.hardware_info.get("inputs", [])

        # Skip Serial Events (U) and USB/SoftCodes (X) for now
        # The firmware only includes these if modules are configured,
        # and we don't have that information in the simplified API.
        # TODO: Add module support if needed in the future.

        # Digital Inputs
        n_ports = 0
        n_bnc = 0
        n_wire = 0

        for input_type in inputs:
            if input_type == "P":
                n_ports += 1
                events.append(f"Port{n_ports}In")
                events.append(f"Port{n_ports}Out")
            elif input_type == "B":
                n_bnc += 1
                events.append(f"BNC{n_bnc}High")
                events.append(f"BNC{n_bnc}Low")
            elif input_type == "W":
                n_wire += 1
                events.append(f"Wire{n_wire}High")
                events.append(f"Wire{n_wire}Low")

        # Global Timers
        n_global_timers = self.hardware_info.get("n_global_timers", 0)
        for i in range(n_global_timers):
            events.append(f"GlobalTimer{i+1}Start")
        for i in range(n_global_timers):
            events.append(f"GlobalTimer{i+1}End")

        # Global Counters
        n_global_counters = self.hardware_info.get("n_global_counters", 0)
        for i in range(n_global_counters):
            events.append(f"GlobalCounter{i+1}End")

        # Conditions
        n_conditions = self.hardware_info.get("n_conditions", 0)
        for i in range(n_conditions):
            events.append(f"Condition{i+1}")

        events.append("Tup")
        return events
