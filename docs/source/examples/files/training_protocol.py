from village.custom_classes.training_protocol_base import TrainingProtocolBase

# Stage number -> task-name suffix, shared by both families (BpodNXxx /
# ArduinoNXxx name the exact same stage the exact same way).
STAGE_NAMES = {
    1: "Habituation",
    2: "Passive",
    3: "Active",
    4: "CenterInitiated",
    5: "IntroducePenalty",
    6: "Delay",
}
LAST_STAGE = max(STAGE_NAMES)


class TrainingProtocol(TrainingProtocolBase):
    """Drives the 6-stage progression shared by the Bpod and Arduino task
    families (bpod_1_habituation.py .. bpod_6_delay.py and their
    arduino_1_habituation.py .. arduino_6_delay.py twins).

    Both families read the exact same settings, use the exact same stage
    numbering/names, and register the exact same after_trial() values
    (outcome, water, response_side, ...) -- so one training protocol works
    for either, without needing to know which one is actually running.
    Whichever family next_task currently names (see default_training_settings
    below) is the one that keeps running: update_training_settings only
    ever advances the stage number, never switches family on its own.

    The reference/demo tasks in this project (bpod_example_*.py,
    bpod_purge_ports.py, bpod_area2_sound.py, bpod_touchscreen.py,
    raspberry_area1_sound.py, raspberry_touchscreen.py) aren't part of this
    progression -- they're meant to be selected and run manually, and this
    protocol leaves next_task alone whenever last_task isn't one of the 12
    stage tasks.
    """

    def __init__(self) -> None:
        super().__init__()

    def default_training_settings(self) -> None:
        """Called once, when a new subject is created.

        Required parameters:
        - next_task, refractory_period, minimum_duration, maximum_duration.

        Task-specific parameters (read across bpod_1..6 / arduino_1..6):
        - reward_volume / reward_volume_large: normal and occasional-large
          reward volumes, in microliters.
        - led_intensity: side port LED brightness (0-255), used by the
          Bpod tasks (the Arduino ones drive their LEDs directly).
        - led_on_time / c_led_on_time: max duration of the side/center LED
          response windows, seconds.
        - iti_time: inter-trial interval, seconds.
        - timeout: punishment timeout after an incorrect response
          (introduce_penalty), seconds.
        - noise_time: white-noise punishment duration (introduce_penalty),
          seconds.
        - p / curve_power: delay-task (6) psychometric parameters -- p is
          the probability of the harder (longer-delay) trial types,
          curve_power shapes how per-delay difficulty scales with p.
        - N_trials: soft cap on trials per session for the delay task.
        - trials_to_advance: minimum trials in the last session of a stage
          before update_training_settings promotes the subject to the next
          one (see below).

        Not part of the 1-6 progression, but read by the reference tasks in
        this project that get selected and run manually rather than chained
        by update_training_settings:
        - long_duration / short_duration: how long each of the two
          rectangles stays on screen in bpod_touchscreen.py, seconds.
        """

        # Required parameters
        self.settings.next_task = "Bpod1Habituation"
        self.settings.refractory_period = 3600 * 4  # 4 hours between sessions
        self.settings.minimum_duration = 600  # 10 min minimum session length
        self.settings.maximum_duration = 2700  # 45 min maximum session length

        # Task-specific parameters
        self.settings.reward_volume = 3  # microliters
        self.settings.reward_volume_large = 6  # microliters
        self.settings.led_intensity = 255  # 0-255
        self.settings.led_on_time = 10  # seconds
        self.settings.c_led_on_time = 10  # seconds
        self.settings.iti_time = 2  # seconds
        self.settings.timeout = 5  # seconds
        self.settings.noise_time = 1.5  # seconds
        self.settings.p = 0.0
        self.settings.curve_power = 3
        self.settings.N_trials = 1000

        # Progression
        self.settings.trials_to_advance = 50

        # bpod_touchscreen.py only
        self.settings.long_duration = 5  # seconds
        self.settings.short_duration = 2  # seconds

    def _current_stage(self) -> tuple[str, int] | None:
        """Splits self.last_task into (family, stage), e.g.
        ("Bpod", 3) from "Bpod3Active" -- or None if it isn't one of the 12
        stage task names (a fresh subject, or a reference/demo task was run
        manually), in which case next_task is left untouched.
        """

        for family in ("Bpod", "Arduino"):
            if not self.last_task.startswith(family):
                continue
            rest = self.last_task[len(family) :]
            for stage, name in STAGE_NAMES.items():
                if rest == f"{stage}{name}":
                    return family, stage
        return None

    def update_training_settings(self) -> None:
        """Called every time a session finishes. Advances one stage, in the
        same family, once the last session of the current stage reached
        trials_to_advance trials -- otherwise repeats the same stage.
        Stays on the last stage once reached.

        self.df is per-trial (one row per trial across every session this
        subject has ever run, see TaskBase.subject_df), so "trials in the
        last session" is however many of this task's rows share the most
        recent session number -- not simply the last row's trial number.
        """

        current = self._current_stage()
        if current is None:
            return

        family, stage = current
        df_task = self.df[self.df["task"] == self.last_task]
        if len(df_task) == 0:
            return
        last_session = df_task["session"].iloc[-1]
        trials_last_session = (df_task["session"] == last_session).sum()

        if (
            stage < LAST_STAGE
            and trials_last_session >= self.settings.trials_to_advance
        ):
            stage += 1
        self.settings.next_task = f"{family}{stage}{STAGE_NAMES[stage]}"

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
                "N_trials",
            ],
            "Progression": [
                "trials_to_advance",
            ],
            "Touchscreen demo": [
                "long_duration",
                "short_duration",
            ],
        }
        self.gui_tabs_restricted = {}
