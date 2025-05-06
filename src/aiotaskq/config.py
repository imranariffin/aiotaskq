"""
Module to define and store all configuration values used across the library.

The public object from this module is `Config`. This object wraps
all the configuration values, which include:
- Variables
- Environment variables
"""

import logging
from os import environ

from .interfaces import SerializationType

_REDIS_URL = environ.get("REDIS_URL", "redis://127.0.0.1:6379")


class Config:
    """
    Provide configuration values.

    These include:
    - Variables
    - Environment variables
    """

    @staticmethod
    def serialization_type() -> SerializationType:
        """Return the serialization type as provided via env var AIOTASKQ_SERIALIZATION."""
        s: str = environ.get("AIOTASKQ_SERIALIZATION", SerializationType.DEFAULT.value)
        return SerializationType[s.upper()]

    @staticmethod
    def log_level() -> int:
        """Return the log level as provided via env var LOG_LEVEL."""
        level: int = getattr(logging, environ.get("AIOTASKQ_LOG_LEVEL", "DEBUG"))
        return level

    @staticmethod
    def broker_url() -> str:
        """
        Return the broker url as provided via env var BROKER_URL.

        Defaults to the env var REDIS_URL or "redis://127.0.0.1:6379" if env var is not provided.
        """
        broker_url: str = environ.get("BROKER_URL", _REDIS_URL)
        return broker_url
