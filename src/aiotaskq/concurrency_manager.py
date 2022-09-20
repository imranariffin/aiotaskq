"""Define IConcurrencyManager implementations."""

from functools import cached_property
import logging
import multiprocessing
import os
import typing as t

from .exceptions import ConcurrencyTypeNotSupported
from .interfaces import ConcurrencyType, IConcurrencyManager, IProcess


class ConcurrencyManagerSingleton:
    """The user-facing facade for creating the right concurrency manager implementation."""

    _instance: t.Optional["IConcurrencyManager"] = None

    @classmethod
    def get(cls, concurrency_type: str, concurrency) -> IConcurrencyManager:
        """
        Return the correct concurrency manager implementation instance based on url.

        Currently supports only MultiProcessing.
        """
        if cls._instance:
            return cls._instance
        if concurrency_type == ConcurrencyType.MULTIPROCESSING:
            cls._instance = MultiProcessing(concurrency=concurrency)
            return cls._instance
        raise ConcurrencyTypeNotSupported(
            f'Concurrency type "{concurrency_type}" is not yet supported.'
        )

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton."""
        cls._instance = None


class MultiProcessing:
    """Implementation of a ConcurrencyManager that uses the `multiprocess` built-in module."""

    def __init__(self, concurrency: int) -> None:
        self.concurrency = concurrency
        self.processes: list[IProcess] = []

    def start(self, func: t.Callable, *args: t.ParamSpecArgs) -> None:
        """Start each processes under management."""
        for _ in range(self.concurrency):
            proc = multiprocessing.Process(target=func, args=args)
            proc.start()
            self.processes.append(proc)

    def terminate(self) -> None:
        """Terminate each process under management."""
        for proc in self.processes:
            self._logger.debug("Sending signal TERM to back worker process [pid=%s]", proc.pid)
            proc.terminate()

    @cached_property
    def _logger(self):
        return logging.getLogger(f"[{os.getpid()}] [{self.__class__.__qualname__}]")
