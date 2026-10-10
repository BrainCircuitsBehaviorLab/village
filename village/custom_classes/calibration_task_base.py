from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils


class CalibrationTaskBase(TaskBase):
    """Base class for the tasks launched from a calibration panel (e.g. to
    open the valves or play a sound while the experimenter measures).

    It is a TaskBase with three differences:
    - It is not listed in the TASKS tab, and import_all does not instantiate
      it, so its __init__ can take the arguments the panel needs.
    - Without Bpod, register_start_trial is optional: if create_trial does
      not call it, the trial is started and ended when create_trial returns.
      Calibration tasks run with no subject and save no session, so their
      trial data is not used.
    - start, after_trial and close do nothing by default, and the task runs
      one trial (self.maximum_number_of_trials = 1) unless changed. Only
      create_trial has to be written.

    Launch it from the calibration panel with self.run_task(task) (see
    CalibrationBase).
    """

    def __init__(self) -> None:
        super().__init__()
        self.maximum_number_of_trials = 1

    def start(self) -> None:
        pass

    def after_trial(self) -> None:
        pass

    def close(self) -> None:
        pass

    def close_trial_without_bpod(self) -> None:
        """Like TaskBase's, but starts the trial now if create_trial did not."""
        if not self.recorder.trial_started:
            now = time_utils.now_timestamp()
            self.register_start_trial(now, now)
        super().close_trial_without_bpod()
