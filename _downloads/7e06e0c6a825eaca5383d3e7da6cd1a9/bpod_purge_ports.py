import math

from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase


class BpodPurgePorts(TaskBase):
    """Maintenance task: flushes each of the 3 ports' water line, one at a
    time, by opening its valve for as long as it's poked -- not a training
    task, no reward logic, nothing is registered as water consumed by the
    subject.
    """

    def __init__(self):
        super().__init__()

        self.info = """
        Purge Ports
        ----------------------------------------------------------------
        Not a training task -- flushes stale water out of each port's line.
        Poke and hold any of the 3 ports: its valve opens for as long as
        the poke is held, then closes the moment you release it. Whichever
        port you poked ends the trial; the task then waits for the next
        poke on any port to start the next one.
        """

    def start(self):
        """Nothing to set up for this maintenance task."""

        pass

    def create_trial(self):
        """One state per port: wait for that port's poke, then keep its
        valve open for exactly as long as the poke is held (the valve
        isn't re-listed in the next state, so it closes automatically the
        moment the poke ends -- same pattern as the LED-until-poke-out
        states in bpod_example_outputs_and_events.py).
        """

        self.bpod.add_state(
            state_name="ready_to_purge",
            state_timer=0,
            state_change_conditions={
                BpodEvent.Port1In: "left_open",
                BpodEvent.Port2In: "center_open",
                BpodEvent.Port3In: "right_open",
            },
            output_actions=[],
        )

        self.bpod.add_state(
            state_name="left_open",
            state_timer=0,
            state_change_conditions={BpodEvent.Port1Out: "exit"},
            output_actions=[BpodOutput.Valve1],
        )

        self.bpod.add_state(
            state_name="center_open",
            state_timer=0,
            state_change_conditions={BpodEvent.Port2Out: "exit"},
            output_actions=[BpodOutput.Valve2],
        )

        self.bpod.add_state(
            state_name="right_open",
            state_timer=0,
            state_change_conditions={BpodEvent.Port3Out: "exit"},
            output_actions=[BpodOutput.Valve3],
        )

    def after_trial(self):
        """Records which port was purged. water stays 0 -- this is line
        maintenance, not a reward given to the subject."""

        def visited(state: str) -> bool:
            # Bpod lists a state that was not visited as [nan]
            t = self.trial_data.get(f"STATE_{state}_START", [math.nan])[0]
            return not math.isnan(t)

        if visited("left_open"):
            outcome = "left"
        elif visited("center_open"):
            outcome = "center"
        elif visited("right_open"):
            outcome = "right"
        else:
            outcome = "none"

        self.register_value("outcome", outcome)
        self.register_value("water", 0)

    def close(self):
        """Nothing to clean up."""

        pass
