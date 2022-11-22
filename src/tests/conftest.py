import asyncio
from abc import ABC, abstractmethod
import importlib
import multiprocessing
import os
import signal
import typing as t

import pytest

from aiotaskq.interfaces import ConcurrencyType
from aiotaskq.worker import Defaults, run_worker_forever

if t.TYPE_CHECKING:  # pragma: no cover
    from celery import Celery


class _WorkerFixtureBase(ABC):
    proc: multiprocessing.Process

    @abstractmethod
    async def start(self, *args, **kwargs) -> None:
        """Start worker process."""
    
    def terminate(self):
        """Send TERM signal to the worker process, and wait for it to exit."""
        if self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(timeout=5)

    def interrupt(self) -> None:
        """Send INT signal to the worker process, and wait for it to exit."""
        if self.proc.is_alive():
            os.kill(self.proc.pid, signal.SIGINT)  # type: ignore
            self.proc.join(timeout=5)

    def close(self) -> None:
        """Release all resources belonging to the worker process."""
        self.proc.close()
    
    async def _start_and_set_proc(self, proc: "multiprocessing.Process") -> None:
        proc.start()
        # Wait for worker to be ready, otherwise some tests will get stuck, because
        # we're publishing a task before the worker managed to suscribe. You can
        # replicate this by adding `await asyncio.sleep(1)` right before the line in
        # in worker.py where the worker manager calls `await pubsub.subscribe()`.
        await asyncio.sleep(1.0)
        self.proc = proc


class WorkerFixtureAiotaskq(_WorkerFixtureBase):
    proc: multiprocessing.Process

    @property
    def pid(self) -> t.Optional[int]:
        return self.proc.pid if self.proc is not None else None

    async def start(
        self,
        app: str,
        concurrency: t.Optional[int] = Defaults.concurrency,
        concurrency_type: t.Optional[ConcurrencyType] = Defaults.concurrency_type,
        poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
    ):
        proc = multiprocessing.Process(
            target=lambda: run_worker_forever(
                app_import_path=app,
                concurrency=concurrency,
                concurrency_type=concurrency_type,
                poll_interval_s=poll_interval_s,
            )
        )
        await self._start_and_set_proc(proc=proc)


class WorkerFixtureCelery(_WorkerFixtureBase):
    proc: multiprocessing.Process

    async def start(self, app: str, concurrency: int) -> None:
        module_path, app_attr_name = app.split(":")
        module = importlib.import_module(module_path)
        app_instance: "Celery" = getattr(module, app_attr_name)
        proc = multiprocessing.Process(
            target=lambda: app_instance.worker_main(
                argv=[
                    "worker",
                    f"--concurrency={concurrency}",
                ],
            ),
        )
        await self._start_and_set_proc(proc=proc)


@pytest.fixture
def worker():
    worker_ = WorkerFixtureAiotaskq()
    yield worker_
    worker_.terminate()
    worker_.close()


@pytest.fixture
def worker_celery():
    worker_ = WorkerFixtureCelery()
    yield worker_
    worker_.terminate()
    worker_.close()
