import math
import random
from collections import deque

import numpy as np

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase

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


class Bpod6Delay(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Delayed Side-Cue Discrimination Task, easy version (Bpod)
        -----------------------------------------------------------------------------
        - Middle port LED turns ON until the animal pokes the middle port,
          for up to c_led_on_time seconds. No poke: the trial ends as an
          omission (it doesn't count for the difficulty adaptation).
        - Middle LED turns OFF. After 100 ms:
            * One lateral port LED (left/right, random) turns ON.
            * After a random delay, the opposite lateral LED turns ON too.
        - The animal has up to 40s total to respond. Correct choice: poke the
          side that was illuminated first.
            * Correct response: side LEDs OFF, reward at the reward port, 1s ITI.
            * Incorrect response: side LEDs OFF, 3s buzzer, 3s timeout total.
            * No response: trial aborted, sequence restarts.

        The delay is drawn from a distribution controlled by self.p (0-1):
        higher self.p means the second cue tends to come later, making the
        trial harder. self.p is tuned automatically after every trial based
        on a rolling accuracy window (see after_trial).
        """

    def start(self):
        """Use the calibration to get the valve opening times (in seconds) for
        ports 1 (left) and 3 (right), for both the normal and large reward
        volumes. Also pre-generates the first-cued side for every trial in
        the session, and initializes the rolling-accuracy bookkeeping used to
        adapt the task's difficulty (self.p).

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: normal reward volume delivered on a
          correct poke
        - self.settings.reward_volume_large: larger reward volume, given on
          ~10% of trials
        - self.settings.led_intensity: port LED brightness (0-255)
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
        # current_trial starts at 1, the side vector at 0.
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
            correct_poke = BpodEvent.Port1In
            wrong_poke = BpodEvent.Port3In
            valvetime = self.valve_l_time_large if large_reward else self.valve_l_time
            valve_action = BpodOutput.Valve1
            first_led = (BpodOutput.PWM1, self.settings.led_intensity)
        else:  # right
            self.correct_side = "right"
            correct_poke = BpodEvent.Port3In
            wrong_poke = BpodEvent.Port1In
            valvetime = self.valve_r_time_large if large_reward else self.valve_r_time
            valve_action = BpodOutput.Valve3
            first_led = (BpodOutput.PWM3, self.settings.led_intensity)

        # 'c_led_on': center LED on, waits for the trial-initiating center poke.
        # SoftCode2 loads the penalty sound now (direct_functions.function2),
        # well ahead of when it's actually needed in 'wrong_choice' below.
        self.bpod.add_state(
            state_name="c_led_on",
            state_timer=self.settings.c_led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",  # no center poke -> omission
                BpodEvent.Port2In: "first_side_led",
            },
            output_actions=[
                (BpodOutput.PWM2, self.settings.led_intensity),
                BpodOutput.SoftCode2,
            ],
        )

        # 'first_side_led': only the first-cued side is lit, for self.delay seconds
        self.bpod.add_state(
            state_name="first_side_led",
            state_timer=self.delay,
            state_change_conditions={
                correct_poke: "correct_choice",
                wrong_poke: "wrong_choice",
                BpodEvent.Tup: "both_side_leds",
            },
            output_actions=[first_led],
        )

        # 'both_side_leds': both sides lit, for the remainder of the 40s response window
        self.bpod.add_state(
            state_name="both_side_leds",
            state_timer=40 - self.delay,
            state_change_conditions={
                correct_poke: "correct_choice",
                wrong_poke: "wrong_choice",
                BpodEvent.Tup: "exit",  # no response -> restart trial
            },
            output_actions=[
                (BpodOutput.PWM1, self.settings.led_intensity),
                (BpodOutput.PWM3, self.settings.led_intensity),
            ],
        )

        # 'correct_choice': reward, then ITI
        self.bpod.add_state(
            state_name="correct_choice",
            state_timer=valvetime,
            state_change_conditions={BpodEvent.Tup: "iti"},
            output_actions=[valve_action],
        )

        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

        # 'wrong_choice': plays the sound loaded back in 'c_led_on'
        # (SoftCode4 -> direct_functions.function4), then silent timeout for
        # the rest of the penalty
        self.bpod.add_state(
            state_name="wrong_choice",
            state_timer=self.settings.noise_time,
            state_change_conditions={BpodEvent.Tup: "timeout"},
            output_actions=[BpodOutput.SoftCode4],
        )

        self.bpod.add_state(
            state_name="timeout",
            state_timer=self.settings.timeout - self.settings.noise_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        """Work out response_side and outcome, then adapt self.p based on a
        rolling accuracy window.

        Both correct_poke and wrong_poke are wired as transitions in both
        "first_side_led" and "both_side_leds" (see create_trial), so the
        first poke on either side -- whichever state it happens in -- is the
        animal's response.
        """

        # 1. This is the moment the first cue turned on. If it never did (no
        # center poke; Bpod lists a state not visited as [nan]), it's an
        # omission: the animal didn't choose, so it doesn't count for the
        # accuracy nor for adapting the difficulty.
        t_first_side_led = self.trial_data.get(
            "STATE_first_side_led_START", [math.nan]
        )[0]
        if math.isnan(t_first_side_led):
            self.register_value("p", self.p)
            self.register_value("water", 0)
            self.register_value("outcome", "omission")
            self.register_value("response_side", "none")
            self.register_value("rewarded_side", self.correct_side)
            self.register_value("delay_cues", self.signed_delay)
            return

        # 2 & 3. Pokes on the correct/wrong port, at or after the first cue.
        correct_key, wrong_key = (
            ("Port1In", "Port3In")
            if self.correct_side == "left"
            else ("Port3In", "Port1In")
        )
        correct_pokes = [
            t for t in self.trial_data.get(correct_key, []) if t >= t_first_side_led
        ]
        wrong_pokes = [
            t for t in self.trial_data.get(wrong_key, []) if t >= t_first_side_led
        ]

        # 4 & 5. Whichever port got poked first, if any, decides the outcome.
        if correct_pokes and (not wrong_pokes or correct_pokes[0] <= wrong_pokes[0]):
            response_side = self.correct_side
            outcome = "correct"
            correct = 1
            t_choice = correct_pokes[0]
        elif wrong_pokes:
            response_side = "right" if self.correct_side == "left" else "left"
            outcome = "incorrect"
            correct = 0
            t_choice = wrong_pokes[0]
        else:
            response_side = "none"
            outcome = "miss"
            correct = 0
            t_choice = None

        water = self.reward_volume if outcome == "correct" else 0

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

        if t_choice is not None:
            self.register_value("first_trial_response_time", t_choice)
        self.register_value("running_accuracy", running_accuracy)
        self.register_value("p", self.p)
        self.register_value("water", water)
        self.register_value("outcome", outcome)
        self.register_value("response_side", response_side)
        self.register_value("rewarded_side", self.correct_side)
        self.register_value("delay_cues", self.signed_delay)

    def close(self):
        pass
