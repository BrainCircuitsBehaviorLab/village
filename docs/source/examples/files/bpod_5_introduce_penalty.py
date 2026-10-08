import math
import random

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class Bpod5IntroducePenalty(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Center-Initiated Side Alternation Task, with penalty (Bpod)
        -----------------------------------------------------------------------------
        Purpose: introduce a penalty for the wrong-side poke
        - Structure:
            * Mice initiate each trial by poking the center port (center LED on).
            * After the center poke, one side LED turns on.
            * Only that side delivers reward (correct side); the correct side is
              chosen at random every trial.
        - Trial logic:
            * Correct poke -> water delivery.
            * Wrong poke -> time-out, buzzer noise, and trial termination.
            * After reward or time-up, a short delay before the next trial.
        """

    def start(self):
        """Use the calibration to get the valve opening times (in seconds) for
        ports 1 (left) and 3 (right), for both the normal and large reward
        volumes.

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: normal reward volume delivered on a
          correct poke
        - self.settings.reward_volume_large: larger reward volume, given on
          ~10% of trials
        - self.settings.led_intensity: port LED brightness (0-255)
        - self.settings.c_led_on_time: time allowed to poke the center port, seconds
        - self.settings.led_on_time: time allowed to poke the correct side, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        - self.settings.noise_time: buzzer duration after a wrong poke, seconds
        - self.settings.timeout: total penalty duration (buzzer + silence), seconds
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

    def create_trial(self):
        self.side = random.choice(["left", "right"])
        large_reward = random.random() < 0.10
        self.reward_volume = (
            self.settings.reward_volume_large
            if large_reward
            else self.settings.reward_volume
        )

        if self.side == "left":
            valvetime = self.valve_l_time_large if large_reward else self.valve_l_time
            valve_action = BpodOutput.Valve1
            correct_led = (BpodOutput.PWM1, self.settings.led_intensity)
            correct_side = BpodEvent.Port1In
            wrong_side = BpodEvent.Port3In
        else:
            valvetime = self.valve_r_time_large if large_reward else self.valve_r_time
            valve_action = BpodOutput.Valve3
            correct_led = (BpodOutput.PWM3, self.settings.led_intensity)
            correct_side = BpodEvent.Port3In
            wrong_side = BpodEvent.Port1In

        # 'c_led_on': center LED on, waits for the trial-initiating center poke.
        # SoftCode2 loads the penalty sound now (direct_functions.function2),
        # well ahead of when it's actually needed in 'wrong_choice' below.
        self.bpod.add_state(
            state_name="c_led_on",
            state_timer=self.settings.c_led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                BpodEvent.Port2In: "side_led_on",
            },
            output_actions=[
                (BpodOutput.PWM2, self.settings.led_intensity),
                BpodOutput.SoftCode2,
            ],
        )

        # 'side_led_on': only the correct side's LED turns on -- a wrong poke
        # now leads to a penalty instead of being ignored (see bpod_4).
        self.bpod.add_state(
            state_name="side_led_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                correct_side: "water_delivery",
                wrong_side: "wrong_choice",
            },
            output_actions=[correct_led],
        )

        self.bpod.add_state(
            state_name="water_delivery",
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
        # (SoftCode4 -> direct_functions.function4), then 'timeout': silent
        # penalty for the rest of the total penalty duration.
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
        """Work out response_side and outcome for this trial.

        Same logic as bpod_4_center_initiated: whichever side the animal
        poked first (if any) after the side LED turned on determines the
        outcome, independently of which Bpod state that poke happened to
        transition into.
        """

        # 1. The center poke never happened -> side LED never turned on -> omission.
        # Bpod lists a state that was not visited as [nan].
        t_side_led_on = self.trial_data.get("STATE_side_led_on_START", [math.nan])[0]
        if math.isnan(t_side_led_on):
            self.register_value("rewarded_side", self.side)
            self.register_value("water", 0)
            self.register_value("outcome", "omission")
            self.register_value("response_side", "none")
            return

        # 2 & 3. Pokes on the correct/wrong port, at or after the side LED turning on.
        correct_key, wrong_key = (
            ("Port1In", "Port3In") if self.side == "left" else ("Port3In", "Port1In")
        )
        correct_pokes = [
            t for t in self.trial_data.get(correct_key, []) if t >= t_side_led_on
        ]
        wrong_pokes = [
            t for t in self.trial_data.get(wrong_key, []) if t >= t_side_led_on
        ]

        # 4 & 5. Correct poke first -> water. Wrong poke (and no earlier correct
        # one) -> incorrect, penalty already applied in create_trial. Neither -> miss.
        if correct_pokes and (not wrong_pokes or correct_pokes[0] <= wrong_pokes[0]):
            outcome = "correct"
            response_side = self.side
            water = self.reward_volume
        elif wrong_pokes:
            outcome = "incorrect"
            response_side = "right" if self.side == "left" else "left"
            water = 0
        else:
            outcome = "miss"
            response_side = "none"
            water = 0

        self.register_value("rewarded_side", self.side)
        self.register_value("water", water)
        self.register_value("outcome", outcome)
        self.register_value("response_side", response_side)

    def close(self):
        pass
