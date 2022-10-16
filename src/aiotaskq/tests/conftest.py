import asyncio
import multiprocessing
import os
import signal
import typing as t

import httpx
import pytest
import uvicorn

from aiotaskq.interfaces import ConcurrencyType
from aiotaskq.worker import Defaults, run_worker_forever


class WorkerFixture:
    proc: multiprocessing.Process

    async def start(
        self,
        app: str,
        concurrency: int = Defaults.concurrency,
        concurrency_type: ConcurrencyType = Defaults.concurrency_type,
        poll_interval_s: float = Defaults.poll_interval_s,
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
        self.proc.close()


@pytest.fixture
def worker():
    worker_ = WorkerFixture()
    yield worker_
    worker_.terminate()
    worker_.close()


class ServerStarletteFixture:
    proc: multiprocessing.Process

    async def start(self, app: str):
        proc = multiprocessing.Process(target=lambda: uvicorn.run(app=app))
        proc.start()
        await self._wait_server_ready()
        self.proc = proc

    def terminate(self):
        """Send TERM signal to the worker process, and wait for it to exit."""
        if self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(timeout=5)

    def close(self) -> None:
        """Release all resources belonging to the worker process."""
        self.proc.close()

    async def _wait_server_ready(self) -> None:
        async def _is_ready(client_: httpx.AsyncClient) -> bool:
            try:
                response = await client_.get(
                    "http://127.0.0.1:8000/healthcheck/", follow_redirects=True
                )
                return response.status_code == 200
            except httpx.ConnectError:
                # Server not serving yet
                return False

        async with httpx.AsyncClient() as client:
            while not (await _is_ready(client_=client)):  # pylint: disable=superfluous-parens
                await asyncio.sleep(0.01)


@pytest.fixture
def server_starlette():
    server = ServerStarletteFixture()
    yield server
    server.terminate()
    server.close()
