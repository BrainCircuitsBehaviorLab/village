import random

import numpy as np
import pandas as pd

from village.custom_classes.auto_no_mouse_base import AutoNoMouseBase, AutonomouseParam
from village.scripts.time_utils import time_utils


class AutoFollowTheLight(AutoNoMouseBase):
    # TASK_NAME = "S5"  # Task it is designed for

    # # Custom parameters for this Autonomouse, that will appear in the UI.
    # PARAMS = [AutonomouseParam(name="p_correct", type_=float,
    #                            default=0.80, label="p correct",
    #                            min_val=0.0, max_val=1.0,
    #                            tooltip="Prob choosing the correct port")]
    TASK_NAME = "S5"  # Task it is designed for

    # Custom parameters for this Autonomouse, that will appear in the UI.
    PARAMS = [
        AutonomouseParam("k_decay", float, 2.0, "memory decay", 0.1, 10.0),
        AutonomouseParam("noise", float, 0.5, "decision noise", 0.0, 2.0),
    ]

    def run_trial(self) -> None:
        """
        Run a trial, what you want the autonomouse to do on each trial.
        Here, it will poke centre, wait, then choose the side port and poke.
        """
        """
        DO THE TASK PERFECTLY:
        """

        #  # 1. center poke
        # self.wait(1)
        # self.poke(2)
        # self.wait(1)

        # # 2. WAIT until cue period (you don't know side yet!)
        # self.wait(0.1)

        # # 3. READ TRUE cue
        # first_side = self.task.first_side
        # print('***First side:', first_side)
        # # fallback safety
        # if first_side is None:
        #     return

        # # 4. respect delay (optional realism)
        # delay = self.task.delay
        # # print('***Delay:', delay)
        # # self.wait(delay)

        # # 5. correct choice
        # if first_side == 0:
        #     self.poke(1)
        # else:
        #     self.poke(3)

        """
        ADD NOISE AND MEMORY DECAY::
        """
        self.wait(1)
        self.poke(2)
        self.wait(1)

        first_side = self.task.first_side
        delay = self.task.delay

        # encode as -1 / +1
        s = -1 if first_side == 0 else +1

        # memory decay
        m = s * np.exp(-self.k_decay * delay)

        # noise
        m += np.random.normal(0, self.noise)

        # decision
        port = 3 if m > 0 else 1

        self.poke(port)

        if self._stop_event.is_set():
            return

        """
        FOLLOW THE LIGHT:
        """
        # # Wait a bit
        # self.wait(.5)

        # # Poke in the middle to initiate the trial then wait a bit
        # self.poke(2)
        # self.wait(.5)

        # # Choose a side and poke
        # trial_type = getattr(self.task, "this_trial_type", "left")
        # if random.random() < self.p_correct:
        #     port = 1 if trial_type == "left" else 3
        # else:
        #     port = 3 if trial_type == "left" else 1
        # self.poke(port)

        # if self._stop_event.is_set():
        #     return

    def inject_trial(self, **kwargs) -> None:
        """Append one mock trial directly to task.session_df."""

        # Update parameters if provided
        for param in self.PARAMS:
            if param.name in kwargs:
                setattr(self, param.name, param.clamp(kwargs[param.name]))

        # define if trials is correct or not based on p_correct
        task = self.task
        trial_type = random.choice(["left", "right"])
        correct = random.random() < self.p_correct
        if correct:
            choice_port = "Port1In" if trial_type == "left" else "Port3In"
        else:
            choice_port = "Port3In" if trial_type == "left" else "Port1In"

        # Set timing of trial, e.g. how long the mouse takes to poke after
        # stimulus, how long the outcome lasts, etc. We also need to call
        # the recorder so trial is created in session_df.
        t0 = time_utils.now_timestamp()
        task.recorder.start_trial(t0, t0)

        t_init = t0 + 0.25
        t_choice = t_init + 0.25
        t_iti = t_choice + 1
        t_end = t_iti + 1

        task.recorder.end_trial(t_end)

        # Construct the mock trial row to append to session_df.
        row: dict = {
            # Task information
            "date": task.date,
            "trial": task.current_trial,
            "subject": task.subject,
            "task": task.name,
            "system_name": task.system_name,
            # Trial events and timings
            "TRIAL_START": t0,
            "TRIAL_END": t_end,
            "Port2In": [t_init],
            "Port2Out": [t_init + 0.05],
            choice_port: [t_choice],
            "ordered_list_of_events": ["Port2In", "Port2Out", choice_port],
            "STATE_ready_to_initiate_START": [t0],
            "STATE_ready_to_initiate_END": [t_init],
            "STATE_stimulus_state_START": [t_init],
            "STATE_stimulus_state_END": [t_choice],
            "STATE_reward_state_START": [t_choice] if correct else [],
            "STATE_reward_state_END": ([t_choice + 1] if correct else []),
            "STATE_punish_state_START": [] if correct else [t_choice],
            "STATE_punish_state_END": ([] if correct else [t_choice + 1]),
            "STATE_iti_state_START": [t_iti],
            "STATE_iti_state_END": [t_end],
            # Outcome and trial type (what's logged in Task.after_trial)
            "water": task.settings.reward_amount_ml if correct else 0,
            "trial_type": trial_type,
            "correct": correct,
        }

        # Write in df and update trial number.
        task.session_df = pd.concat(
            [task.session_df, pd.DataFrame([row])], ignore_index=True
        )
        task.current_trial += 1
