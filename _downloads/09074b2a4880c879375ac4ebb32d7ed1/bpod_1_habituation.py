from village.custom_classes.task_base import BpodEvent, TaskBase


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

    def start(self):
        """In this simple task we don't need to do anything in the start method."""

        pass

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

    def after_trial(self):
        """
        Here we look at the trial_data dictionary that bpod records automatically
        to find out which events we got.
        """

        outcome = "miss"

        # for each portIn, we have a list of times at which pokes were registered,
        # so we check that there's an entry for that port, that the list of times
        # isn't empty, and that the first time is greater than 0 (i.e. not NaN),
        # which indicates that a poke happened.
        port1 = self.trial_data.get("Port1In")
        if port1 and len(port1) > 0 and port1[0] > 0:
            outcome = "left_poke"

        port2 = self.trial_data.get("Port2In")
        if port2 and len(port2) > 0 and port2[0] > 0:
            outcome = "center_poke"

        port3 = self.trial_data.get("Port3In")
        if port3 and len(port3) > 0 and port3[0] > 0:
            outcome = "right_poke"

        # Register the outcome of the trial and the water consumed
        self.register_value("outcome", outcome)
        self.register_value("water", 0)

    def close(self):
        """
        We don't need to do any extra work when the task finishes.
        """

        pass
