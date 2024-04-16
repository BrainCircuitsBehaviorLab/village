import logging

logger = logging.getLogger(__name__)


class BaseEventName(object):
    @staticmethod
    def is_state_timer(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return True if event_name.startswith("_Tup") else False

    @staticmethod
    def is_condition(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return True if event_name.startswith("_Condition") else False

    @staticmethod
    def is_global_counter_end(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return (
            True
            if event_name.startswith("_GlobalCounter") and event_name.endswith("End")
            else False
        )

    @staticmethod
    def is_global_timer_trigger(event_name):
        """
        :param str event_name:
        :rtype: bool
        """
        return event_name == "_GlobalTimerTrig"

    @staticmethod
    def is_global_timer_cancel(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return event_name == "_GlobalTimerCancel"

    @staticmethod
    def is_global_timer_start(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return (
            True
            if event_name.startswith("_GlobalTimer") and event_name.endswith("Start")
            else False
        )

    @staticmethod
    def is_global_timer_end(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return (
            True
            if event_name.startswith("_GlobalTimer") and event_name.endswith("End")
            else False
        )
