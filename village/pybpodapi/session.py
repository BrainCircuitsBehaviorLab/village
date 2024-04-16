import logging
import sys
from datetime import datetime as datetime_now

from pybpodapi.com.messaging.state_occurrence import StateOccurrence
from pybpodapi.com.messaging.trial import Trial
from pybpodapi.utils import csv

logger = logging.getLogger(__name__)


class StreamsWrapper(object):
    def __init__(self, streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def close(self):
        for stream in self.streams:
            stream.flush()
            stream.close()


class Session(object):
    """
    Stores information about bpod run, including the list of trials.
    """

    def __init__(self, path=None):
        self.ostdout = sys.stdout
        self.ostderr = sys.stderr

        # the variable will contain a list of streams where the session output
        # should be written.
        streams = []

        self.history = []  # type: list[Trial]
        self.trials = []  # type: list[Trial]
        self.firmware_version = None  # type: int
        self.bpod_version = None  # type: int
        self.start_timestamp = datetime_now.now()

        self.csvwriter = None
        self._path = path

        # stream data to a file.
        if path:
            streams += [open(path, "w")]

        self.csvstream = StreamsWrapper(streams)
        self.csvwriter = csv.Writer(
            self.csvstream,
            columns_headers=["TRIAL", "START", "END", "MSG", "VALUE"],
        )

    def __del__(self):

        self.csvstream.close()

        sys.stdout = self.ostdout
        sys.stderr = self.ostderr

    def __add__(self, msg):
        """
        Add new trial to this session and associate a state machine to it

        :param pybpodapi.model.state_machine sma: state machine
        associated with this trial
        """

        if isinstance(msg, Trial):
            self.trials.append(msg)
        elif self.current_trial is not None:
            self.current_trial += msg

        self.history.append(msg)

        if self.csvwriter:
            if msg.MESSAGE_TYPE_ALIAS == "VAL":
                if msg.content == "TRIAL":
                    time0 = self.current_trial.trial_start_timestamp
                    time1 = (
                        self.current_trial.trial_end_timestamp
                        - self.current_trial.difference
                    )
                    self.csvwriter.writerow(
                        [len(self.trials)] + [time0, time1] + msg.tolist()
                    )
                    self.csvwriter.flush()
                else:
                    self.csvwriter.writerow([len(self.trials)] + [None] + msg.tolist())
                    self.csvwriter.flush()
            elif msg.MESSAGE_TYPE_ALIAS in {
                "INFO",
                "TRIAL",
                "END-TRIAL",
                "stdout",
                "stderr",
            }:
                pass
            else:
                self.csvwriter.writerow([len(self.trials)] + msg.tolist())
                self.csvwriter.flush()
        return self

    def add_trial_events(self):

        current_trial = self.current_trial  # type: Trial
        sma = current_trial.sma

        visitedStates = [0] * current_trial.sma.total_states_added
        # determine unique states while preserving visited order
        uniqueStates = []
        nUniqueStates = 0
        uniqueStateIndexes = [0] * len(current_trial.states)

        for i in range(len(current_trial.states)):
            if current_trial.states[i] in uniqueStates:
                uniqueStateIndexes[i] = uniqueStates.index(current_trial.states[i])
            else:
                uniqueStateIndexes[i] = nUniqueStates
                nUniqueStates += 1
                uniqueStates.append(current_trial.states[i])
                visitedStates[current_trial.states[i]] = 1

        # Create a 2-d matrix for each state in a list
        uniqueStateDataMatrices = [[] for i in range(len(current_trial.states))]

        # Append one matrix for each unique state
        for i in range(len(current_trial.states)):
            if len(current_trial.state_timestamps) > 1:
                uniqueStateDataMatrices[uniqueStateIndexes[i]] += [
                    (
                        current_trial.state_timestamps[i]
                        + current_trial.trial_start_timestamp,
                        current_trial.state_timestamps[i + 1]
                        + current_trial.trial_start_timestamp,
                    )
                ]

        for i in range(nUniqueStates):
            thisStateName = sma.state_names[uniqueStates[i]]

            for state_dur in uniqueStateDataMatrices[i]:
                self += StateOccurrence(thisStateName, state_dur[0], state_dur[1])

        logger.debug("State names: %s", sma.state_names)
        logger.debug("nPossibleStates: %s", sma.total_states_added)
        for i in range(sma.total_states_added):
            thisStateName = sma.state_names[i]
            if not visitedStates[i]:
                self += StateOccurrence(thisStateName, float("NaN"), float("NaN"))

        logger.debug(
            "Trial states: %s",
            [str(state) for state in current_trial.states_occurrences],
        )

        # save events occurrences on trial
        # current_trial.events_occurrences = sma.raw_data.events_occurrences

        logger.debug(
            "Trial events: %s",
            [str(event) for event in current_trial.events_occurrences],
        )

        logger.debug("Trial info: %s", str(current_trial))

    @property
    def current_trial(self):
        """
        Get current trial

        :rtype: Trial
        """
        return self.trials[-1] if len(self.trials) > 0 else None

    @current_trial.setter
    def current_trial(self, value):
        """
        Get current trial

        :rtype: Trial
        """
        self.trials[-1] = value
