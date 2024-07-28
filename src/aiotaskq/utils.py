"""Define util functions for use within the whole library."""

import os
import sys
from contextlib import contextmanager
from importlib import import_module


def import_from_cwd(import_path):
    """Import module as if the caller is located in current working directory (cwd)."""
    with _cwd_in_path():
        return import_module(import_path)


# Private region


@contextmanager
def _cwd_in_path():
    """Context adding the current working directory to sys.path."""
    cwd = os.getcwd()
    if cwd in sys.path:
        yield
    else:
        sys.path.insert(0, cwd)
        try:
            yield cwd
        finally:
            try:
                sys.path.remove(cwd)
            except ValueError:  # pragma: no cover
                pass

# Private region ends
