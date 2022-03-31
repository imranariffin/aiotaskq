"""
Define all exceptions that are possibly raised by the package.

Any raised thrown must be defined here.
"""


class WorkerNotReady(Exception):
    """Attempt to send task to worker but no worker is subscribing to tasks channel."""


class ModuleInvalidForTask(Exception):
    """Attempt to convert to task a function in an invalid module."""
