import logging

logger = logging.getLogger(__name__)


class GlobalCounters(object):
    def __init__(self, max_states, n_global_counters):
        self.matrix = [[] for i in range(max_states)]

        self.reset_matrix = [0 for i in range(max_states)]

        self.attached_events = [254] * n_global_counters
        self.thresholds = [0] * n_global_counters

        self.max_size = n_global_counters

    def get_max_index_used(self):

        for i in range(self.max_size - 1, -1, -1):
            if self.thresholds[i] != 0:
                return i

        return None
