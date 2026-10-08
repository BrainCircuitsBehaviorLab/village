import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Protocol (see arduino_1_habituation.ino):
#
# Pi -> Arduino, 3 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, duration_s (uint16, little-endian)]
#   Tells the Arduino how long this trial lasts. From here the Arduino
#   watches the 3 poke sensors on its own; the Pi just listens.
#
# Arduino -> Pi, 6 raw bytes per message:
#   [EVENT_STATE, state, elapsed_ms (uint32, LE)]
#     -- every time the Arduino enters a new state (see STATE_NAMES), so it
#        can be registered with register_enter_state, as Bpod does.
#   [EVENT_TRIAL_END, port (0 if nobody poked), elapsed_ms (uint32, LE)]
#     -- once, when the trial is over.
#   elapsed_ms is milliseconds since the Arduino received CMD_START_TRIAL
#   for THIS trial (its own timer, reset every trial). It is the controller
#   clock: the trial start is registered as controller time 0 at the moment
#   the Pi sent CMD_START_TRIAL, and every elapsed_ms as a controller
#   timestamp (register_controller_event / register_enter_state), so the two
#   clocks never need to be synchronized.
CMD_START_TRIAL = 1
EVENT_TRIAL_END = 1
EVENT_STATE = 3

# State ids sent by the Arduino (same names as bpod_1_habituation.py)
STATE_NAMES = {1: "ready_to_explore"}

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop gets re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes
STATE_DURATION = 60  # seconds


class Arduino1Habituation(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = """
        Habituation Task
        ----------------------------------------------------------
        Lets a mouse get used to being in the box on its own. Every trial,
        the Pi tells the Arduino how long to wait (STATE_DURATION), and the
        Arduino watches all 3 ports for that whole window, ending the trial
        early the moment any one of them is poked. No reward is delivered --
        pokes are only recorded, to see the animal is exploring the box.
        """

    def start(self):
        """Opens the serial connection to the Arduino."""

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        self.serial_port.reset_input_buffer()

    def create_trial(self):
        """Tells the Arduino how long this trial should last, then waits for
        its single reply: either a port number (whichever was poked first)
        or 0 if the whole duration passed with no poke at all.

        The deadline below is only a safety net for a lost/garbled message
        -- in normal operation the Arduino's own reply always arrives well
        before it.
        """

        self.serial_port.write(struct.pack("<BH", CMD_START_TRIAL, STATE_DURATION))
        t_sent = time_utils.now_timestamp()
        # The Arduino's clock (elapsed_ms) starts at 0 when it gets the command.
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        deadline = t_sent + STATE_DURATION + 2.0  # margin for serial/USB latency
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                continue  # nothing arrived within READ_TIMEOUT; keep waiting
            buffer += chunk
            if len(buffer) < MESSAGE_SIZE:
                continue

            event, value, elapsed_ms = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            t = elapsed_ms / 1000.0  # controller clock, seconds

            if event == EVENT_STATE:
                self.register_enter_state(STATE_NAMES.get(value, f"state{value}"), t)
            elif event == EVENT_TRIAL_END:
                if value != 0:  # the port that was poked
                    self.register_controller_event(f"Port{value}In", t)
                self.register_end_trial(t)
                break
        # If the loop ended without EVENT_TRIAL_END (task stopped, or a lost
        # message), the trial is ended automatically when this returns.

    def after_trial(self):
        """Reads back whichever port event create_trial registered, if any,
        to label the trial."""

        outcome = "miss"
        if self.trial_data.get("Port1In"):
            outcome = "left_poke"
        elif self.trial_data.get("Port2In"):
            outcome = "center_poke"
        elif self.trial_data.get("Port3In"):
            outcome = "right_poke"

        self.register_value("outcome", outcome)
        self.register_value("water", 0)

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
