import os
from typing import TYPE_CHECKING

import pytest

from aiotaskq.task import task as task_decorator
from aiotaskq.exceptions import InvalidArgument, InvalidRetryOptions
from tests.apps import simple_app

if TYPE_CHECKING:
    from aiotaskq.task import Task
    from tests.conftest import WorkerFixture


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "task,invalid_args,invalid_kwargs",
    [
        pytest.param(
            *(simple_app.add, tuple(), {"invalid_kwarg_1": 1, "invalid_kwarg_2": 2}),
            id="Provide invalid keyword arguments",
        ),
        pytest.param(
            *(simple_app.power, (1, 2, 3), {}),
            id="Provide more positional arguments than allowed",
        ),
        pytest.param(
            *(simple_app.echo, tuple(), {"y": 1}),
            id="Provide positional arguments as keyword, but missing one",
        ),
        pytest.param(
            *(simple_app.add, (1,), {}),
            id="Provide positional argument, but missing one",
        ),
    ],
)
async def test_invalid_argument_provided_to_apply_async(
    worker: "WorkerFixture",
    task: "Task",
    invalid_args: tuple,
    invalid_kwargs: dict,
):
    # Given a worker running in the background
    await worker.start(app=simple_app.__name__)

    # When a task has been applied with invalid arguments
    # Then an error should raised
    error = None
    try:
        _ = await task.apply_async(*invalid_args, **invalid_kwargs)
    except InvalidArgument as exc:
        error = exc
    finally:
        assert str(error) == (
            f"These arguments are invalid: args={invalid_args}," f" kwargs={invalid_kwargs}"
        )


@pytest.mark.asyncio
async def test_retry_as_per_task_definition(worker: "WorkerFixture", some_file: str):
    # Given a worker running in the background
    await worker.start(app=simple_app.__name__, concurrency=1)
    # And a task defined with retry configuration
    assert simple_app.append_to_file.retry["max_retries"] == 2
    assert simple_app.append_to_file.retry["on"] == (simple_app.SomeException,)
    # And the task will raise an exception when called as a function
    exception = None
    try:
        await simple_app.append_to_file(some_file)
    except simple_app.SomeException as e:
        exception = e
    finally:
        if os.path.exists(some_file):
            os.remove(some_file)
        assert isinstance(exception, simple_app.SomeException)

    # When the task has been applied
    exception = None
    try:
        await simple_app.append_to_file.apply_async(filename=some_file)
    except simple_app.SomeException as exc:
        exception = exc
    finally:
        # Then the task should be retried as many times as configured
        with open(some_file, encoding="utf-8") as fi:
            assert len(fi.readlines()) == 1 + 2, f"file: {fi.readlines()}"  # First call + 2 retries
        assert isinstance(exception, simple_app.SomeException)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "retry_on,retries_expected",
    [
        (
            (
                simple_app.SomeException,
                simple_app.SomeException2,
            ),
            1,
        ),
        (
            (
                simple_app.SomeException,
                simple_app.SomeException2,
            ),
            2,
        ),
    ],
)
async def test_retry_as_per_task_call(
    worker: "WorkerFixture",
    retry_on: tuple[type[Exception], ...],
    retries_expected: int,
    some_file: str,
):
    # Given a worker running in the background
    await worker.start(app=simple_app.__name__, concurrency=1)
    # And a task defined WITHOUT retry configuration
    assert simple_app.append_to_file_2.retry is None
    # And the task will raise an exception when called
    exception = None
    try:
        await simple_app.append_to_file_2.func(some_file)
    except simple_app.SomeException2 as e:
        exception = e
    finally:
        assert isinstance(exception, simple_app.SomeException2)
    if os.path.exists(some_file):
        os.remove(some_file)

    # When the task is applied with retry option
    exception = None
    try:
        await simple_app.append_to_file_2.with_retry(
            max_retries=retries_expected,
            on=retry_on,
        ).apply_async(filename=some_file)
    except simple_app.SomeException2 as e:
        exception = e
    finally:
        # Then the task should be retried as many times as requested
        with open(some_file, encoding="utf-8") as fi:
            assert (
                len(fi.readlines()) == 1 + retries_expected
            )  # First call + `retries_expected` retries
        # And the task should fail with the expected exception
        assert isinstance(exception, simple_app.SomeException2)


@pytest.mark.asyncio
async def test_no_retry_as_per_task_call(worker: "WorkerFixture", some_file: str):
    # Given a worker running in the background
    await worker.start(app=simple_app.__name__, concurrency=1)
    # And a task defined WITH retry configuration
    assert simple_app.append_to_file.retry is not None
    # And the task will raise an exception when called
    exception = None
    try:
        await simple_app.append_to_file.func(some_file)
    except simple_app.SomeException as e:
        exception = e
    finally:
        assert isinstance(exception, simple_app.SomeException)
    if os.path.exists(some_file):
        os.remove(some_file)

    # When the task is applied with retry option
    # where retry["on"] doesn't include the exception that the task raises
    exception = None
    retry_on_new = (simple_app.SomeException2,)
    assert [exc not in simple_app.append_to_file.retry["on"] for exc in retry_on_new]
    try:
        await simple_app.append_to_file.with_retry(
            max_retries=2,
            on=retry_on_new,
        ).apply_async(filename=some_file)
    except simple_app.SomeException as e:
        exception = e
    finally:
        # Then the task should NOT be retried
        with open(some_file, encoding="utf-8") as fi:
            assert len(fi.readlines()) == 1
        # And the task should fail with the expected exception
        assert isinstance(exception, simple_app.SomeException)


@pytest.mark.asyncio
async def test_retry_until_successful(worker: "WorkerFixture", some_file: str):
    """Assert that task will stop being retried once it's successfully executed without error."""
    # Given a worker running in the background
    await worker.start(app=simple_app.__name__, concurrency=1)
    # And a task defined WITH retry max_retries = 2
    assert simple_app.append_to_file_first_3_times_with_error.retry["max_retries"] == 2
    # And the task will raise an exception when called until it's called for the 3rd time
    exception = None
    try:
        # Call for the first time
        await simple_app.append_to_file_first_3_times_with_error.func(some_file)
    except simple_app.SomeException as e:
        exception = e
    finally:
        assert exception is not None
    exception = None
    try:
        # Call for the second time
        await simple_app.append_to_file_first_3_times_with_error.func(some_file)
    except simple_app.SomeException as e:
        exception = e
    finally:
        assert exception is not None
    # Call for the third time (Should no longer raise error)
    await simple_app.append_to_file_first_3_times_with_error.func(some_file)
    with open(some_file, mode="r", encoding="utf-8") as fi:
        num_lines = len(fi.read().rstrip("\n").split("\n"))
    assert num_lines == 3
    # Delete the file
    if os.path.exists(some_file):
        os.remove(some_file)

    # When the task is applied
    await simple_app.append_to_file_first_3_times_with_error.apply_async(filename=some_file)

    # Then the task should applied successfully with no error
    # After having been retried 2 times
    with open(some_file, mode="r", encoding="utf-8") as fi:
        num_lines = len(fi.read().rstrip("\n").split("\n"))
    assert num_lines == 3  # (first call + 2 retries)


def test_empty_retry_on_during_task_definition__invalid():
    # When a task is defined with options.retry.on = tuple()
    exception = None
    try:
        @task_decorator(
            options={
                "retry": {
                    "on": tuple(),
                    "max_retries": 1,
                },
            },
        )
        def _():
            return "Hello world"  # pragma: no cover
    except Exception as e:  # pylint: disable=broad-except
        exception = e
    finally:
        # Then InvalidRetryOptions should be raised during task definition
        assert isinstance(exception, InvalidRetryOptions), (
            "Task definition should fail with InvalidRetryOptions"
        )


@pytest.mark.asyncio
async def test_empty_retry_on_during_task_call__invalid(some_file: str):
    # Give a task that is defined without error
    some_task = simple_app.append_to_file

    exception = None
    try:
        # When the task is called with options.retry.on = empty tuple
        await some_task.with_retry(max_retries=1, on=tuple()).apply_async(some_file)
    except Exception as e:  # pylint: disable=broad-except
        exception = e
    finally:
        # Then InvalidRetryOptions should be raised during task call
        assert isinstance(exception, InvalidRetryOptions), "Task call should fail with InvalidRetryOptions"
