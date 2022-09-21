import asyncio
import multiprocessing
import typing as t

import pytest

from aiotaskq.interfaces import ConcurrencyType
from aiotaskq.worker import Defaults, run_worker_forever


class WorkerFixture:
    proc: multiprocessing.Process

    async def start(
        self,
        app: str,
        concurrency: t.Optional[int] = Defaults.concurrency,
        concurrency_type: t.Optional[ConcurrencyType] = Defaults.concurrency_type,
        poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
    ) -> None:
        proc = multiprocessing.Process(
            target=lambda: run_worker_forever(
                app_import_path=app,
                concurrency=concurrency,
                concurrency_type=concurrency_type,
                poll_interval_s=poll_interval_s,
            )
        )
        proc.start()
        # Wait for worker to be ready, otherwise some tests will get stuck, because
        # we're publishing a task before the worker managed to suscribe. You can
        # replicate this by adding `await asyncio.sleep(1)` right before the line in
        # in worker.py where the worker manager calls `await pubsub.subscribe()`.
        await asyncio.sleep(0.5)
        self.proc = proc

    def terminate(self):
        if self.proc:
            self.proc.terminate()


@pytest.fixture
def worker():
    worker_ = WorkerFixture()
    yield worker_
    worker_.terminate()
