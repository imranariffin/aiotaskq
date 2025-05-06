import asyncio
import typing as t
from time import time

import pytest

from tests.apps import simple_app

if t.TYPE_CHECKING:
    from tests.conftest import WorkerFixture


@pytest.mark.asyncio
async def test_async_concurrency(worker: "WorkerFixture"):
    # Given that the worker cli is run with "--concurrency 1" option
    await worker.start(app=simple_app.__name__, concurrency=1)

    # When multiple async tasks are being queued at the same time
    t_0 = time()
    results_actual = await asyncio.gather(*[simple_app.wait.apply_async(t_s=1) for _ in range(5)])
    t_1 = time()

    # Then those async tasks should run concurrently in that one worker
    dt_actual = t_1 - t_0
    error = 0.2
    assert 1.0 < dt_actual < 1.0 + error
    # And the results should be correct
    results_expected = [1, 1, 1, 1, 1]
    assert results_actual == results_expected


@pytest.mark.asyncio
async def test_async_worker_rate_limit(worker: "WorkerFixture"):
    # Given that the worker cli is run with "--concurrency 1" and "--worker-rate-limit 3" options
    await worker.start(app=simple_app.__name__, concurrency=1, worker_rate_limit=3)

    # When multiple async tasks are being queued at the same time
    t_0 = time()
    results_actual = await asyncio.gather(*[simple_app.wait.apply_async(t_s=1) for _ in range(5)])
    t_1 = time()

    # Then those async tasks should run concurrently in that one worker, limited to 3 tasks at a time
    dt_actual = t_1 - t_0
    num_batches = 2  # 3 tasks run simultaneously, then 2 tasks run simultaneously
    error = 0.2
    assert 1.0 * num_batches < dt_actual < (1.0 + error) * num_batches
    # And the results should be correct
    results_expected = [1, 1, 1, 1, 1]
    assert results_actual == results_expected


@pytest.mark.asyncio
async def test_serial_async_tasks_return_correctly(worker: "WorkerFixture"):
    # Given that worker cli is run
    await worker.start(app=simple_app.__name__)

    # When multiple async tasks with different expected return value are applied serially
    results_1 = await simple_app.echo.apply_async(x=1)
    results_2 = await simple_app.echo.apply_async(x=2)
    results_3 = await simple_app.echo.apply_async(x=3)
    results_actual = [results_1, results_2, results_3]

    # Then the results should be correct
    results_expected = [1, 2, 3]
    assert results_actual == results_expected


@pytest.mark.asyncio
async def test_concurrent_async_tasks_return_correctly(worker: "WorkerFixture"):
    # Given that worker cli is run with "--concurrency 2" option
    await worker.start(app=simple_app.__name__, concurrency=2)

    # When multiple async tasks with different expected return value are applied simultaneously
    results_actual = await asyncio.gather(
        *[
            simple_app.echo.apply_async(x=1),
            simple_app.echo.apply_async(x=2),
            simple_app.echo.apply_async(x=3),
        ],
    )

    # Then the results should be correct
    results_expected = [1, 2, 3]
    assert results_actual == results_expected


@pytest.mark.asyncio
async def test_async__concurrency_and_worker_rate_limit_of_1__effectively_serial(
    worker: "WorkerFixture",
):
    """Assert that if concurrency=1 & worker-rate-limit=1, tasks will effectively run serially."""
    # Given that the worker cli is run with "--concurrency 1" and "--worker-rate-limit 1" options
    await worker.start(app=simple_app.__name__, concurrency=1, worker_rate_limit=1)

    # When multiple async tasks are being queued at the same time
    t_0 = time()
    results_actual = await asyncio.gather(*[simple_app.wait.apply_async(t_s=1) for _ in range(5)])
    t_1 = time()

    # Then those async tasks will run serially
    dt_actual = t_1 - t_0
    error = 0.2
    assert 1.0 * 5 <= dt_actual < (1.0 + error) * 5
    # And the results should be correct
    results_expected = [1, 1, 1, 1, 1]
    assert results_actual == results_expected
