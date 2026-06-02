## Task Development Guide


To create a task, create a Python file, and within it, a class with the task’s name,
inheriting functionality from the generic `Task` class. This process is straightforward.
Let’s look at an example:

Let's explore the task `habituation.py` inside your code folder. The structure of the
task is the following:


```python
from village.classes.task import Event, Output, Task
from village.manager import manager


class Habituation(Task):
    """
    This class defines the task.

    Required methods to implement:
    - __init__: Initialize the task
    - start: Called when the task starts.
    - create_trial: Called once per trial to create the state machine.
    - after_trial: Called once after each trial to register the values in the .csv file.
    - close: Called when the task is finished.
    """

    def __init__(self):
        """
        Initialize the training protocol. The text in the self.info variable
        will be shown when the task is selected in the GUI to be run manually.
        """
        super().__init__()

        self.info = """

        Habituation Task
        -------------------

        This task is a simple visual task where the mouse has
        to poke in illuminated ports.
        The center port illuminates when a trial starts.
        After the center port is poked,
        both side ports are illuminated and give reward.
        """
```

The task is named Habituation. It is initialized with __init__, and we acquire all the properties of the generic Task class using super().__init__(). The naming conventions follow Python standards: CamelCase for class names and lower_case for filenames and function names.
Certain methods must be implemented in your class. These methods are:

### The `start()` Method

```python
    def start(self):
        """
        This function is called when the task starts.
        It is used to calculate values needed for the task.
        The following variables are accessible by default:
        - self.bpod: (Bpod object)
        - self.name: (str) the name of the task
                (it is the name of the class, in this case Habituation)
        - self.subject: (str) the name of the subject performing the task
        - self.current_trial: (int) the current trial number starting from 1
        - self.system_name: (str) the name of the system as defined in the
                                tab settings of the GUI
        - self.settings: (Settings object) the settings defined in training_protocol.py
        - self.trial_data: (dict) information about the current trial
        - self.force_stop: (bool) if made true the task will stop

        Al the variables created in training_protocol.py are accessible.
        - self.settings.reward_amount_ml: reward volume
        - self.settings.stage: current training stage
        - self.settings.light_intensity_high: high light intensity
        - self.settings.light_intensity_low: low light intensity
        - self.settings.trial_types: possible trial types
        - self.settings.punishment_time: punishment duration
        - self.settings.iti_time: inter-trial interval
        """

        # First we calculate the time that the valves (or pumps) need to open to deliver
        # the reward amount
        # Make sure to calibrate the valves before using this function, otherwise
        # it will return an Exception
        self.left_valve_opening_time = manager.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_amount_ml
        )
        self.right_valve_opening_time = manager.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_amount_ml
        )
```

### The `create_trial()` Method

```python
    def create_trial(self):
        """
        This function is called once per trial, first it modifies variables and then
        sends the state machine to the bpod that will run the trial.
        """

        # 'ready_to_initiate': state that turns on the central port light and
        # waits for a poke in the central port (Port2)
        self.bpod.add_state(
            state_name="ready_to_initiate",
            state_timer=0,
            state_change_conditions={Event.Port2In: "stimulus_state"},
            output_actions=[(Output.PWM2, self.settings.light_intensity_high)],
        )

        # 'stimulus_state': state that turns on the side ports and
        # waits for a poke in one of the side ports (Port1 or Port3)
        self.bpod.add_state(
            state_name="stimulus_state",
            state_timer=0,
            state_change_conditions={
                Event.Port1In: "reward_state_left",
                Event.Port3In: "reward_state_right",
            },
            output_actions=[
                (Output.PWM1, self.settings.light_intensity_high),
                (Output.PWM3, self.settings.light_intensity_high),
            ],
        )

        # 'reward_state_left' and 'reward_state_right': states that deliver the reward
        self.bpod.add_state(
            state_name="reward_state_left",
            state_timer=self.left_valve_opening_time,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[Output.Valve1],
        )

        self.bpod.add_state(
            state_name="reward_state_right",
            state_timer=self.right_valve_opening_time,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[Output.Valve3],
        )
```
### The `after_trial()` Method

```python
    def after_trial(self):
        """
        Here you can register all the values you need to save for each trial.
        It is essential to always include a variable named water, which stores the
        amount of water consumed during each trial.
        The system will calculate the total water consumption in each session
        by summing this variable.
        If the total water consumption falls below a certain threshold,
        an alarm will be triggered.
        This threshold can be adjusted in the Settings tab of the GUI.
        """

        self.register_value("water", self.settings.reward_amount_ml)
```

### The `close()` Method

```python
    def close(self):
        """
        Here you can perform any actions you want to take once the task is completed,
        such as sending a message via email or Slack, creating a plot, and more.
        """

        pass
```

### The FollowTheLight Task

Now you can explore the more complex FollowTheLight Task, where we use other variables that
were created in the settings training_protocol.

```python
from village.classes.task import Event, Output, Task
from village.manager import manager
import random


class FollowTheLight(Task):
    def __init__(self):
        super().__init__()

        self.info = """

        Follow The Light Task
        -------------------

        This task is a simple visual task where the mouse has
        to poke the center port to start a trial.
        After the center port is poked,
        one of the two side ports will be illuminated.
        If the mouse licks the correct side port, it receives a reward.
        If the mouse licks the wrong side port, it receives a punishment.

        It contains 2 training stages:
        - Training stage 1: Only one side port is illuminated and gives reward.
                            No punishment is given, and the mouse can choose again.
        - Training stage 2: Both ports are illuminated with different intensity.
                            Brighter port gives reward, the other one gives punishment.

        The progression through the stages is defined in the training_settings.py file.
        """


    def start(self):
        """
        Al the variables created in training_protocol.py are accessible.
        - self.settings.reward_amount_ml: reward volume
        - self.settings.stage: current training stage
        - self.settings.light_intensity_high: high light intensity
        - self.settings.light_intensity_low: low light intensity
        - self.settings.trial_types: possible trial types
        - self.settings.punishment_time: punishment duration
        - self.settings.iti_time: inter-trial interval
        """

        # First we calculate the time that the valves (or pumps) need to open to deliver
        # the reward amount
        # Make sure to calibrate the valves before using this function, otherwise
        # it will return an Exception
        self.left_valve_opening_time = manager.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_amount_ml
        )
        self.right_valve_opening_time = manager.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_amount_ml
        )

        # determine if punishment will be used depending on stage
        if self.settings.stage == 1:
            # no punishment is used, let the mouse choose again
            self.punish_condition = "stimulus_state"
        else:
            # punishment is used
            self.punish_condition = "punish_state"


    def create_trial(self):
        # Pick a trial type at random
        self.this_trial_type = random.choice(self.settings.trial_types)

        # Set the variables for the stimulus states and the possible choices
        # based on the trial type
        self.stimulus_state_output = []
        if "left" in self.this_trial_type:
            self.stimulus_state_output.append(
                (Output.PWM1, self.settings.light_intensity_high)
            )
            if "hard" in self.this_trial_type:
                self.stimulus_state_output.append(
                    (Output.PWM3, self.settings.light_intensity_low)
                )
            self.left_poke_action = "reward_state"
            self.valve_to_open = Output.Valve1
            self.valve_opening_time = self.left_valve_opening_time
            self.right_poke_action = self.punish_condition

        elif "right" in self.this_trial_type:
            self.stimulus_state_output.append(
                (Output.PWM3, self.settings.light_intensity_high)
            )
            if "hard" in self.this_trial_type:
                self.stimulus_state_output.append(
                    (Output.PWM1, self.settings.light_intensity_low)
                )
            self.left_poke_action = self.punish_condition
            self.right_poke_action = "reward_state"
            self.valve_to_open = Output.Valve3
            self.valve_opening_time = self.right_valve_opening_time


        # 'ready_to_initiate' state that waits for the poke in the middle port
        self.bpod.add_state(
            state_name="ready_to_initiate",
            state_timer=0,
            state_change_conditions={Event.Port2In: "stimulus_state"},
            output_actions=[(Output.PWM2, self.settings.light_intensity_high)],
        )

        # 'stimulus_state' lights the side ports
        self.bpod.add_state(
            state_name="stimulus_state",
            state_timer=self.settings.timer_for_response,
            state_change_conditions={
                Event.Port1In: self.left_poke_action,
                Event.Port3In: self.right_poke_action,
                Event.Tup: "exit",
            },
            output_actions=self.stimulus_state_output,
        )

        # 'reward_state' delivers the reward
        self.bpod.add_state(
            state_name="reward_state",
            state_timer=self.valve_opening_time,
            state_change_conditions={Event.Tup: "iti_state"},
            output_actions=[self.valve_to_open],
        )

        # 'punish_state' waits during the punishment time
        self.bpod.add_state(
            state_name="punish_state",
            state_timer=self.settings.punishment_time,
            state_change_conditions={Event.Tup: "iti_state"},
            output_actions=[],
        )

        # 'iti_state' waits for certain time before starting the next trial
        # (inter-trial interval)
        self.bpod.add_state(
            state_name="iti_state",
            state_timer=self.settings.iti_time,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[],
        )


    def after_trial(self):
        # First, we calculates the performance of a trial, comparing the trial type
        # to the first port that the mouse poked.
        # We can access the trial information in self.trial_data

        # get the side port that the mouse poked first
        first_poke = self.find_first_occurrence(
            self.trial_data["ordered_list_of_events"],
            ["Port1In", "Port3In"],
        )
        # check if the mouse poked the correct port
        if first_poke == "Port1In" and "left" in self.this_trial_type:
            correct = True
        elif first_poke == "Port3In" and "right" in self.this_trial_type:
            correct =  True
        else:
            correct =  False

        # register the amount of water given to the mouse in this trial
        # (this is always mandatory)
        self.register_value("water", self.settings.reward_amount_ml)

        # we will also record the trial type
        self.register_value("trial_type", self.this_trial_type)

        # we will also record if the trial was correct or not
        self.register_value("correct", correct)


    def close(self):
        pass


    def find_first_occurrence(self, event_list, targets):
        """
        Helper function to find the first occurrence of any target event in the list.

        Args:
            event_list: List of events
            targets: List of target events to look for

        Returns:
            The first target event found, or "NaN" if none are found
        """
        for event in event_list:
            if event in targets:
                return event
        return "NaN"
```
