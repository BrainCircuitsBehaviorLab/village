## Custom Scheduled Actions

Some actions run automatically at fixed points in the system lifecycle. By default, a data synchronization is triggered after each session ends, and old video files are deleted during each day/night cycle transition (the retention period is configurable in `SETTINGS`).

You can override or extend this behavior by creating custom classes in your project. For example, you might want to sync data in a different way, or send a notification (email, Telegram, Slack, etc.) after each session.

If the system detects a class inheriting from `AfterSessionBase` or `ChangeCycleBase` in your project, it will use your custom class instead of the default base class. The file and class names are up to you (the examples below use the usual ones); only one class of each kind is used per project.

---

### After Session Actions

Create a file in your `project/code` folder (e.g. `after_session.py`) with a class (e.g. `AfterSession`) that inherits from `AfterSessionBase`. Its `run` method is executed automatically every time a subject's session ends, in the `SYNC` state, before the system goes back to `WAIT`.

```python
from village.custom_classes.after_session_base import AfterSessionBase
from village.scripts.log import log


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
        log.info("Performing custom after-session actions")  # shown in the events
```

A complete example, which sends an alarm when the sync is too slow:
[after_session.py](../examples/after_session.md).

---

### Change Cycle Actions

Create a file in your `project/code` folder (e.g. `change_cycle.py`) with a class (e.g. `ChangeCycle`) that inherits from `ChangeCycleBase`. Its `run` method is executed automatically after every day/night cycle transition: the transition marks it as pending, and it runs as soon as the system is in `WAIT` (going through the `SYNC` state). If a session is running at that moment, it waits until the session has finished.

```python
from village.custom_classes.change_cycle_base import ChangeCycleBase
from village.scripts.log import log


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
        log.info("Performing custom cycle change actions")  # shown in the events
```

A complete example, which logs how many videos are left after the cleanup:
[change_cycle.py](../examples/change_cycle.md).

```{toctree}
:hidden:

After Session Example <../examples/after_session.md>
Change Cycle Example <../examples/change_cycle.md>
```
