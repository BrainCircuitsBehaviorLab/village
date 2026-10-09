from village.custom_classes.training_protocol_base import TrainingProtocolBase


class TrainingProtocol(TrainingProtocolBase):
    """Moves each subject through the 6 Bpod training stages, one after another:
    Bpod1Habituation -> Bpod2Passive -> Bpod3Active -> Bpod4CenterInitiated ->
    Bpod5IntroducePenalty -> Bpod6Delay (bpod_1_habituation.py ..
    bpod_6_delay.py).

    A practically identical protocol works for the Arduino versions of the
    same tasks (arduino_1_habituation.py .. arduino_6_delay.py): they read the
    same settings and register the same values, so it is enough to change the
    task names (Arduino1Habituation, Arduino2Passive...).

    The other example tasks (bpod_example_*.py, bpod_purge_ports.py,
    bpod_area2_sound.py, bpod_touchscreen.py, raspberry_*.py) are not part of
    the progression: they are run manually, and this protocol leaves next_task
    alone after them.
    """

    def __init__(self) -> None:
        super().__init__()

    def default_training_settings(self) -> None:
        """Called once, when a new subject is created. These are the settings of
        the first stage; update_training_settings changes some of them when the
        subject moves to the next stage.

        Required parameters:
        - next_task, refractory_period, minimum_duration, maximum_duration.

        Task-specific parameters (read by bpod_1..6):
        - reward_volume / reward_volume_large: normal and occasional-large
          reward volumes, in microliters.
        - led_intensity: port LED brightness (0-255).
        - led_on_time / c_led_on_time: max duration of the side/center LED
          response windows, seconds.
        - iti_time: inter-trial interval, seconds.
        - timeout: punishment timeout after an incorrect response
          (introduce_penalty and delay), seconds.
        - noise_time: white-noise punishment duration (introduce_penalty and
          delay), seconds.
        - p: difficulty of the delay task (0-1), carried over from session to
          session (see update_training_settings).
        - delay_thresholds: possible delays between the two side LEDs (seconds;
          the longer, the easier) and, for each one, the p from which it
          starts to appear.
        - curve_power: how strictly the harder delays are held back while p is
          below their threshold.

        Not part of the progression, but read by bpod_touchscreen.py, which
        is run manually:
        - long_duration / short_duration: how long each of the two
          rectangles stays on screen, seconds.
        """

        # Required parameters
        self.settings.next_task = "Bpod1Habituation"
        self.settings.refractory_period = 4 * 60 * 60  # 4 hours between sessions
        self.settings.minimum_duration = 10 * 60
        self.settings.maximum_duration = 15 * 60  # habituation lasts 15 min

        # Task-specific parameters (for bpod_1..6 or arduino 1..6, read the respective
        # task code to understand their usage)
        self.settings.reward_volume = 2  # microliters
        self.settings.reward_volume_large = 6  # microliters
        self.settings.led_intensity = 255  # 0-255
        self.settings.led_on_time = 5 * 60  # seconds
        self.settings.c_led_on_time = 5 * 60  # seconds
        self.settings.iti_time = 1  # seconds
        self.settings.timeout = 5  # seconds
        self.settings.noise_time = 1.5  # seconds
        self.settings.p = 0.0
        self.settings.curve_power = 3
        self.settings.delay_thresholds = {
            0: 0.75,
            0.1: 0.65,
            0.25: 0.50,
            0.5: 0.25,
            1: 0.001,
            40: 0.0,
        }

        # Task-specific parameters for other tasks (e.g., bpod_touchscreen.py)
        self.settings.long_duration = 5  # seconds
        self.settings.short_duration = 2  # seconds

    def update_training_settings(self) -> None:
        """Called every time a session finishes. Decides the next task (and
        changes some settings when the subject moves to the next stage).

        self.df is per-trial (one row per trial across every session this
        subject has ever run, see TaskBase.subject_df), so sessions are told
        apart by the "session" column.
        """

        if self.last_task == "Bpod1Habituation":
            # If the session we just completed is habituation, move to the next task.
            self.settings.next_task = "Bpod2Passive"
            self.settings.minimum_duration = 25 * 60
            self.settings.maximum_duration = 45 * 60

        elif self.last_task == "Bpod2Passive":
            # At least 2 passive sessions, and 100 trials in the last two.
            df2 = self.df[self.df["task"] == "Bpod2Passive"]
            n_sessions = len(df2["session"].unique())
            last_2_sessions = df2["session"].unique()[-2:]
            df2_last_2 = df2[df2["session"].isin(last_2_sessions)]
            trials_last_2_sessions = df2_last_2.shape[0]

            if n_sessions >= 2 and trials_last_2_sessions >= 100:
                self.settings.next_task = "Bpod3Active"
                self.settings.minimum_duration = 25 * 60
                self.settings.maximum_duration = 45 * 60

        elif self.last_task == "Bpod3Active":
            # At least 2 active sessions, and in the last two: 100 trials and
            # 70% of them correct.
            df3 = self.df[self.df["task"] == "Bpod3Active"]
            n_sessions = len(df3["session"].unique())
            last_2_sessions = df3["session"].unique()[-2:]
            df3_last_2 = df3[df3["session"].isin(last_2_sessions)]
            trials_last_2_sessions = df3_last_2.shape[0]
            correct_last_2_sessions = (df3_last_2["outcome"] == "correct").mean()

            if (
                n_sessions >= 2
                and trials_last_2_sessions >= 100
                and correct_last_2_sessions >= 0.70
            ):
                self.settings.next_task = "Bpod4CenterInitiated"
                self.settings.minimum_duration = 30 * 60
                self.settings.maximum_duration = 45 * 60

        elif self.last_task == "Bpod4CenterInitiated":
            # At least 2 center-initiated sessions, and in the last two: 200
            # trials and 70% of them correct.
            df4 = self.df[self.df["task"] == "Bpod4CenterInitiated"]
            n_sessions = len(df4["session"].unique())
            last_2_sessions = df4["session"].unique()[-2:]
            df4_last_2 = df4[df4["session"].isin(last_2_sessions)]
            trials_last_2_sessions = df4_last_2.shape[0]
            correct_last_2_sessions = (df4_last_2["outcome"] == "correct").mean()

            if (
                n_sessions >= 2
                and trials_last_2_sessions >= 200
                and correct_last_2_sessions >= 0.70
            ):
                self.settings.next_task = "Bpod5IntroducePenalty"
                self.settings.minimum_duration = 30 * 60
                self.settings.maximum_duration = 45 * 60
                self.settings.timeout = 5
                self.settings.noise_time = 3

        elif self.last_task == "Bpod5IntroducePenalty":
            # At least 2 introduce-penalty sessions, and in the last two: 200
            # trials and 70% of them correct.
            df5 = self.df[self.df["task"] == "Bpod5IntroducePenalty"]
            n_sessions = len(df5["session"].unique())
            last_2_sessions = df5["session"].unique()[-2:]
            df5_last_2 = df5[df5["session"].isin(last_2_sessions)]
            trials_last_2_sessions = df5_last_2.shape[0]
            correct_last_2_sessions = (df5_last_2["outcome"] == "correct").mean()

            if (
                n_sessions >= 2
                and trials_last_2_sessions >= 200
                and correct_last_2_sessions >= 0.70
            ):
                self.settings.next_task = "Bpod6Delay"
                self.settings.minimum_duration = 45 * 60
                self.settings.maximum_duration = 60 * 60
                self.settings.timeout = 5
                self.settings.p = 0.0
                self.settings.curve_power = 3

        elif self.last_task == "Bpod6Delay":
            # Last stage: the subject stays here. The next session starts from
            # the difficulty p reached in this one, minus 0.05.
            last_session = self.df["session"].max()
            df_last_session = self.df[self.df["session"] == last_session]
            p_values = df_last_session["p"].dropna()
            if len(p_values) > 0:
                p_next = max(float(p_values.iloc[-1]) - 0.05, 0.0)
                self.settings.p = round(p_next, 2)

        # Any other task was run manually: next_task is left as it was.

    def define_gui_tabs(self) -> None:
        self.gui_tabs = {
            "Reward": [
                "reward_volume",
                "reward_volume_large",
            ],
            "Timing": [
                "led_intensity",
                "led_on_time",
                "c_led_on_time",
                "iti_time",
                "timeout",
                "noise_time",
            ],
            "Delay task (stage 6)": [
                "p",
                "curve_power",
                "delay_thresholds",
            ],
            "Touchscreen demo": [
                "long_duration",
                "short_duration",
            ],
        }
        self.gui_tabs_restricted = {}
