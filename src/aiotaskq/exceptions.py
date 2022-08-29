"""
Define all exceptions that are possibly raised by the package.

Any raised thrown must be defined here.
"""


class ModuleInvalidForTask(Exception):
    """Attempt to convert to task a function in an invalid module."""
