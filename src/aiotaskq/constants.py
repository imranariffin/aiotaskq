_TASKS_CHANNEL = "channel:tasks"
_RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"


class Constants:
    @staticmethod
    def tasks_channel() -> str:
        """Return the channel name used for transporting task requests on the broker."""
        return _TASKS_CHANNEL

    @staticmethod
    def results_channel_template() -> str:
        """Return the template chnnale name used for transporting task results on the broker."""
        return _RESULTS_CHANNEL_TEMPLATE
