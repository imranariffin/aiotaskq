import asyncio
import multiprocessing
import os
import signal
import typing as t

import pytest

from aiotaskq.interfaces import ConcurrencyType
from aiotaskq.concurrency_manager import ConcurrencyManagerSingleton
from aiotaskq.worker import Defaults, run_worker_forever


class WorkerFixture:
    proc: multiprocessing.Process

    async def start(
        self,
        *,
        app: str,
        concurrency: t.Optional[int] = Defaults.concurrency(),
        concurrency_type: t.Optional[ConcurrencyType] = Defaults.concurrency_type(),
        worker_rate_limit: int = Defaults.worker_rate_limit(),
        poll_interval_s: t.Optional[float] = Defaults.poll_interval_s(),
    ) -> None:
        # Reset singleton so each test is isolated
        ConcurrencyManagerSingleton.reset()

        proc = multiprocessing.Process(
            target=lambda: run_worker_forever(
                app_import_path=app,
                concurrency=concurrency,
                concurrency_type=concurrency_type,
                worker_rate_limit=worker_rate_limit,
                poll_interval_s=poll_interval_s,
            )
        )
        proc.start()
        # Wait for worker to be ready, otherwise some tests will get stuck, because
        # we're publishing a task before the worker managed to suscribe. You can
        # replicate this by adding `await asyncio.sleep(1)` right before the line in
        # in worker.py where the worker manager calls `await pubsub.subscribe()`.
        await asyncio.sleep(1.0)
        self.proc = proc

    @property
    def pid(self) -> t.Optional[int]:
        return self.proc.pid if self.proc is not None else None

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
        if not self.proc.is_alive():
            self.proc.close()


@pytest.fixture
def worker():
    worker_ = WorkerFixture()
    yield worker_
    worker_.terminate()
    worker_.close()


@pytest.fixture
def some_file():
    filename = "./some_file.txt"
    yield filename
    if os.path.exists(filename):
        os.remove(filename)
