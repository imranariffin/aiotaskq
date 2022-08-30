from functools import cached_property
import logging
import multiprocessing
import os
import typing as t

from .exceptions import ConcurrencyTypeNotSupported
from .interfaces import ConcurrencyType, IConcurrencyManager, IProcess


class ConcurrencyManager:
    """The user-facing facade for creating the right concurrency manager implementation."""

    _instance: "IConcurrencyManager"

    @classmethod
    def get(cls, concurrency_type: str, concurrency) -> IConcurrencyManager:
        if cls._instance:
            return cls._instance
        if concurrency_type == ConcurrencyType.MULTIPROCESSING:
            cls._instance = MultiProcessing(concurrency=concurrency)
            return cls._instance
        raise ConcurrencyTypeNotSupported(
            f'Concurrency type "{concurrency_type}" is not yet supported.'
        )


class MultiProcessing:
    """Implementation of a ConcurrencyManager that uses the `multiprocess` built-in module."""

    def __init__(self, concurrency: int) -> None:
        self.concurrency = concurrency
        self.processes: dict[int, IProcess] = {}

    def start(self, func: t.Callable, *args: t.ParamSpecArgs) -> None:
        """Start each processes under management."""
        for _ in range(self.concurrency):
            proc = multiprocessing.Process(target=func, args=args)
            proc.start()
            assert proc.pid is not None
            self.processes[proc.pid] = proc

    def terminate(self) -> None:
        """Terminate each process under management."""
        for proc in self.processes.values():
            self._logger.debug("Sending signal TERM to back worker process [pid=%s]", proc.pid)
            proc.terminate()

    @cached_property
    def _logger(self):
        return logging.getLogger(f"[{os.getpid()}] [{self.__class__.__qualname__}]")
