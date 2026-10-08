import math
import random
import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Protocol (see arduino_3_active.ino):
#
# Pi -> Arduino, 6 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, correct_port,
#    led_on_timeout_ms (uint16, LE), valve_time_ms (uint16, LE)]
#   This is everything the Arduino needs to run the whole trial on its own:
#   which port is correct, how long to wait for a response, and how long to
#   open the valve for a correct one. From here the Arduino owns the
#   waiting/decision/valve logic -- the Pi just listens.
#
# Arduino -> Pi, 6 raw bytes per message:
#   [EVENT_POKE, port, elapsed_ms (uint32, LE)]
#     -- once per poke seen on EITHER port during the response window.
#        Only a poke on the correct port ends the window early; a poke on
#        the wrong port is reported too, but the Arduino keeps waiting.
#   [EVENT_STATE, state, elapsed_ms (uint32, LE)]
#     -- every time the Arduino enters a new state (see STATE_NAMES), so it
#        can be registered with register_enter_state, as Bpod does.
#   [EVENT_TRIAL_END, result, elapsed_ms (uint32, LE)]
#     -- once, when the response window is over: result is
#        RESULT_GOT_CORRECT if the correct port was poked before the
#        timeout (whether or not a wrong poke happened earlier), or
#        RESULT_TIMEOUT if it never was.
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

# State ids sent by the Arduino (same names as bpod_3_active.py). The ITI
# ("iti") is done by the Pi, after EVENT_TRIAL_END.
STATE_NAMES = {1: "led_on", 2: "water_delivery"}

RESULT_TIMEOUT = 0
RESULT_GOT_CORRECT = 1

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop/deadlines get re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes


class Arduino3Active(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Active learning, Water Delivery Task variation
        -----------------------------------------------------------------------------
        Teaches mice to approach the lickport.
        - Each trial, the Pi picks a port and sends it, along with the two
          timeouts it needs, to the Arduino in one message. From there the
          Arduino runs the trial on its own:
            * That port's LED turns on.
            * The animal has to poke it. A poke on the wrong port is
              recorded but doesn't end the wait -- only a poke on the
              correct port does (delivering reward), or the timeout running
              out with no correct poke at all.
        - Whichever port was poked first, chronologically, is what decides
          the logged outcome (correct/incorrect/miss) -- this can end up
          different from whether reward was actually given, if a wrong
          poke happened before an eventual correct one.
        """

    def start(self):
        """Opens the serial connection to the Arduino, and uses the calibration
        to get the valve opening times (in seconds) for ports 1 (left) and 3
        (right), for both the normal and large reward volumes -- sent to the
        Arduino once per trial, in create_trial().

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: normal reward volume delivered on a
          correct poke
        - self.settings.reward_volume_large: larger reward volume, given on
          ~10% of trials
        - self.settings.led_on_time: max duration of the "led_on" phase, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        """

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        # Discard anything left over from before this session started (e.g.
        # a stray message the Arduino sent while nobody was listening).
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
        """Picks the trial's correct port and reward volume, hands them to
        the Arduino in one message, then just listens for whatever it
        reports until it signals the trial is over. The deadline below is
        only a safety net for a lost/garbled message -- in normal operation
        the Arduino's own EVENT_TRIAL_END always arrives well before it.
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

        led_on_timeout_ms = int(self.settings.led_on_time * 1000)
        valve_time_ms = int(valvetime * 1000)

        # Hand the whole trial over to the Arduino.
        self.serial_port.write(
            struct.pack(
                "<BBHH", CMD_START_TRIAL, port, led_on_timeout_ms, valve_time_ms
            )
        )
        t_sent = time_utils.now_timestamp()
        # The Arduino's clock (elapsed_ms) starts at 0 when it gets the command.
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        self.got_correct_poke = False
        t_end = None  # controller time of EVENT_TRIAL_END
        deadline = (
            t_sent
            + self.settings.led_on_time
            + valvetime
            + self.settings.iti_time
            + 2.0  # margin for serial/USB latency, never expected to matter
        )
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                # nothing arrived within READ_TIMEOUT; loop back to
                # re-check should_stop/deadline
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
                self.got_correct_poke = value == RESULT_GOT_CORRECT
                t_end = t
                break

        if t_end is None:
            return  # stopped or lost message: the trial is ended automatically

        if self.got_correct_poke:
            # The ITI is timed by the Pi, starting when the Arduino finished.
            self.register_enter_state("iti", t_end)
            t_end += self.wait(self.settings.iti_time)
        self.register_end_trial(t_end)

    def wait(self, seconds):
        """Waits up to `seconds` (less if the task is asked to stop), discarding
        any stray serial bytes. Returns the time actually waited, in seconds."""

        start = time_utils.now_timestamp()
        while not self.should_stop and time_utils.now_timestamp() < start + seconds:
            self.serial_port.read(MESSAGE_SIZE)
        return time_utils.now_timestamp() - start

    def after_trial(self):
        """Works out response_side and outcome for this trial from the
        poke events registered in create_trial.

        A poke on the wrong side doesn't end the response window early
        (see create_trial), but it's still logged -- so a poke there is
        still a valid (incorrect) response, not nothing happening. Note
        this is evaluated independently of self.got_correct_poke: if a
        wrong poke happened before an eventual correct one, the outcome
        below is "incorrect" even though reward was actually delivered.
        """

        # 1. The moment the LED turned on and the animal could start responding.
        t_led_on = self.trial_data.get("STATE_led_on_START", [math.nan])[0]

        # 2. All the pokes registered on each port during the whole trial.
        left_pokes = self.trial_data.get("Port1In", [])
        right_pokes = self.trial_data.get("Port3In", [])

        # 3. Keep only the pokes that happened after the LED turned on.
        left_pokes = [t for t in left_pokes if t >= t_led_on]
        right_pokes = [t for t in right_pokes if t >= t_led_on]

        # 4. Whichever side got poked first, if any.
        if left_pokes and (not right_pokes or left_pokes[0] < right_pokes[0]):
            response_side = "left"
        elif right_pokes:
            response_side = "right"
        else:
            response_side = "none"

        # 5. No poke -> miss. Otherwise correct/incorrect, water only on correct.
        if response_side == "none":
            outcome = "miss"
            water = 0
        else:
            outcome = "correct" if response_side == self.side else "incorrect"
            water = self.reward_volume if outcome == "correct" else 0

        self.register_value("rewarded_side", self.side)
        self.register_value("water", water)
        self.register_value("outcome", outcome)
        self.register_value("response_side", response_side)

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
