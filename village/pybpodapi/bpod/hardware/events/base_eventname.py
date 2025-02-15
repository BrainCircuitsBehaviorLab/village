import logging

logger = logging.getLogger(__name__)


class BaseEventName(object):
    @staticmethod
    def is_state_timer(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return True if event_name.startswith("Tup") else False

    @staticmethod
    def is_condition(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return True if event_name.startswith("Condition") else False

    @staticmethod
    def is_global_counter_end(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return (
            True
            if event_name.startswith("GlobalCounter") and event_name.endswith("End")
            else False
        )

    @staticmethod
    def is_global_timer_trigger(event_name):
        """
        :param str event_name:
        :rtype: bool
        """
        return event_name == "GlobalTimerTrig"

    @staticmethod
    def is_global_timer_cancel(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return event_name == "GlobalTimerCancel"

    @staticmethod
    def is_global_timer_start(event_name):
        """

        :param str event_name:
        :rtype: bool
        """
        return (
            True
            if event_name.startswith("GlobalTimer") and event_name.endswith("Start")
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
            if event_name.startswith("GlobalTimer") and event_name.endswith("End")
            else False
        )
