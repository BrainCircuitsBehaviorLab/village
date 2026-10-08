import random

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class Bpod3Active(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Active learning, Water Delivery Task variation (Bpod)
        -----------------------------------------------------------------------------
        The task is designed to teach mice to approach the lickport:
        - Each trial starts with:
            * LED on the rewarded port turns on (one of the two ports)
            * The animal has to poke in the port with the led on
            * Reward valve opens (water is delivered)
        - The LED remains ON until:
            * A poke is detected in the correct port
            * Or a time up occurs
        If the animal pokes in the wrong port nothing will happen, the mice
        will remain in the same state until pokes in the "correct" port.
        Reward is set at 2nl, and 5nl randomly in 10% of the trials.
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
        - self.settings.led_intensity: side port LED brightness (0-255)
        - self.settings.led_on_time: max duration of the "led_on" state, seconds
        - self.settings.iti_time: inter-trial interval, seconds
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
            light_led = (BpodOutput.PWM1, self.settings.led_intensity)
            correct_side = BpodEvent.Port1In
        else:
            valvetime = self.valve_r_time_large if large_reward else self.valve_r_time
            valve_action = BpodOutput.Valve3
            light_led = (BpodOutput.PWM3, self.settings.led_intensity)
            correct_side = BpodEvent.Port3In

        # 'led_on': the rewarded port's LED turns on and waits for the poke
        self.bpod.add_state(
            state_name="led_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                correct_side: "water_delivery",
            },
            output_actions=[light_led],
        )

        # 'water_delivery': valve opens, LED stays on
        self.bpod.add_state(
            state_name="water_delivery",
            state_timer=valvetime,
            state_change_conditions={BpodEvent.Tup: "iti"},
            output_actions=[valve_action, light_led],
        )

        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        """Work out response_side and outcome for this trial.

        Only the correct-side poke is wired to end "led_on" early (see
        create_trial); a poke on the wrong side doesn't transition anywhere
        but is still logged by Bpod, so it still counts as a valid
        (incorrect) response.
        """

        # 1. The moment the LED turned on and the animal could start responding.
        t_led_on = self.trial_data["STATE_led_on_START"][0]

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
        pass
