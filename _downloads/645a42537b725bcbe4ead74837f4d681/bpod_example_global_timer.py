import math

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class BpodExampleGlobalTimer(TaskBase):
    """Reference task: a minimal demo of Bpod's global timer -- a deadline
    that ticks in the background across every state that follows, until it
    ends or is cancelled (GlobalTimer1Cancel), independently of each state's
    own timer. See bpod_example_outputs_and_events.py for the rest of the
    Bpod primitives (LEDs, valve, pokes, softcodes, TTL).

    Two more primitives exist but aren't demonstrated here: global counters
    (self.bpod.set_global_counter -- counts occurrences of an event and
    fires once a threshold is reached) and conditions (self.bpod.set_condition
    -- branches on a channel's current level, rather than reacting to an
    edge like Port1In/Port1Out do). For both, see the official Bpod
    documentation: https://sanworks.github.io/Bpod_Wiki/
    """

    def __init__(self):
        super().__init__()

        self.info = """
        Bpod Example: Global Timer
        ----------------------------------------------------------------
        Not a real task -- a minimal demo of the global timer primitive:
        1. Trigger a 10s global timer at the very start of the trial.
        2. Wait for either a poke in port 1, or the timer ending -- whichever
           happens first decides the branch.
        3. Exit.
        """

    def start(self):
        """Nothing to set up for this demo task."""

        pass

    def create_trial(self):
        # Configure Global Timer 1 to run for 10 seconds once triggered. This
        # just registers the timer's settings on the state machine being
        # built -- it doesn't start counting until GlobalTimer1Trig is
        # actually sent as an output action (see "trigger_global_timer"
        # below), and can be done any time before create_trial returns.
        self.bpod.set_global_timer(timer_id=1, timer_duration=10)

        # Trigger the timer right away, then move straight on -- state_timer=0
        # with a Tup condition just fires the pulse and moves on immediately.
        self.bpod.add_state(
            state_name="trigger_global_timer",
            state_timer=0,
            state_change_conditions={BpodEvent.Tup: "wait_poke_or_timer"},
            output_actions=[BpodOutput.GlobalTimer1Trig],
        )

        # Wait for whichever comes first: a poke in port 1, or Global Timer 1
        # ending (10s after it was triggered above). No state_timer of its
        # own -- the global timer is what bounds this wait.
        self.bpod.add_state(
            state_name="wait_poke_or_timer",
            state_timer=0,
            state_change_conditions={
                BpodEvent.Port1In: "poked",
                BpodEvent.GlobalTimer1End: "exit",
            },
            output_actions=[],
        )

        self.bpod.add_state(
            state_name="poked",
            state_timer=0.1,
            state_change_conditions={
                BpodEvent.Tup: "wait_poke_or_timer",
                BpodEvent.GlobalTimer1End: "exit",
            },
            output_actions=[(BpodOutput.PWM1, 255)],
        )

    def after_trial(self):
        """Just records the number of pokes before the global timer ended."""
        # Bpod lists a state that was not visited as [nan]: count real entries only
        starts = self.trial_data.get("STATE_poked_START", [])
        pokes = sum(1 for t in starts if not math.isnan(t))
        self.register_value("pokes", pokes)

    def close(self):
        pass
