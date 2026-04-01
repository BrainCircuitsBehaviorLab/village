import logging

from village.pybpodapi.com.messaging.event_occurrence import EventOccurrence

logger = logging.getLogger(__name__)


class Trial:
    """Lightweight internal tracker for Bpod state machine execution.

    Tracks states visited, event occurrences, and timestamps during a trial.
    Used internally by BpodBase during run_state_machine().
    Data output is handled by TrialRecorder.
    """

    def __init__(self, sma=None):
        self.raspberry_trial_start = None
        self.trial_end_timestamp = None
        self.bpod_start_timestamp = None
        self.sma = sma
        self.events_occurrences = []

        self.states = [0]
        self.state_timestamps = [0]
        self.event_timestamps = []

    def add_event(self, event):
        """Add an EventOccurrence to the trial.

        Args:
            event (EventOccurrence): The event to add.
        """
        self.events_occurrences.append(event)
