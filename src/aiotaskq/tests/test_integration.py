import pytest

from aiotaskq.task import Task
from aiotaskq.tests.conftest import WorkerFixture
from aiotaskq.tests.apps import simple_app


@pytest.mark.asyncio
async def test_sync_and_async_parity__simple_app(worker: WorkerFixture):
    # Given a simple app running as a worker
    app = simple_app
    await worker.start(app=app.__name__, concurrency=8)
    # Then there should be parity between sync and async call of the tasks
    tests: list[tuple[Task, tuple, dict]] = [
        (simple_app.add, tuple(), {"x": 41, "y": 1}),
        (simple_app.power, (2,), {"b": 64}),
        (simple_app.join, ([2021, 2, 20],), {}),
        (simple_app.some_task, (21,), {}),
    ]
    for task, args, kwargs in tests:
        sync_result = task(*args, **kwargs)
        async_result = await task.apply_async(*args, **kwargs)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
