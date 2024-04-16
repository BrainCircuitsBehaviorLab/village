import logging

logger = logging.getLogger(__name__)


class GlobalTimers(object):
    def __init__(self, max_states, n_global_timers):

        self.start_matrix = [[] for i in range(max_states)]
        self.end_matrix = [[] for i in range(max_states)]

        # for each state\position has an integer which the bits represents
        # global timers to trigger
        self.triggers_matrix = [0 for i in range(max_states)]

        # for each state\position has an integer which the bits represents
        # global timers to cancel
        self.cancels_matrix = [0 for i in range(max_states)]

        # for each state\position has an integer which the bits represents
        # global timers to on set
        # TODO count the number of timers used on the state machine
        self.onset_matrix = [0] * n_global_timers

        self.timers = [0] * n_global_timers
        self.on_set_delays = [0] * n_global_timers
        self.channels = [255] * n_global_timers
        self.on_messages = [255] * n_global_timers
        self.off_messages = [255] * n_global_timers

        self.loop_mode = [0] * n_global_timers
        self.loop_intervals = [0] * n_global_timers
        self.send_events = [1] * n_global_timers

        self.max_size = n_global_timers

    def get_max_index_used(self):
        for i in range(self.max_size - 1, -1, -1):
            if self.timers[i] != 0:
                return i
        return None
