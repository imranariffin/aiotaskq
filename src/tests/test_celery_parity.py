"""
Ensure that aiotaskq has parity with selected celery features.

The goal is to have an interface as close as possible to Celery
to enable easy adoption.
"""

import typing as t

import pytest

from sample_apps.simple_app import app_aiotaskq
from sample_apps.simple_app import app_celery

if t.TYPE_CHECKING:  # pragma: no cover
    from tests.conftest import WorkerFixtureAiotaskq, WorkerFixtureCelery


@pytest.mark.asyncio
async def test_parity_with_celery__simple_app(
    worker_aiotaskq: "WorkerFixtureAiotaskq",
    worker_celery: "WorkerFixtureCelery",
):
    # Given a simple app that uses both Celery and aiotaskq in
    # the following file structure (Please check it out):
    # > tree src/sample_apps/simple_app -I __pycache__
    # src/sample_apps/simple_app
    # ├── aiotaskq.py
    # ├── app_aiotaskq.py
    # ├── app_celery.py
    # ├── celery.py
    # ├── __init__.py
    # ├── tasks_aiotaskq.py
    # ├── tasks_celery.py
    # └── tests.py

    concurrency = 2
    # And the simple app is running as Celery worker in background
    await worker_celery.start(app="sample_apps.simple_app.celery:app", concurrency=concurrency)
    # And the simple app is also running as aiotaskq worker in background
    await worker_aiotaskq.start(app="sample_apps.simple_app.aiotaskq:app", concurrency=concurrency)

    # When both apps are run
    result_aiotaskq = await app_aiotaskq.main()
    result_celery = app_celery.main()

    # Then they should output the same result
    assert result_aiotaskq == result_celery


@pytest.mark.asyncio
async def test_parity_with_celery__simple_app_implicit_instance(
    worker_aiotaskq: "WorkerFixtureAiotaskq",
    worker_celery: "WorkerFixtureCelery",
):
    # Given a simple app that uses both Celery and aiotaskq in
    # the following file structure (Please check it out):
    # > tree src/sample_apps/simple_app_implicit -I __pycache__
    # src/sample_apps/simple_app_implicit_instance
    # ├── app_aiotaskq.py
    # ├── app_celery.py
    # └── __init__.py

    concurrency = 2
    # And the simple app is running as Celery worker in background
    await worker_celery.start(
        app="sample_apps.simple_app_implicit_instance",
        concurrency=concurrency,
    )
    # And the simple app is also running as aiotaskq worker in background
    await worker_aiotaskq.start(
        app="sample_apps.simple_app_implicit_instance.app_aiotaskq",
        concurrency=concurrency,
    )

    # When both apps are run
    result_aiotaskq = await app_aiotaskq.main()
    result_celery = app_celery.main()

    # Then they should output the same result
    assert result_aiotaskq == result_celery
