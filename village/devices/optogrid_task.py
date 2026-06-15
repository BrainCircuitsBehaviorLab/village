import random
import time

import numpy as np
from BpodPorts import BpodPorts
from utils_functions import get_delay_probabilities

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
from village.devices.optogrid import OptoGrid, OptoSetting
from village.scripts.log import log


class S5OptoGrid(TaskBase):
    """
    S5 OptoGrid
    """

    def __init__(self):
        super().__init__()
        self.info = """
    S5OptoGrid: Delayed Side-Cue Discrimination Task, easy version
    ---------------------------------------------------------------------------------------
    · Middle port LED turns ON until the animal pokes the middle port.
    · Middle LED turns OFF. After 100 ms:
        - One lateral port LED (L/R, random) turns ON.
        - After a random delay (250–500 ms), the opposite lateral LED turns ON.
    · The animal has 40 s to respond (Correct choice: poke the side illuminated first:
        - Correct response:
            Side LEDs OFF
            Reward delivered at middle port
            ITI (1s)
        - Incorrect response:
            Side LEDs OFF
            Buzzer noise (3s)
            3s timeout
        - No response:
            Trial aborted
            Restart task sequence
    ---------------------------------------------------------------------------------------
    Task Variables:
    DELAY DISTRIBUTION = [0.0, 0.5]
    """

    def start(self):

        # Turn on NeuroLux
        self.bpod.manual_override_output("BNC" + str(2) + "High")
        time.sleep(1)  # wait for the device to be powered up

        # Connect to OptoGrid at session start
        if self.settings.opto_sess == 1:
            self.current_opto_setting = OptoSetting()
            self.og = OptoGrid(
                device_name=self.settings.optogrid_device_name,
                sessions_directory=self.sessions_directory,
                filename=self.filename,
            )
            self.og.start()
            success = self.og.connect()
            if not success:
                log.alarm(
                    "Could not connect to OptoGrid. Check connection and device name."
                )
                self.settings.opto_sess = 0
            else:
                self.og.start_imu_logging()

        # counters
        self.trial_count = 0
        self.reward_drunk = 0
        self.correct_history = []
        self.running_accuracy = []
        self.adaptation_window = []

        self.iti_time = self.settings.iti_time
        self.timeout = self.settings.timeout
        self.noise_time = self.settings.noise_time
        self.p = getattr(self.settings, "p", 0.0)
        self.percentage_trials = getattr(self.settings, "percentage_trials", 100)
        self.start_opto_trial = getattr(self.settings, "start_opto_trial", 0)
        self.ports = BpodPorts(
            nbox=self.system_name,
            water_calibration=self.calibrations.bpod_water_calibration,
            sound_calibration=self.calibrations.sound_calibration,
            settings=self.settings,
        )

        # Generate the vector with the first-cued side
        self.first_led_side_vec = np.random.choice(
            [0, 1], size=int(self.settings.N_trials)
        )

    def create_trial(self):
        # if self.current_trial == 0:
        #     self.p = self.settings.p

        # current_trial starts at 1 we want to start at 0
        self.first_side = self.first_led_side_vec[self.current_trial - 1]
        curve_power = getattr(self.settings, "curve_power", 2.0)
        delay_values, delay_probs = get_delay_probabilities(p=self.p, gamma=curve_power)

        self.delay = np.random.choice(delay_values, p=delay_probs)
        if self.first_side == 0:  # left
            self.signed_delay = -1 * self.delay
        else:
            self.signed_delay = +1 * self.delay

        if self.first_side == 0:  # left
            self.correct_side = "left"
            self.correct_poke = self.ports.left_poke
            self.wrong_poke = self.ports.right_poke
            self.valvetime = self.ports.valve_l_time
            self.valve_action = self.ports.valve_l_reward
            self.first_led = self.ports.LED_l_on

        else:  # right
            self.correct_side = "right"
            self.correct_poke = self.ports.right_poke
            self.wrong_poke = self.ports.left_poke
            self.valvetime = self.ports.valve_r_time
            self.valve_action = self.ports.valve_r_reward
            self.first_led = self.ports.LED_r_on

        # Decide if this trial is an opto trial
        if self.current_trial > self.start_opto_trial:
            self.is_opto_trial = True

        else:
            self.is_opto_trial = False

        # OptoGrid Trial-wise configuration
        if self.settings.opto_sess == 1:
            print("This is Opto Session")
            if self.is_opto_trial:
                print("This is an Opto Trial")
                # Step 1: Check connection
                battery_val = self.og.read_battery_mv()
                print(f"OptoGrid voltage: {battery_val} mV")
                if battery_val is None:
                    print("Warning: OptoGrid not connected")
                    print("Attempting to reconnect...")
                    reconnect_success = self.og.connect()
                    if not reconnect_success:
                        print("Warning: Reconnect failed, turning off opto session")
                        self.settings.opto_sess = 0
                        self.is_opto_trial = False
                        log.alarm("Turning off opto trial and sess")
                    else:
                        self.og.start_imu_logging()

                # Step 2: If connected, program this trail's opto settings
                if self.settings.opto_sess == 1 and self.is_opto_trial:
                    print("Programming OptoGrid for this trial...")
                    self.current_opto_setting = OptoSetting(
                        sequence_length=int(self.settings.opto_sequence_length),
                        led_selection=int(
                            random.choice(self.settings.opto_led_selection)
                        ),
                        duration=int(random.choice(self.settings.opto_duration)),
                        period=int(random.choice(self.settings.opto_period)),
                        pulse_width=int(random.choice(self.settings.opto_pulse_width)),
                        amplitude=int(random.choice(self.settings.opto_amplitude)),
                        pwm_frequency=int(
                            random.choice(self.settings.opto_pwm_frequency)
                        ),
                        ramp_up=int(random.choice(self.settings.opto_ramp_up)),
                        ramp_down=int(random.choice(self.settings.opto_ramp_down)),
                    )

                    _ = self.og.program(self.current_opto_setting)

        opto_output = BpodOutput.SoftCode3 if self.is_opto_trial else ""

        print(opto_output)
        #### CREATING STATE MACHINE, ADDING STATES, SENDING AND RUNNING ####

        print("")
        print("Trial: " + str(self.current_trial))
        print("Reward side: " + str(self.correct_side))
        print("First_side: ", self.first_side)
        print("Delay: ", self.delay)
        print("Opto trial: ", self.is_opto_trial)

        # --------------------------------------------------
        # CENTER LED STATE
        # --------------------------------------------------
        self.bpod.add_state(
            state_name="c_led_on",
            state_timer=0,
            state_change_conditions={self.ports.center_poke: "opto_onset"},
            output_actions=[self.ports.LED_c_on, BpodOutput.BNC1Low],
        )

        # --------------------------------------------------
        # ONLY ONE SIDE LED ON
        # lasts for random delay
        # --------------------------------------------------
        self.bpod.add_state(
            state_name="opto_onset",
            state_timer=0.05,
            state_change_conditions={
                BpodEvent.Tup: "first_side_led",
            },
            output_actions=[opto_output],
        )

        self.bpod.add_state(
            state_name="first_side_led",
            state_timer=self.delay,
            state_change_conditions={
                self.correct_poke: "correct_choice",
                self.wrong_poke: "wrong_choice",
                BpodEvent.Tup: "both_side_leds",
            },
            output_actions=[self.first_led],
        )

        # --------------------------------------------------
        # BOTH SIDE LEDs ON
        # lasts max 40 s or until poke
        # --------------------------------------------------

        self.bpod.add_state(
            state_name="both_side_leds",
            state_timer=(40),
            state_change_conditions={
                self.correct_poke: "correct_choice",
                self.wrong_poke: "wrong_choice",
                BpodEvent.Tup: "exit",  # no response -> restart trial
            },
            output_actions=[self.ports.LED_l_on, self.ports.LED_r_on],
        )

        # --------------------------------------------------
        # CORRECT TRIAL: REWARD
        # --------------------------------------------------
        self.bpod.add_state(
            state_name="correct_choice",
            state_timer=self.valvetime,
            state_change_conditions={BpodEvent.Tup: "iti"},
            output_actions=[self.valve_action],
        )

        self.bpod.add_state(
            state_name="iti",
            state_timer=self.iti_time,
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

        # --------------------------------------------------
        # INCORRECT TRIAL: NO REWARD, NOISE CUE
        # --------------------------------------------------
        self.bpod.add_state(
            state_name="wrong_choice",
            state_timer=self.noise_time,
            state_change_conditions={BpodEvent.Tup: "timeout"},
            output_actions=[BpodOutput.SoftCode2],
        )

        self.bpod.add_state(
            state_name="timeout",
            state_timer=(self.timeout - self.noise_time),  # 3s of noise = 10s time-out
            state_change_conditions={BpodEvent.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self):
        self.trial_count += 1

        def _event_key(ev):
            return ev.name if hasattr(ev, "name") else str(ev)

        def _first_choice_after(t0, left_key, right_key):
            L = [t for t in self.trial_data.get(left_key, []) if t >= t0]
            R = [t for t in self.trial_data.get(right_key, []) if t >= t0]

            tL = L[0] if len(L) > 0 else None
            tR = R[0] if len(R) > 0 else None

            if tL is None and tR is None:
                return None, None
            if tL is None:
                return "right", tR
            if tR is None:
                return "left", tL

            return ("left", tL) if tL <= tR else ("right", tR)

        # -----------------------------
        # FIND FIRST LED STATE TIME
        # -----------------------------
        # Your actual first decision state is:
        t0_key = "STATE_first_side_led_START"
        t0 = None

        if t0_key in self.trial_data and len(self.trial_data[t0_key]) > 0:
            t0 = self.trial_data[t0_key][0]

        left_key = _event_key(self.ports.left_poke)
        right_key = _event_key(self.ports.right_poke)

        # Find first poke after both LEDs are ON
        if t0 is not None:
            first_resp, t_choice = _first_choice_after(t0, left_key, right_key)
        else:
            first_resp, t_choice = None, None

        # CORRECT SIDE (from task)
        rewarded_side = self.correct_side  # "left" or "right"

        # OUTCOME LOGIC
        if first_resp is None:  # no response
            chosen_side = "none"
            outcome = "miss"
            correct = 0
        else:
            chosen_side = first_resp
            correct = int(chosen_side == rewarded_side)
            outcome = "correct" if correct else "incorrect"

        # RUNNING ACCURACY
        # Full-session history
        self.correct_history.append(correct)

        # Adaptive window history
        self.adaptation_window.append(correct)
        window = 20
        recent_trials = self.correct_history[-window:]
        running_acc = np.mean(recent_trials)
        self.running_accuracy.append(running_acc)
        self.register_value("running_accuracy", running_acc)
        print(f"Running accuracy ({len(recent_trials)} trials): {running_acc:.2f}")

        # ADAPTIVE DIFFICULTY
        if len(self.adaptation_window) >= window:
            recent_window = self.adaptation_window[-window:]
            window_acc = np.mean(recent_window)
            print(f"Adaptive window accuracy: {window_acc:.2f}")

            # ----------------------------
            # Increase difficulty
            # ----------------------------
            if window_acc > 0.75:
                self.p += 0.05
                self.p = min(self.p, 1.0)
                print("Increasing difficulty.")
                print(f"New p value: {self.p:.2f}")
                # RESET WINDOW
                self.adaptation_window = []

            # ----------------------------
            # Decrease difficulty
            # ----------------------------
            elif window_acc < 0.15:
                self.p -= 0.05
                self.p = max(self.p, 0.0)
                print("Decreasing difficulty.")
                print(f"New p value: {self.p:.2f}")

                # RESET WINDOW
                self.adaptation_window = []

        # Save current p
        self.register_value("p", self.p)

        water = self.settings.volume if outcome == "correct" else 0
        self.reward_drunk += water
        # register the amount of water given to the mouse in this trial
        # do not delete this variable, it is used to calculate the water consumption
        # and trigger alarms. You can override the alarms in the GUI

        # -----------------------------
        # REGISTER
        # -----------------------------
        if t_choice is not None:
            self.register_value("first_trial_response_time", t_choice)

        self.register_value("water", water)
        self.register_value("outcome", outcome)
        self.register_value("response_side", chosen_side)
        self.register_value("rewarded_side", rewarded_side)
        self.register_value("delay_cues", self.signed_delay)

        # #SAVE OPTO PARAMETERS
        if self.settings.opto_sess == 1:
            self.register_value("is_opto_trial", self.is_opto_trial)
            opto = self.current_opto_setting
            self.register_value("opto_sequence_length", opto.sequence_length)
            self.register_value("opto_led_selection", opto.led_selection)
            self.register_value("opto_duration", opto.duration)
            self.register_value("opto_period", opto.period)
            self.register_value("opto_pulse_width", opto.pulse_width)
            self.register_value("opto_amplitude", opto.amplitude)
            self.register_value("opto_pwm_frequency", opto.pwm_frequency)
            self.register_value("opto_ramp_up", opto.ramp_up)
            self.register_value("opto_ramp_down", opto.ramp_down)
            self.register_value("battery_end", self.og.read_battery_mv())
            self.register_value("uled_check", self.og.read_uled_check())
            self.register_value("last_stim_time", self.og.read_last_stim_ms())

        print("registration")
        print(f"Rewarded side: {rewarded_side}")
        print(f"Response side: {first_resp}")
        print(f"Outcome: {outcome}")
        print(f"P value: {self.p:.2f}")
        print(f"Delay cues: {self.signed_delay}")
        print("")

    def close(self):
        # Turn off NeuroLux
        self.bpod.manual_override_output("BNC" + str(2) + "Low")
        # Turn off optogrid if connected
        if getattr(self, "og", None) is not None:
            self.og.stop()
