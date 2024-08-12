"""
Module to define and store all constants used across the library.

The public object from this module is `Constants`. This object wraps
all the constants, which include:
- Static methods that return constant values
"""


_TASKS_CHANNEL = "channel:tasks"
_RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"


class Constants:
    """
    Provide all the constants.

    These include:
    - Static methods that return constant values
    """

    @staticmethod
    def tasks_channel() -> str:
        """Return the channel name used for transporting task requests on the broker."""
        return _TASKS_CHANNEL

    @staticmethod
    def results_channel_template() -> str:
        """Return the template chnnale name used for transporting task results on the broker."""
        return _RESULTS_CHANNEL_TEMPLATE
