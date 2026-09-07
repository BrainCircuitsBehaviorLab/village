## Task Development Guide

To create a task, create a Python file inside your project's `code` directory, and
within it, a class named after the task, inheriting from the generic `TaskBase`
class. Naming conventions follow Python standards: CamelCase for class names,
lower_case for filenames and function/variable names. Let's look at an example.

### A minimal task

`village/code/bpod_1_habituation.py` is the simplest real task in this project — the
mouse is just left alone in the box, pokes are logged, no reward is given:

```python
from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class Bpod1Habituation(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = """
        Habituation Task (Bpod)
        ----------------------------------------------------------
        This task is an automatic mouse habituation to the box.
        Nothing will happen during the task, the mouse will be left alone in the box
        for the duration of the task.
        Port pokes will be registered but no reward will be delivered.
        """
```

The task is named `Bpod1Habituation`. It's initialized with `__init__`, and we
acquire all the properties of the generic `TaskBase` class using `super().__init__()`.
`self.info` is shown to the user when the task is selected in the GUI to run
manually.

Four methods must be implemented in your class: `start`, `create_trial`,
`after_trial`, and `close`.

### The `start()` method

Called once, when the task starts. Use it to compute anything the whole session
needs — valve opening times, loaded sounds, opened serial connections, etc.

```python
    def start(self):
        """In this simple task we don't need to do anything in the start method."""

        pass
```

The most commonly used attributes available by default inside any task method
(see the `TaskBase` class docstring for the full list) are:

- `self.bpod` — the Bpod interface, used inside `create_trial` to build the state
  machine.
- `self.settings` — the session's parameters, as defined in `training_protocol.py`
  (e.g. `self.settings.reward_volume`).
- `self.calibrations` — convert hardware values to real-world units, e.g.
  `self.calibrations.water_calibration.get_valve_time(port, volume)` or
  `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`.
- `self.cam_box`, `self.gpio`, `self.custom_areas` — the box camera, GPIO output
  control, and any custom-shaped detection areas the project defines.
- `self.name`, `self.subject`, `self.current_trial`, `self.system_name`, `self.date`.
- `self.trial_data` — populated automatically after each trial, available inside
  `after_trial` (see below).

A task that delivers water almost always needs a valve opening time first —
calibrate the ports from the Water Calibration panel before using this, or it
raises an exception:

```python
    def start(self):
        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )
```

### The `create_trial()` method

Called once per trial. It builds the Bpod state machine for that trial (the
machine is only sent to Bpod and actually run once `create_trial` returns).

```python
    def create_trial(self):
        """
        This task is very simple, the state machine has only one state
        called "ready_to_explore". We give it a 60-second timer and a
        timer-up condition (once the timer elapses) that takes us to "exit".
        Also, every time there's a poke in any port, we switch to the "exit" state.
        """

        self.bpod.add_state(
            state_name="ready_to_explore",
            state_timer=60,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                BpodEvent.Port1In: "exit",
                BpodEvent.Port2In: "exit",
                BpodEvent.Port3In: "exit",
            },
            output_actions=[],
        )
```

`BpodEvent` and `BpodOutput` (imported from `village.custom_classes.task_base`
alongside `TaskBase`) enumerate every Bpod input event and output action. See
[More Bpod primitives](#more-bpod-primitives) below for a full walkthrough of
`add_state`, LEDs, valves, softcodes and TTL.

### The `after_trial()` method

Called once after each trial ends, to register whatever values you want saved
to the session's data file. `self.trial_data` is populated automatically by
then — `self.trial_data.get("Port1In", [])` is the list of timestamps at which
port 1 was poked during the trial (empty if it never was), and
`self.trial_data.get("STATE_<name>_START", [])` / `"..._END"` likewise for every
Bpod state visited.

```python
    def after_trial(self):
        """
        Here we look at the trial_data dictionary that bpod records automatically
        to find out which events we got.
        """

        outcome = "miss"

        # for each portIn, we have a list of times at which pokes were registered,
        # so we check that there's an entry for that port and that it isn't empty,
        # which indicates that a poke happened.
        if self.trial_data.get("Port1In"):
            outcome = "left_poke"
        if self.trial_data.get("Port2In"):
            outcome = "center_poke"
        if self.trial_data.get("Port3In"):
            outcome = "right_poke"

        # Register the outcome of the trial and the water consumed.
        # Registering "water" (in microliters) is mandatory on every task --
        # it's how the system tracks each subject's daily water intake.
        self.register_value("outcome", outcome)
        self.register_value("water", 0)
```

### The `close()` method

Called once when the task finishes (session ends, or manually stopped). Use it
for any cleanup — closing a serial connection, sending a Slack/email summary,
generating a plot, etc.

```python
    def close(self):
        """
        We don't need to do any extra work when the task finishes.
        """

        pass
```

### A more complete example: FollowTheLight

Now let's look at a task closer to a real 2-choice discrimination protocol —
`village/code/bpod_4_center_initiated.py` and `bpod_5_introduce_penalty.py` are
the real versions of this in the project (respectively without and with a
penalty for the wrong side); this walkthrough merges both into one task that
switches behavior based on `self.settings.stage`:

- The mouse initiates each trial by poking the center port (its LED turns on).
- After the center poke, one of the two side LEDs turns on at random.
- Poking the correct side delivers a reward.
- In stage 1, poking the wrong side does nothing (the mouse can just try again).
  In stage 2, it triggers a penalty (noise + timeout) instead.
- Progression between stages is decided in `training_protocol.py`'s
  `update_training_settings`, based on performance.

```python
import random

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class FollowTheLight(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = """
        Follow The Light Task
        -------------------
        The mouse pokes the center port to start a trial. One of the two side
        ports then lights up; poking it delivers a reward. Stage 1 has no
        penalty for the wrong side, stage 2 does (see self.settings.stage).
        """

    def start(self):
        """
        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: reward volume delivered on a correct poke
        - self.settings.led_intensity: port LED brightness (0-255)
        - self.settings.c_led_on_time: time allowed to poke the center port, seconds
        - self.settings.led_on_time: time allowed to poke the correct side, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        - self.settings.stage: 1 (no penalty) or 2 (penalty for the wrong side)
        - self.settings.noise_time, self.settings.timeout: only used in stage 2
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
            correct_led = (BpodOutput.PWM1, self.settings.led_intensity)
            correct_side = BpodEvent.Port1In
            wrong_side = BpodEvent.Port3In
        else:
            valvetime = self.valve_r_time
            valve_action = BpodOutput.Valve3
            correct_led = (BpodOutput.PWM3, self.settings.led_intensity)
            correct_side = BpodEvent.Port3In
            wrong_side = BpodEvent.Port1In

        # In stage 1, a wrong poke isn't wired to any transition, so it's just
        # ignored and the mouse can try again before "side_led_on" times out.
        side_led_on_conditions = {
            BpodEvent.Tup: "exit",
            correct_side: "water_delivery",
        }
        if self.settings.stage == 2:
            side_led_on_conditions[wrong_side] = "wrong_choice"

        # 'c_led_on': center LED on, waits for the trial-initiating center poke
        self.bpod.add_state(
            state_name="c_led_on",
            state_timer=self.settings.c_led_on_time,
            state_change_conditions={
                BpodEvent.Tup: "exit",
                BpodEvent.Port2In: "side_led_on",
            },
            output_actions=[(BpodOutput.PWM2, self.settings.led_intensity)],
        )

        # 'side_led_on': only the correct side's LED turns on
        self.bpod.add_state(
            state_name="side_led_on",
            state_timer=self.settings.led_on_time,
            state_change_conditions=side_led_on_conditions,
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

        # Stage 2 only: noise, then a silent timeout, before exiting.
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

        Whichever side the animal poked first (if any) after the side LED
        turned on determines the outcome, independently of which Bpod state
        that poke happened to transition into -- this way stage 1 (where a
        wrong poke isn't wired to any transition) and stage 2 (where it goes
        to "wrong_choice") are scored the same way.
        """

        side_led_on_start = self.trial_data.get("STATE_side_led_on_START")
        if not side_led_on_start:
            # The center poke never happened -> side LED never turned on.
            self.register_value("rewarded_side", self.side)
            self.register_value("water", 0)
            self.register_value("outcome", "omission")
            self.register_value("response_side", "none")
            return

        t_side_led_on = side_led_on_start[0]

        correct_key, wrong_key = (
            ("Port1In", "Port3In") if self.side == "left" else ("Port3In", "Port1In")
        )
        correct_pokes = [
            t for t in self.trial_data.get(correct_key, []) if t >= t_side_led_on
        ]
        wrong_pokes = [
            t for t in self.trial_data.get(wrong_key, []) if t >= t_side_led_on
        ]

        if correct_pokes and (not wrong_pokes or correct_pokes[0] <= wrong_pokes[0]):
            outcome = "correct"
            response_side = self.side
            water = self.settings.reward_volume
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
```

---

### More Bpod primitives

For a runnable walkthrough of the Bpod building blocks, see two reference
tasks in this project's `code` directory (neither is a real behavioral
protocol):

- `bpod_example_outputs_and_events.py` — LEDs, a valve, poke in/out,
  softcodes in both directions, and TTL pulses in both directions.
- `bpod_example_global_timer.py` — a global timer: a deadline that ticks in
  the background across every state, independently of each state's own
  timer, until it ends or is cancelled.

Two more primitives exist beyond what those examples cover — global counters
(`self.bpod.set_global_counter(counter_number, target_event, threshold)`,
counts occurrences of an event and fires once a threshold is reached) and
conditions (`self.bpod.set_condition(condition_number, condition_channel,
channel_value)`, checks a channel's current level at the moment of a
transition rather than reacting to an edge). For both, see the official Bpod
documentation: [sanworks.github.io/Bpod_Wiki](https://sanworks.github.io/Bpod_Wiki/).
