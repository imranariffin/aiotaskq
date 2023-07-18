"""
Define all exceptions that are possibly raised by the package.

Any raised thrown must be defined here.
"""


class ModuleInvalidForTask(Exception):
    """Attempt to convert to task a function in an invalid module."""


class UrlNotSupported(Exception):
    """This url is currently not supported."""


class ConcurrencyTypeNotSupported(Exception):
    """This concurrency type is currently not supported."""


class InvalidArgument(Exception):
    """A task is applied with invalid arguments."""
