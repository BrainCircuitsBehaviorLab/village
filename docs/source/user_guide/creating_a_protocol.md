### Project Structure

For training animals, the code and data are organized into projects. A project’s structure is automatically created when a new project is started.

A folder is created for the project:
/village/village_projects/name_of_the_project/

Within this folder, there are two subfolders: /data and /code
Let’s first explore how the code is organized:

#### Code

The training protocol consists of one or more Python scripts, each representing a task that the animals can perform. In addition to these scripts, a training script is required. The training script is run every time a subject finishes a task and contains the logic to either advance or regress the subject in their training based on their performance. This could involve changing the task or modifying its parameters.

```{code-block}
:caption: Example 1
code/
├── habituation.py
├── lick_teaching.py
├── task_simple.py
├── final_task.py
├── training_protocol.py
```

```{code-block}
:caption: Example 2
code/
├── follow_the_light.py
├── training_protocol.py
```

In Example 1, there are several tasks corresponding to different training stages. Animals start with habituation, a simple task that helps them get used to the behavioral box. After one or two sessions, they move on to lick_teaching, where they learn to lick the behavioral ports. Once they have completed a sufficient number of trials, they progress to simple_task, a simplified version of the final task. When performance reaches an adequate level, they transition to final_task. The logic governing task progression is written in training_protocol.

In Example 2, there is only one task, follow_the_light, but each time a subject finishes a session, training_protocol adjusts variables to increase the task’s difficulty.

The user can choose either approach—or a combination of both—to organize the training as needed.

#### Tasks

To create a task, a Python file is created, and within it, a class with the task’s name is defined, inheriting functionality from the generic Task class. This process is straightforward. Let’s look at an example:

Within the folder: village/village_projects/demo_project/code/, we create the file simple_task.py with the following code:

```python
class SimpleTask(Task):
    def __init__(self):
        super().__init__()
```

The task is named SimpleTask. It is initialized with __init__, and we acquire all the properties of the generic Task class using super().__init__(). The naming conventions follow Python standards: CamelCase for class names and lower_case for filenames and function names.
If you try to run this task as-is, you will encounter an error indicating that certain methods must be implemented in your class. These methods are:
- `start`
- `create_trial`
- `after_trial`
- `close`

We can implement these methods for now, even if they don’t perform any actions:

```python
class SimpleTask(Task):
    def __init__(self):
        super().__init__()
    def start(self):
        return
    def create_trial(self):
        return
    def after_trial(self):
        return
    def close(self):
        return
```
