from typing import TYPE_CHECKING

import pytest

from aiotaskq.exceptions import InvalidArgument
from tests.apps import simple_app

if TYPE_CHECKING:  # pragma: no cover
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
    await worker.start(simple_app.__name__)

    # When a task has been applied with invalid arguments
    # Then an error should raised
    error = None
    try:
        _ = await task.apply_async(*invalid_args, **invalid_kwargs)
    except InvalidArgument as exc:
        error = exc
    finally:
        assert str(error) == (
            f"These arguments are invalid: args={invalid_args},"
            f" kwargs={invalid_kwargs}"
        )
