"""
Module to define and store all constants used across the library.

The public object from this module is `Config`. This object wraps
all the constants, which include:
- Variables
- Environment variables
- Static methods that return constant values
"""

import logging
from os import environ

from .interfaces import SerializationType

_REDIS_URL = "redis://127.0.0.1:6379"
_TASKS_CHANNEL = "channel:tasks"
_RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"


class Config:
    """
    Provide configuration values.

    These include:
    - Variables
    - Environment variables
    - Static methods that return constant values
    """

    @staticmethod
    def serialization_type() -> SerializationType:
        """Return the serialization type as provided via env var AIOTASKQ_SERIALIZATION."""
        s: str | None = environ.get("AIOTASKQ_SERIALIZATION", SerializationType.DEFAULT.value)
        return SerializationType[s.upper()]

    @staticmethod
    def log_level() -> int:
        """Return the log level as provided via env var LOG_LEVEL."""
        level: int = int(environ.get("AIOTASKQ_LOG_LEVEL", logging.DEBUG))
        return level

    @staticmethod
    def broker_url() -> str:
        """
        Return the broker url as provided via env var BROKER_URL.

        Defaults to "redis://127.0.0.1:6379".
        """
        broker_url: str = environ.get("BROKER_URL", _REDIS_URL)
        return broker_url

    @staticmethod
    def tasks_channel() -> str:
        """Return the channel name used for transporting task requests on the broker."""
        return _TASKS_CHANNEL

    @staticmethod
    def results_channel_template() -> str:
        """Return the template chnnale name used for transporting task results on the broker."""
        return _RESULTS_CHANNEL_TEMPLATE
