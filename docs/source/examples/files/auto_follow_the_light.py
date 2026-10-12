import math
import random

import numpy as np
import pandas as pd
from bpod_6_delay import get_delay_probabilities

from village.custom_classes.auto_no_mouse_base import AutoNoMouseBase, AutonomouseParam
from village.scripts.time_utils import time_utils


class AutoFollowTheLight(AutoNoMouseBase):
    """A virtual animal that performs Bpod6Delay (bpod_6_delay.py) by itself,
    to test the task, the training protocol and the plots without a real
    animal. Started and stopped from the VIRTUAL MOUSE tab of the MONITOR
    screen while the task is running.

    In every trial it pokes the center port and, after its reaction time,
    pokes a side port. It has to poke the side that lit up first: the longer
    the delay between the two side LEDs, the easier it is to tell them apart,
    so the more likely it chooses right. This way its accuracy depends on the
    difficulty, as a real animal's does, and the task's adaptation of p can be
    watched at work.
    """

    # The task this virtual animal is for (the task class name). Without it,
    # it would be used for any task that has no virtual animal of its own.
    TASK_NAME = "Bpod6Delay"

    # Parameters shown in the VIRTUAL MOUSE tab, editable while it runs.
    PARAMS = [
        AutonomouseParam(
            "tau",
            float,
            0.3,
            "delay needed (s)",
            0.01,
            5.0,
            "How long a delay it needs to tell the sides apart: the larger, "
            "the more mistakes with short delays",
        ),
        AutonomouseParam(
            "reaction_time",
            float,
            0.5,
            "reaction time (s)",
            0.0,
            5.0,
            "Time from the center poke to the side poke",
        ),
        AutonomouseParam(
            "lapse",
            float,
            0.05,
            "lapse rate",
            0.0,
            1.0,
            "Probability of choosing at random, whatever the delay",
        ),
    ]

    def p_correct(self, delay: float) -> float:
        """Probability of choosing the right side for a given delay: from 0.5
        (chance) with no delay, to 1 with a long one, minus the lapses."""
        p_seen = 1 - math.exp(-delay / self.tau)
        return (1 - self.lapse) * (0.5 + 0.5 * p_seen) + self.lapse * 0.5

    def run_trial(self) -> None:
        """One trial: center poke, wait the reaction time, side poke."""
        self.wait(1.0)  # some time to reach the center port
        if self._stop_event.is_set():
            return
        self.poke(2)  # starts the trial: the first side LED turns on

        self.wait(self.reaction_time)
        if self._stop_event.is_set():
            return

        # correct_side and delay are set by the task in create_trial
        correct = random.random() < self.p_correct(self.task.delay)
        if self.task.correct_side == "left":
            port = 1 if correct else 3
        else:
            port = 3 if correct else 1
        self.poke(port)

        # Let the reward or the timeout and the ITI pass before the next trial
        self.wait(self.task.settings.timeout + self.task.settings.iti_time)

    def inject_trial(self, **kwargs) -> None:
        """Appends one simulated trial directly to the session data, without
        running the state machine, with the same columns Bpod6Delay saves.
        Useful to fill a session quickly and test the plots and the training
        protocol."""

        self.update_params(**kwargs)
        task = self.task
        settings = task.settings

        p = getattr(task, "p", getattr(settings, "p", 0.0))
        delays, probabilities = get_delay_probabilities(
            p, settings.delay_thresholds, gamma=getattr(settings, "curve_power", 3.0)
        )
        delay = float(np.random.choice(delays, p=probabilities))
        correct_side = random.choice(["left", "right"])
        correct = random.random() < self.p_correct(delay)
        response_side = (
            correct_side if correct else ("right" if correct_side == "left" else "left")
        )
        choice_port = "Port1In" if response_side == "left" else "Port3In"

        # Times of the simulated trial. The recorder must also open and close
        # the trial, so that the session's trial count stays consistent.
        t0 = time_utils.now_timestamp()
        task.recorder.start_trial(t0, t0)
        t_center = t0 + 1.0
        t_choice = t_center + self.reaction_time
        t_outcome_end = t_choice + (0.1 if correct else settings.noise_time)
        t_end = t_outcome_end + (settings.iti_time if correct else settings.timeout)
        task.recorder.end_trial(t_end)

        # the side poke happens either before or after the second LED turns on
        first_led_end = min(t_center + delay, t_choice)
        outcome_state = "correct_choice" if correct else "wrong_choice"
        after_state = "iti" if correct else "timeout"
        row: dict = {
            "date": task.date,
            "trial": task.current_trial,
            "subject": task.subject,
            "task": task.name,
            "system_name": task.system_name,
            "TRIAL_START": t0,
            "TRIAL_END": t_end,
            "STATE_c_led_on_START": [t0],
            "STATE_c_led_on_END": [t_center],
            "STATE_first_side_led_START": [t_center],
            "STATE_first_side_led_END": [first_led_end],
            f"STATE_{outcome_state}_START": [t_choice],
            f"STATE_{outcome_state}_END": [t_outcome_end],
            f"STATE_{after_state}_START": [t_outcome_end],
            f"STATE_{after_state}_END": [t_end],
            "Port2In": [t_center],
            choice_port: [t_choice],
            "ordered_list_of_events": ["Port2In", choice_port],
            # the values Bpod6Delay registers in after_trial
            "first_trial_response_time": t_choice,
            "p": p,
            "water": settings.reward_volume if correct else 0,
            "outcome": "correct" if correct else "incorrect",
            "response_side": response_side,
            "rewarded_side": correct_side,
            "delay_cues": -delay if correct_side == "left" else delay,
        }
        if t_center + delay < t_choice:
            row["STATE_both_side_leds_START"] = [t_center + delay]
            row["STATE_both_side_leds_END"] = [t_choice]

        task.session_df = pd.concat(
            [task.session_df, pd.DataFrame([row])], ignore_index=True
        )
        task.current_trial += 1
