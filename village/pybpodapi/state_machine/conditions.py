import logging

logger = logging.getLogger(__name__)


class Conditions(object):
    def __init__(self, max_states, n_conditions):
        self.matrix = [[] for i in range(max_states)]
        self.values = [0] * n_conditions
        self.channels = [0] * n_conditions
        self.max_size = n_conditions

    def get_max_index_used(self):

        for i in range(self.max_size - 1, -1, -1):
            if self.channels[i] != 0:
                return i

        return None
