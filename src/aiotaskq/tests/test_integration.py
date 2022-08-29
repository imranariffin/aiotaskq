import asyncio
import subprocess
from typing import Any

import pytest

from aiotaskq.main import Task
from aiotaskq.tests.apps import simple_app


@pytest.mark.asyncio
async def test_sync_and_async_parity__simple_app():
    # Given a simple app running as a worker
    app = simple_app
    bash_command = ["aiotaskq", "worker", app.__name__]
    with subprocess.Popen(bash_command) as worker_cli_process:
        # Once worker process is ready
        await asyncio.sleep(0.5)
        # Then there should be parity between sync and async call of the tasks
        tests: list[tuple[Task, Any, Any]] = [
            (simple_app.add, tuple(), {"x": 41, "y": 1}),
            (simple_app.power, (2,), {"b": 64}),
            (simple_app.join, ([2021, 2, 20],), {}),
            (simple_app.some_task, (21,), {}),
        ]
        try:
            for task, args, kwargs in tests:
                sync_result = task(*args, **kwargs)
                async_result = await task.apply_async(*args, **kwargs)
                assert async_result == sync_result, f"{async_result} != {sync_result}"
        finally:
            worker_cli_process.terminate()
