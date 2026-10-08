import random

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class Bpod2Passive(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Passive learning, Water Delivery Task (Bpod)
        ----------------------------------------------------------------
        It's designed to habituate the mice to the LEDs and to the ports.
        the reward is already delivered at the moment of the lick, Passive
        learning.
        - Each trial starts with:
            * one reward valve opens (water is delivered)
            * the corresponding LED turns on
        - The LED remains ON until:
            * A poke is detected in the "correct" port
            * Or a time-up occurs
        If the animal pokes in the wrong port nothing will happen, the mice
        will remain in the same state until pokes in the "correct" port.
        """

    def start(self):
        """Use the calibration to get the valve opening times (in seconds) for
        ports 1 (left) and 3 (right), so they deliver the water volume defined
        in settings.reward_volume.

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: reward volume delivered each trial
        - self.settings.led_intensity: side port LED brightness (0-255)
        - self.settings.led_on_time: max duration of the "led_on" state, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        """

        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )

        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )

    def create_trial(self):
        self.side = random.choice(["left", "right"])

        if self.side == "left":
            valvetime = self.valve_l_time
            valve_action = BpodOutput.Valve1
            light_LED = (BpodOutput.PWM1, self.settings.led_intensity)
            correct_side = BpodEvent.Port1In
        else:
            valvetime = self.valve_r_time
            valve_action = BpodOutput.Valve3
            light_LED = (BpodOutput.PWM3, self.settings.led_intensity)
            correct_side = BpodEvent.Port3In

        self.bpod.add_state(
            state_name="water_delivery",
            state_timer=valvetime,
            state_change_conditions={BpodEvent.Tup: "led_on"},
            output_actions=[light_LED, valve_action],
        )

        self.bpod.add_state(
            state_name="led_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions={BpodEvent.Tup: "exit", correct_side: "iti"},
            output_actions=[light_LED],
        )

        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        """Work out chosen_side and outcome for this trial.

        A poke on the wrong side does not end the "led_on" state early (see
        create_trial), but it's still logged by Bpod -- so a poke there is
        still a valid (incorrect) response, not nothing happening.
        """

        # 1. Water delivery always ends and moves to "led_on" via Tup (see
        # create_trial), so this is the moment the LED actually turned on.
        t_led_on = self.trial_data["STATE_led_on_START"][0]

        # 2. All the pokes registered on each port during the whole trial.
        left_pokes = self.trial_data.get("Port1In", [])
        right_pokes = self.trial_data.get("Port3In", [])

        # 3. Keep only the pokes that happened after the LED turned on --
        # anything earlier happened during "water_delivery" and doesn't count.
        left_pokes = [t for t in left_pokes if t >= t_led_on]
        right_pokes = [t for t in right_pokes if t >= t_led_on]

        # 4. Whichever side got poked first, if any.
        if left_pokes and (not right_pokes or left_pokes[0] < right_pokes[0]):
            chosen_side = "left"
        elif right_pokes:
            chosen_side = "right"
        else:
            chosen_side = "none"

        # 5. No poke -> miss. Otherwise, correct if it matches the rewarded side.
        if chosen_side == "none":
            outcome = "miss"
        else:
            outcome = "correct" if chosen_side == self.side else "incorrect"

        self.register_value("rewarded_side", self.side)
        self.register_value("water", self.settings.reward_volume)
        self.register_value("outcome", outcome)
        self.register_value("response_side", chosen_side)

    def close(self):
        pass
