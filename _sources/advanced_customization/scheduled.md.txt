## Custom Scheduled Actions

Some actions run automatically at fixed points in the system lifecycle. By default, a data synchronization is triggered after each session ends, and old video files are deleted during each day/night cycle transition (the retention period is configurable in `SETTINGS`).

You can override or extend this behavior by creating custom classes in your project. For example, you might want to sync data in a different way, or send a notification (email, Telegram, Slack, etc.) after each session.

If the system detects a class inheriting from `AfterSessionBase` or `ChangeCycleBase` in your project, it will use your custom class instead of the default base class.

---

### After Session Actions

Create a file named `after_session.py` in your `project/code` folder containing a class named `AfterSession` that inherits from `AfterSessionBase`. This class will be executed automatically every time a subject's session ends.

```python
from village.custom_classes.after_session_base import AfterSessionBase


class AfterSession(AfterSessionBase):
    """Operations performed after a session ends.

    The base class handles data synchronization (backup) to either a hard drive
    or a remote server, depending on the current settings.
    """

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        """Executes the post-session logic."""
        super().run()  # remove this line if you don't want the default sync

        # Add your custom actions here
        print("Performing custom after-session actions")
```

---

### Change Cycle Actions

Create a file named `change_cycle.py` in your `project/code` folder containing a class named `ChangeCycle` that inherits from `ChangeCycleBase`. This class will be executed automatically on every day/night cycle transition, provided no animal is currently in the operant box.

```python
from village.custom_classes.change_cycle_base import ChangeCycleBase


class ChangeCycle(ChangeCycleBase):
    """Operations performed during the day/night cycle transition.

    The base class handles cleanup tasks such as deleting old video files.
    It can be configured to only delete videos that have already been synced
    to an external location.
    """

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        """Executes the cycle change logic."""
        super().run()  # remove this line if you don't want the default cleanup

        # Add your custom actions here
        print("Performing custom cycle change actions")
```
