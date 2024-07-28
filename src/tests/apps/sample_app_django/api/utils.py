import logging
from collections.abc import Iterator
from logging import Logger
from time import perf_counter
from typing import TypeVar

T = TypeVar("T")


def chunker(seq: list[T], size: int = 100) -> Iterator[list[T]]:
    chunk: list[T] = []
    for t in seq:
        if len(chunk) == size:
            yield chunk
            chunk = []
        else:
            chunk.append(t)
    if chunk:
        yield chunk


class Timer:
    _name: str | None
    _logger: logging.Logger
    _level: int
    t_0 : float | None
    t_1 : float | None

    def __init__(self, logger: Logger, level: int = logging.DEBUG):
        self._logger = logger
        self._level = level
        self._name = None
        self.t_0 = None
        self.t_1 = None

    def __call__(self, name: str) -> "Timer":
        self._name = name
        return self

    def __enter__(self):
        self._logger.log(self._level, "%s ...", self._name)
        self.t_0 = perf_counter()

    def __exit__(self, *args):
        self.t_1 = perf_counter()
        duration = self.t_1 - self.t_0
        self._logger.log(self._level, "%s took %.4f seconds", self._name, duration)
