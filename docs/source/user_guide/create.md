# Create a Training Protocol

## Project Structure

For training animals, the code and data are organized into projects. A project's
structure is
automatically created when a new project is started.

A folder is created for the project:
```
/village/village_projects/name_of_the_project/
```

Within this folder, there are two subfolders:
```
/data    # Stores all experimental data
/code    # Contains all task scripts and the training protocol
```

The first time you run Training Village, it will automatically create a project called `demo_project`.
It will also clone the [follow-the-light-task](https://github.com/BrainCircuitsBehaviorLab/follow-the-light-task) repository,
which contains a working example for a simple project. You can use it as a base to start creating your own tasks.

## Code Organization

A training protocol consists of one or more Python scripts, each representing a task that the animals can perform. In addition to
these scripts, a training script is required (called `training_protocol.py`).

The training script is run every time a subject finishes a task and contains the logic to either advance or regress the subject in
their training based on their performance. This could involve changing the animal to a different task and/or modifying the
parameters used in the task.

### Examples of Code Structure

```
# Example 1: Multiple sequential tasks
code/
├── habituation.py
├── lick_teaching.py
├── simple_task.py
├── final_task.py
├── training_protocol.py
```

```
# Example 2: One task with progressive difficulty
code/
├── behavioral_task.py
├── training_protocol.py
```

In Example 1, there are several tasks corresponding to different training stages:
1. Animals start with `habituation`, a simple task that helps them get used to the behavioral box
2. After one or two sessions, they move on to `lick_teaching`, where they learn to lick the behavioral ports
3. Once they have completed a sufficient number of trials, they progress to `simple_task`, a simplified version of the final task
4. When performance reaches an adequate level, they transition to `final_task`

In Example 2, there is only one task, `behavioral_task`, but each time a subject finishes a session, `training_protocol.py` adjusts
variables to increase the task's difficulty.

The user can choose either approach to organize the training as needed. In our example we
use a combination of both approaches, we have 2 tasks: `habituation` and `follow_the_light` and some
variables change in the later of them.
Apart from the task and the training protocol, there are other files in the `code` repository
(for creating sounds and plots and other helper files, we will talk about them later).

```
code/
├── __init__.py
├── habituation.py
├── follow_the_light.py
├── training_protocol.py
├── session_plot.py
├── subject_plot.py
├── online_plot.py
├── softcode_functions.py
├── sound_functions.py
├── LICENSE
├── README.md
```

### Training Protocol

The training protocol must be in a file named `training_protocol.py` inside your code folder. The structure of the
training protocol is the following:

```python
from village.classes.training import Training


class TrainingProtocol(Training):
    """
    This class defines the training protocol for animal behavior experiments.

    The training protocol is run every time a task is finished and it determines:
    1. Which new task is scheduled for the subject
    2. How training variables change based on performance metrics


    Required methods to implement:
    - __init__: Initialize the training protocol
    - default_training_settings: Define initial parameters. It is called when creating a new subject.
    - update_training_settings: Update parameters after each session.

    Optional method:
    - gui_tabs: Organize the variables in custom GUI tabs
    """


    def __init__(self) -> None:
        """Initialize the training protocol."""
        super().__init__()
```

First we import the class Training which our custom class TrainingProtocol will depend on.
We initialize the class and call the super().__init__()


### The `default_training_settings()` Method

```python
    def default_training_settings(self) -> None:
        """
        Define all initial training parameters for new subjects.

        This method is called when creating a new subject, and these parameters
        are saved as the initial values for that subject.

        Required parameters:
        - next_task (str): Name of the next task to run
        - refractary_period (int): Waiting time in seconds between sessions
        - minimum_duration (int): Minimum time in seconds for the task before door2 opens
        - maximum_duration (int): Maximum time in seconds before task stops automatically

        Additional parameters:
        You can define any additional parameters needed for your specific tasks.
        These can be modified between sessions based on subject performance.
        """

        # Required parameters for any training protocol
        self.settings.next_task = "Habituation"  # Next task to run
        self.settings.refractary_period = 3600 * 4  # 4 hours between sessions of the same subject
        self.settings.minimum_duration = 600  # Minimum duration of 10 min
        self.settings.maximum_duration = 900  # Maximum duration of 15 min

        # Task-specific parameters
        # (can be modified between sessions or set when the task is run manually)
        self.settings.reward_amount_ml = 0.08  # Reward volume in milliliters
        self.settings.stage = 1  # Current training stage
        self.settings.light_intensity_high = 255 # High light intensity in the port (0-255)
        self.settings.light_intensity_low = 50 # Low light intensity in the port (0-255)
        self.settings.trial_types = ["left_easy",
                                     "right_easy",
                                     "left_hard",
                                     "right_hard"]  # Possible trial types
        self.settings.punishment_time = 1  # Time in seconds for punishment
        self.settings.iti_time = 2  # Inter-trial interval in seconds
        self.settings.response_time = 10  # Time in seconds to respond before timeout
```

We set the value of next_task to "Habituation" so this would be the first task that the
subject will perform.
The refractary period is the time a subject needs to wait until be allowed to enter the
behavioral box again. This period is important to prevent some animals monipolize the
use of the behavioral box. It can be changed depending on the number of subjects in
the systems and the duration of the tasks.
When the minimum_duration is reached door2 is opened so is a choice of the animal if it
continues performing the tasks of it goes out. When the maximum duration is reached,
the tasks stops and the system waits for the animal to come back home. (Door2 is already
open as maximum_duration must be larger or equal to minimum_duration).

#### The `update_training_settings()` Method

This method is essential for training progression. It runs every time a session finishes
and determines how the subject should progress through the training protocol.

Here's an example implementation:

```python
    def update_training_settings(self) -> None:
        """
        Update training parameters after each session.

        This method is called when a session finishes and determines how
        the subject progresses through the training protocol.

        Available data for decision-making:
        - self.subject (str): Name of the current subject
        - self.last_task (str): Name of the task that just finished
        - self.df (pd.DataFrame): DataFrame with all sessions data for this subject

        Example logic:
        - Progress from Habituation to FollowTheLight after 2 sessions with >100 trials
        - Reduce reward amount as training progresses
        - Advance to stage 2 after two consecutive sessions in FollowTheLight with >85% performance
        """

        if self.last_task == "Habituation":
            # Get all Habituation sessions from the dataframe
            df_habituation = self.df[self.df["task"] == "Habituation"]

            # Check if the animal completed at least 2 Habituation sessions
            if len(df_habituation) >= 2:
                # Get data from the last session
                df_last_session = df_habituation.iloc[-1]
                trials_last_session = df_last_session["trial"].iloc[-1]

                # Progress to next task if criteria met (>100 trials)
                if trials_last_session >= 100:
                    self.settings.next_task = "FollowTheLight"
                    self.settings.reward_amount_ml = 0.07  # Decrease reward

        elif self.last_task == "FollowTheLight":
            # Get all FollowTheLight sessions
            df_follow_the_light = self.df[self.df["task"] == "FollowTheLight"]

            # Check if at least 2 sessions completed
            if len(df_follow_the_light) >= 2:
                # Get data from the last two sessions
                df_last_session = df_follow_the_light.iloc[-1]
                df_previous_session = df_follow_the_light.iloc[-2]

                # Calculate performance metrics
                performance_last_session = df_last_session["correct"].mean()
                performance_previous_session = df_previous_session["correct"].mean()
                trials_last_session = df_last_session["trial"].iloc[-1]
                trials_previous_session = df_previous_session["trial"].iloc[-1]

                # Advance to stage 2 if criteria met
                # (>85% correct in two sessions with >100 trials each)
                if (performance_last_session >= 0.85 and
                    performance_previous_session >= 0.85 and
                    trials_last_session >= 100 and
                    trials_previous_session >= 100):
                    self.settings.stage = 2
                    self.settings.reward_amount_ml = 0.05  # Decrease reward
```

#### The optional `gui_tabs()` Method

```python
    def gui_tabs(self):
        """
        It is used to define the organization of the settings in the GUI.
        Whatever that is not defined here will be placed in the "General" tab.

        They need to have the same name as your settings variables.
        You can use the 'Hide' tab to hide a setting from the GUI.

        Items in the lists need to have the same name as your settings variables.

        You can also restrict the possible values for each setting.
        """

        self.gui_tabs = {
            "Port_variables": ["reward_amount_ml",
                              "light_intensity_high",
                              "light_intensity_low"],
            "Other_variables": ["stage",
                               "trial_types",
                               "punishment_time",
                               "iti_time",
                               "response_time"],
        }


        # define possible values for each variable
        self.gui_tabs_restricted = {
            "trial_types": ["left_easy", "right_easy", "left_hard", "right_hard"],
        }
```

If you have a lot of variables in your settings, you may want to organize them in tabs
when they appear in the GUI when you are going to run the task manually.
Also in this case we are restricting the possible values for trial_types, so when
we run the task from the GUI, if we want to change this value, a dropbox menu with
those 4 options will appear.



### Customizing Your Training Protocol

When creating your own training protocol, you can fully customize:

1. **Progression between tasks**: Define when an animal should move to the next task or
return to a simpler one.
2. **Parameter adjustment**: Modify parameters such as reward amount, session duration,
or task difficulty.
3. **Advancement criteria**: Set performance metrics (accuracy, number of trials, etc.)
to determine when an animal is ready to advance.

Remember that you must always implement at least the three required methods (`__init__`, `default_training_settings`,
and `update_training_settings`) in your `TrainingProtocol` class.


### Tasks

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
