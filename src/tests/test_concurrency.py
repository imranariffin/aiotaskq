import asyncio
import typing as t

import pytest

from tests.apps import simple_app

if t.TYPE_CHECKING:  # pragma: no cover
    from tests.conftest import WorkerFixture


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
