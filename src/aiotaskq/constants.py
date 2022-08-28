"""Module to define and store all constants used across the library."""

REDIS_URL = "redis://127.0.0.1:6379"
TASKS_CHANNEL = "channel:tasks"
RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"
