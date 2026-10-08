import random
import struct
from collections import deque

import numpy as np
import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Curriculum-based probability distribution over delay values, used by
# create_trial() to pick each trial's delay. As learning progress p goes
# from 0 to 1, longer delays are introduced gradually instead of all at
# once: at p=0 only the easiest (shortest) delays are likely, at p=1 every
# delay is equally likely. thresholds[d] is the p value at which delay d
# starts being seriously considered; tau controls how sharp that
# introduction is, gamma how strongly the curriculum favors easier delays
# below their threshold.
_DELAYS = np.array([0, 0.1, 0.25, 0.5, 1, 40])
_THRESHOLDS = {1: 0.001, 40: 0.0, 0.5: 0.25, 0.25: 0.50, 0.1: 0.65, 0: 0.75}


def get_delay_probabilities(
    p: float, tau: float = 0.08, gamma: float = 3
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (delays, probabilities) -- probabilities sums to 1, same
    order as _DELAYS -- for np.random.choice(delays, p=probabilities)."""
    weights = []
    for d in _DELAYS:
        t = _THRESHOLDS[float(d)]
        # t == 0 (the easiest delay) never fades out, it just slowly loses
        # dominance to the others as p grows.
        a = 1.0 if t == 0 else 1.0 / (1.0 + np.exp(-(p - t) / tau))
        weights.append(a**gamma)
    weights = np.array(weights)
    return _DELAYS, weights / weights.sum()


# Protocol (see arduino_6_delay.ino):
#
# Pi -> Arduino, 10 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, first_port, c_led_on_timeout_ms (uint16, LE),
#    delay_ms (uint16, LE), total_timeout_ms (uint16, LE),
#    valve_time_ms (uint16, LE)]
#   Tells the Arduino which side lights up first this trial, how long to
#   wait for the center poke, how long to wait before lighting the other
#   side too, the overall response window, and the valve time for a
#   correct response. From here the Arduino runs
#   the whole trial (center poke, both cue phases, valve) on its own; the
#   Pi just listens and plays the penalty sound itself when told a wrong
#   poke happened (the Arduino has no speaker to do that with).
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

# State ids sent by the Arduino (same names as bpod_6_delay.py). "iti",
# "wrong_choice" and "timeout" are done by the Pi, after EVENT_TRIAL_END.
STATE_NAMES = {
    1: "c_led_on",
    2: "first_side_led",
    3: "both_side_leds",
    4: "correct_choice",
}

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
READ_TIMEOUT = 0.05  # seconds; also how often should_stop gets re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes
TOTAL_RESPONSE_WINDOW = 40  # seconds, from the first cue turning on


class Arduino6Delay(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Delayed Side-Cue Discrimination Task, easy version
        -----------------------------------------------------------------------------
        - The mouse must poke the center port to start each trial, within
          c_led_on_time seconds. No poke: the trial ends as an omission
          (it doesn't count for the difficulty adaptation).
        - One side's LED then turns on (the "first cue", side chosen at
          random each trial). If the delay set for this trial passes with
          no poke, the other side's LED turns on too, and the response
          window continues up to a fixed total.
        - Whichever port is poked first (in either phase) decides the
          outcome: correct if it's the side that was cued first, incorrect
          otherwise. No poke within the whole window is a miss.
            * correct -> reward, then a short delay before the next trial
            * incorrect -> the Pi plays a buzzer, then a silent timeout
            * miss -> the trial just ends, no penalty

        The delay is drawn from a distribution controlled by self.p (0-1):
        higher self.p means the second cue tends to come later, making the
        trial harder. self.p is tuned automatically after every trial based
        on a rolling accuracy window (see after_trial).
        """

    def start(self):
        """Opens the serial connection to the Arduino, and uses the
        calibration to get the valve opening times (in seconds) for ports 1
        (left) and 3 (right), for both the normal and large reward volumes.
        Also pre-generates the first-cued side for every trial in the
        session, and initializes the rolling-accuracy bookkeeping used to
        adapt the task's difficulty (self.p).

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: normal reward volume delivered on a
          correct poke
        - self.settings.reward_volume_large: larger reward volume, given on
          ~10% of trials
        - self.settings.c_led_on_time: max wait for the center poke, seconds
        - self.settings.iti_time: inter-trial interval after a correct
          response, seconds
        - self.settings.noise_time: buzzer duration after a wrong poke, seconds
        - self.settings.timeout: total penalty duration (buzzer + silence),
          seconds
        - self.settings.N_trials: size of the pre-generated first-cued-side
          sequence -- must be at least the number of trials the session can run
        - self.settings.p (optional, default 0.0): initial difficulty, 0-1
        - self.settings.curve_power (optional, default 3.0): shape parameter
          for the delay distribution, see get_delay_probabilities
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

        # The side of the first cue is decided once per session, not per
        # trial, so the whole sequence is reproducible/inspectable up front.
        self.first_led_side_vec = np.random.choice(
            [0, 1], size=int(self.settings.N_trials)
        )

        self.p = getattr(self.settings, "p", 0.0)

        # Rolling-window accuracy, used to adapt self.p after every trial.
        self.correct_history: list[int] = []
        self.adaptation_window: deque[int] = deque(maxlen=20)

    def create_trial(self):
        """Picks the trial's first-cued side, delay and reward volume,
        loads the penalty sound, hands everything the Arduino needs to
        run the trial in one message, then just listens for whatever it
        reports until it signals the trial is over. The deadline below is
        only a safety net for a lost/garbled message -- in normal operation
        the Arduino's own EVENT_TRIAL_END always arrives well before it.
        """

        first_side = self.first_led_side_vec[self.current_trial - 1]
        curve_power = getattr(self.settings, "curve_power", 3.0)
        delay_values, delay_probs = get_delay_probabilities(p=self.p, gamma=curve_power)
        self.delay = np.random.choice(delay_values, p=delay_probs)
        self.signed_delay = -self.delay if first_side == 0 else self.delay

        large_reward = random.random() < 0.10
        self.reward_volume = (
            self.settings.reward_volume_large
            if large_reward
            else self.settings.reward_volume
        )

        if first_side == 0:  # left
            self.correct_side = "left"
            port = 1
            valvetime = self.valve_l_time_large if large_reward else self.valve_l_time
        else:  # right
            self.correct_side = "right"
            port = 3
            valvetime = self.valve_r_time_large if large_reward else self.valve_r_time

        c_led_on_timeout_ms = int(self.settings.c_led_on_time * 1000)
        delay_ms = int(self.delay * 1000)
        total_timeout_ms = int(TOTAL_RESPONSE_WINDOW * 1000)
        valve_time_ms = int(valvetime * 1000)

        # Load the penalty sound now, well ahead of when it's actually
        # needed (see the "incorrect" branch below) -- this is Pi-only
        # hardware, the Arduino has no part in it.
        self.execute_function(2)

        self.serial_port.write(
            struct.pack(
                "<BBHHHH",
                CMD_START_TRIAL,
                port,
                c_led_on_timeout_ms,
                delay_ms,
                total_timeout_ms,
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
            + TOTAL_RESPONSE_WINDOW
            + valvetime
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
                self.outcome = _OUTCOME_NAMES.get(value, "miss")
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
        """Reads back the outcome the Arduino already decided, then adapts
        self.p based on a rolling accuracy window."""

        # No center poke: the animal didn't choose, so it doesn't count for
        # the accuracy nor for adapting the difficulty.
        if self.outcome == "omission":
            self.register_value("p", self.p)
            self.register_value("water", 0)
            self.register_value("outcome", "omission")
            self.register_value("response_side", "none")
            self.register_value("rewarded_side", self.correct_side)
            self.register_value("delay_cues", self.signed_delay)
            return

        if self.outcome == "correct":
            response_side = self.correct_side
            correct = 1
        elif self.outcome == "incorrect":
            response_side = "right" if self.correct_side == "left" else "left"
            correct = 0
        else:
            response_side = "none"
            correct = 0

        water = self.reward_volume if self.outcome == "correct" else 0

        # Adapt difficulty: raise self.p after a strong window, lower it
        # after a weak one, based on the last 20 trials.
        self.correct_history.append(correct)
        self.adaptation_window.append(correct)
        running_accuracy = np.mean(self.correct_history[-20:])
        if len(self.adaptation_window) >= self.adaptation_window.maxlen:
            window_accuracy = np.mean(self.adaptation_window)
            if window_accuracy > 0.75:
                self.p = min(self.p + 0.05, 1.0)
                self.adaptation_window.clear()
            elif window_accuracy < 0.50:
                self.p = max(self.p - 0.05, 0.0)
                self.adaptation_window.clear()

        # The response is the first side poke (Port1In / Port3In), if any.
        side_pokes = self.trial_data.get("Port1In", []) + self.trial_data.get(
            "Port3In", []
        )
        if side_pokes:
            self.register_value("first_trial_response_time", min(side_pokes))
        self.register_value("running_accuracy", running_accuracy)
        self.register_value("p", self.p)
        self.register_value("water", water)
        self.register_value("outcome", self.outcome)
        self.register_value("response_side", response_side)
        self.register_value("rewarded_side", self.correct_side)
        self.register_value("delay_cues", self.signed_delay)

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
