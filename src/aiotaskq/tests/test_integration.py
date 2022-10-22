import httpx
import pytest

from aiotaskq.task import Task
from aiotaskq.tests.conftest import WorkerFixture, ServerStarletteFixture
from .apps.simple_app import tasks as simple_app
from .apps.simple_app_starlette import (
    app as simple_app_starlette,
    tasks as simple_app_starlette_worker,
)


@pytest.mark.asyncio
async def test_sync_and_async_parity__simple_app(worker: WorkerFixture):
    # Given a simple app running as a worker
    await worker.start(app=simple_app.__name__, concurrency=8)
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


@pytest.mark.asyncio
async def test_sync_and_async_parity__simple_app_starlette(
    worker: WorkerFixture,
    server_starlette: ServerStarletteFixture,
):
    # Given a simple starlette app running as a worker
    await worker.start(app=simple_app_starlette_worker.__name__)
    # And a simple starlette app running as a server
    await server_starlette.start(app=f"{simple_app_starlette.__name__}:app")
    print("TEST")

    # Then there should be parity between sync and async call of the tasks
    tests: list[tuple[Task, tuple, dict]] = [
        (simple_app_starlette_worker.add, tuple(), {"x": 41, "y": 1}),
        (simple_app_starlette_worker.power, tuple(), {"a": 2, "b": 64}),
        (simple_app_starlette_worker.join, tuple(), {"ls": [2021, 2, 20]}),
        (simple_app_starlette_worker.fibonacci, tuple(), {"n": 21}),
    ]
    for task, args, kwargs in tests:
        sync_result = task(*args, **kwargs)
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            body = {**kwargs}
            response = await client.post(
                f"http://127.0.0.1:8000/{task.__name__}", json=body, headers=headers
            )

            # And the endpoints should be working correctly with the worker
            status_code_actual = response.status_code
            status_code_expected = 201
            assert status_code_actual == status_code_expected
            # And the response should match the direct sync result from the task
            response_data_actual = response.json()
            response_data_expected = sync_result
            assert response_data_actual == response_data_expected
