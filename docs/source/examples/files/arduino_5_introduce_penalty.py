import random
import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Protocol (see arduino_5_introduce_penalty.ino):
#
# Pi -> Arduino, 8 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, correct_port,
#    c_led_on_timeout_ms (uint16, LE),
#    led_on_timeout_ms (uint16, LE),
#    valve_time_ms (uint16, LE)]
#   Tells the Arduino which side port is correct this trial and the three
#   timings it needs. From here the Arduino runs the whole trial (center
#   poke, side poke, valve) on its own; the Pi just listens and plays the
#   penalty sound itself when told a wrong poke happened (the Arduino has
#   no speaker to do that with).
#
# Arduino -> Pi, 6 raw bytes per message:
#   [EVENT_POKE, port, elapsed_ms (uint32, LE)]
#     -- once per poke that matters (the center poke, then whichever side
#        port is poked first)
#   [EVENT_STATE, state, elapsed_ms (uint32, LE)]
#     -- every time the Arduino enters a new state (see STATE_NAMES), so it
#        can be registered with register_enter_state, as Bpod does.
#   [EVENT_TRIAL_END, outcome, elapsed_ms (uint32, LE)]
#     -- once, when the trial is over
#   elapsed_ms is milliseconds since the Arduino received CMD_START_TRIAL
#   for THIS trial (its own timer, reset every trial). It is the controller
#   clock: the trial start is registered as controller time 0 at the moment
#   the Pi sent CMD_START_TRIAL, and every elapsed_ms as a controller
#   timestamp (register_controller_event / register_enter_state), so the two
#   clocks never need to be synchronized.
CMD_START_TRIAL = 1

EVENT_POKE = 1
EVENT_TRIAL_END = 2
EVENT_STATE = 3

# State ids sent by the Arduino (same names as bpod_5_introduce_penalty.py).
# "iti", "wrong_choice" and "timeout" are done by the Pi, after
# EVENT_TRIAL_END.
STATE_NAMES = {1: "c_led_on", 2: "side_led_on", 3: "water_delivery"}

OUTCOME_OMISSION = 0
OUTCOME_CORRECT = 1
OUTCOME_INCORRECT = 2
OUTCOME_MISS = 3
_OUTCOME_NAMES = {
    OUTCOME_OMISSION: "omission",
    OUTCOME_CORRECT: "correct",
    OUTCOME_INCORRECT: "incorrect",
    OUTCOME_MISS: "miss",
}

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop/deadlines get re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes


class Arduino5IntroducePenalty(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Center-Initiated Side Alternation Task, with penalty
        -----------------------------------------------------------------------------
        Same idea as plain center-initiation, plus a penalty for choosing
        the wrong side: a buzzer and a timeout before the next trial.
        - The Pi picks which side is correct this trial, loads the penalty
          sound (ready ahead of time, in case it's needed), and sends the
          trial's port and timings to the Arduino. The Arduino runs the
          rest on its own:
            * The center LED turns on; the mouse must poke it to start the
              trial's response phase. No poke within its own window is an
              omission -- the trial ends there.
            * The correct side's LED then turns on. Whichever port is
              poked first decides the outcome:
                - correct -> reward, then a short delay before the next trial
                - wrong -> the Pi plays the already-loaded buzzer sound,
                  then a silent timeout
                - neither, before the window ends -> miss, no penalty
        """

    def start(self):
        """Opens the serial connection to the Arduino, and uses the
        calibration to get the valve opening times (in seconds) for ports 1
        (left) and 3 (right), for both the normal and large reward volumes.

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: normal reward volume delivered on a
          correct poke
        - self.settings.reward_volume_large: larger reward volume, given on
          ~10% of trials
        - self.settings.c_led_on_time: time allowed to poke the center port, seconds
        - self.settings.led_on_time: time allowed to poke the correct side, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        - self.settings.noise_time: buzzer duration after a wrong poke, seconds
        - self.settings.timeout: total penalty duration (buzzer + silence), seconds
        """

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        self.serial_port.reset_input_buffer()

        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_l_time_large = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume_large
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )
        self.valve_r_time_large = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume_large
        )

    def create_trial(self):
        """Picks the trial's correct side and reward volume, loads the
        penalty sound, hands the port and timings to the Arduino in one
        message, then just listens for whatever it reports until it
        signals the trial is over. The deadline below is only a safety net
        for a lost/garbled message -- in normal operation the Arduino's own
        EVENT_TRIAL_END always arrives well before it.
        """

        self.side = random.choice(["left", "right"])
        large_reward = random.random() < 0.10
        self.reward_volume = (
            self.settings.reward_volume_large
            if large_reward
            else self.settings.reward_volume
        )

        if self.side == "left":
            valvetime = self.valve_l_time_large if large_reward else self.valve_l_time
            port = 1
        else:
            valvetime = self.valve_r_time_large if large_reward else self.valve_r_time
            port = 3

        c_led_on_timeout_ms = int(self.settings.c_led_on_time * 1000)
        led_on_timeout_ms = int(self.settings.led_on_time * 1000)
        valve_time_ms = int(valvetime * 1000)

        # Load the penalty sound now, well ahead of when it's actually
        # needed (see the "incorrect" branch below) -- this is Pi-only
        # hardware, the Arduino has no part in it.
        self.execute_function(2)

        self.serial_port.write(
            struct.pack(
                "<BBHHH",
                CMD_START_TRIAL,
                port,
                c_led_on_timeout_ms,
                led_on_timeout_ms,
                valve_time_ms,
            )
        )
        t_sent = time_utils.now_timestamp()
        # The Arduino's clock (elapsed_ms) starts at 0 when it gets the command.
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        self.outcome = "omission"
        t_end = None  # controller time of EVENT_TRIAL_END
        deadline = (
            t_sent
            + self.settings.c_led_on_time
            + self.settings.led_on_time
            + valvetime
            + self.settings.timeout
            + self.settings.iti_time
            + 2.0  # margin for serial/USB latency, never expected to matter
        )
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                continue
            buffer += chunk
            if len(buffer) < MESSAGE_SIZE:
                continue

            event, value, elapsed_ms = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            t = elapsed_ms / 1000.0  # controller clock, seconds

            if event == EVENT_STATE:
                self.register_enter_state(STATE_NAMES.get(value, f"state{value}"), t)

            elif event == EVENT_POKE:
                self.register_controller_event(f"Port{value}In", t)
            elif event == EVENT_TRIAL_END:
                self.outcome = _OUTCOME_NAMES.get(value, "omission")
                t_end = t
                break

        if t_end is None:
            return  # stopped or lost message: the trial is ended automatically

        # The ITI and the penalty are timed by the Pi, starting when the
        # Arduino finished, with the same states as the Bpod version.
        if self.outcome == "correct":
            self.register_enter_state("iti", t_end)
            t_end += self.wait(self.settings.iti_time)
        elif self.outcome == "incorrect":
            self.register_enter_state("wrong_choice", t_end)
            self.execute_function(4)  # play the sound loaded above
            t_end += self.wait(self.settings.noise_time)
            if not self.should_stop:
                self.register_enter_state("timeout", t_end)
                t_end += self.wait(self.settings.timeout - self.settings.noise_time)
        self.register_end_trial(t_end)

    def wait(self, seconds):
        """Waits up to `seconds` (less if the task is asked to stop), discarding
        any stray serial bytes. Returns the time actually waited, in seconds."""

        start = time_utils.now_timestamp()
        while not self.should_stop and time_utils.now_timestamp() < start + seconds:
            self.serial_port.read(MESSAGE_SIZE)
        return time_utils.now_timestamp() - start

    def after_trial(self):
        """Reads back the outcome the Arduino already decided (the penalty
        sound was already played in create_trial, if needed) to work out
        response_side and the water given."""

        if self.outcome == "correct":
            response_side = self.side
            water = self.reward_volume
        elif self.outcome == "incorrect":
            response_side = "right" if self.side == "left" else "left"
            water = 0
        else:
            response_side = "none"
            water = 0

        self.register_value("rewarded_side", self.side)
        self.register_value("water", water)
        self.register_value("outcome", self.outcome)
        self.register_value("response_side", response_side)

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
