"""Module to define the main logic of the library."""
# pylint: disable=cyclic-import

import copy

import inspect
import logging
from types import ModuleType
import typing as t
import uuid

from .config import Config
from .constants import Constants
from .exceptions import InvalidArgument, InvalidRetryOptions, ModuleInvalidForTask
from .interfaces import PollResponse, TaskOptions
from .pubsub import PubSub

if t.TYPE_CHECKING:
    from .interfaces import RetryOptions

RT = t.TypeVar("RT")
P = t.ParamSpec("P")

logger = logging.getLogger(__name__)


class AsyncResult(t.Generic[RT]):
    """
    Define the object returned by a Task once called asynchronously.

    To get the result of corresponding task, use `.get()`.
    """

    task_id: str
    ready: bool = False
    result: RT | None
    error: Exception | None

    def __init__(
        self, task_id: str, result: RT | None, ready: bool, error: Exception | None
    ) -> None:
        """Store task_id in AsyncResult instance."""
        self.task_id = task_id
        self.ready = ready
        self.result = result
        self.error = error

    def get(self) -> RT | Exception:
        """Return the result of the task once finished."""
        if self.error is not None:
            return self.error
        return self.result


class Task(t.Generic[P, RT]):
    """
    A callable can be applied asyncronously and executed on an aiotaskq worker process.

    A task is essentially the same as any regular function, which can be
    called synchronously, and thus be executed on the same process. It also can be
    called asynchronously, and thus be executed on a worker process.

    Example:
    ```python
    def some_func(x: int, y: int) -> int:
        return x + y
    some_task = aiotaskq.task(some_func)
    # Or equivalently:
    # @aiotaskq.task()
    # def some_task(x: int, y: int) -> int:
    #     return x + y

    function_result = some_func(1, 2)
    sync_task_result = some_task(1, 2)
    async_task_result = some_task.apply_async(1, 2)

    assert function_result == sync_task_result == async_task_result
    ```
    """

    id: str
    func: t.Callable[P, RT]
    retry: "RetryOptions | None"
    args: t.Optional[tuple[t.Any, ...]]
    kwargs: t.Optional[dict]

    def __init__(
        self,
        func: t.Callable[P, RT],
        *,
        retry: "RetryOptions | None" = None,
        task_id: t.Optional[str] = None,
        args: t.Optional[tuple[t.Any, ...]] = None,
        kwargs: t.Optional[dict] = None,
    ) -> None:
        """
        Store the underlying function and an automatically generated task_id in the Task instance.
        """
        self.func = func

        if retry and len(retry.get("on", [])) == 0:
            raise InvalidRetryOptions('retry.on should not be empty')
        self.retry = retry

        self.args = args
        self.kwargs = kwargs
        self.id = task_id

        # Copy metadata from the function to simulate as close as possible

        self.__module__ = self.func.__module__
        self.__qualname__ = self.func.__qualname__
        self.__name__ = self.func.__name__

    def __call__(self, *args, **kwargs) -> RT:
        """Call the task synchronously, by directly executing the underlying function."""
        return self.func(*args, **kwargs)

    def with_retry(self, max_retries: int, on: tuple[type[Exception], ...]) -> "Task":
        """
        Return a **copy** of self with the provided retry options.

        We return a copy so that we don't overwrite the original task definition.
        """
        task_: Task = copy.deepcopy(self)
        if len(on) == 0:
            raise InvalidRetryOptions
        retry: RetryOptions = {"max_retries": max_retries, "on": on}
        task_.retry = retry
        return task_

    def generate_task_id(self) -> str:
        """Generate a unique id for an individual call to a task."""
        id_ = uuid.uuid4()
        return f"{self.__module__}.{self.__qualname__}:{id_}"

    async def apply_async(self, *args: P.args, **kwargs: P.kwargs) -> RT:
        """
        Call the task asyncronously, by executing the underlying function in a different process.

        Execution is done by the following steps:
        1. Serialize the task (just the task id and its arguments)
        2. Publish it to a Tasks Channel, and wait for the results on a Results Channel
        3. A worker process will pick up the taskand de-serialize it
        4. The worker process find in its memory the task by the task id and execute it as a regular
           function
        5. The worker process will publish the result of the task to Results Channel
        6. The main process (the caller) will pick up the result and return the result. DONE
        """
        # Raise error if arguments provided are invalid, before enything
        self._validate_arguments(task_args=args, task_kwargs=kwargs)
        task_ = copy.deepcopy(self)
        task_.args = args
        task_.kwargs = kwargs
        if task_.id is None:
            task_.id = task_.generate_task_id()
        # pylint: disable=protected-access
        await task_.publish()
        return await task_._get_result()

    async def publish(self) -> None:
        """
        Publish the task.

        At this point we expected that args & kwargs are already provided and task_id is already generated.
        """
        from aiotaskq.serde import Serialization  # pylint: disable=import-outside-toplevel

        assert hasattr(self, "args") and hasattr(self, "kwargs") and self.id is not None

        message: bytes = Serialization.serialize(self)

        pubsub_ = PubSub.get(
            url=Config.broker_url(),
            poll_interval_s=0.01,
            max_connections=10,
            decode_responses=True,
        )
        async with pubsub_ as pubsub:  # pylint: disable=not-async-context-manager
            logger.debug("Publishing task [task_id=%s, message=%s]", self.id, message)
            await pubsub.publish(Constants.tasks_channel(), message=message)

    async def _get_result(self) -> RT:
        from aiotaskq.serde import Serialization  # pylint: disable=import-outside-toplevel

        logger.debug("Retrieving result for task [task_id=%s]", self.id)
        pubsub_ = PubSub.get(url=Config.broker_url(), poll_interval_s=0.01)
        async with pubsub_ as pubsub:  # pylint: disable=not-async-context-manager
            await pubsub.subscribe(Constants.results_channel_template().format(task_id=self.id))
            message: PollResponse = await pubsub.poll()

        logger.debug("Message: %s", message)

        result_serialized: bytes = message["data"]
        async_result: AsyncResult[RT] = Serialization.deserialize(AsyncResult, result_serialized)

        result: RT | Exception = async_result.get()
        if isinstance(result, Exception):
            raise result
        return result

    def _validate_arguments(self, task_args: tuple, task_kwargs: dict):
        try:
            func_sig: "inspect.Signature" = inspect.signature(self.func)
            func_sig.bind(*task_args, **task_kwargs)
        except TypeError as exc:
            raise InvalidArgument(
                f"These arguments are invalid: args={task_args}, kwargs={task_kwargs}"
            ) from exc


def task(*, options: TaskOptions | None = None) -> t.Callable[[t.Callable[P, RT]], Task[P, RT]]:
    """
    Decorator to convert a callable into an aiotaskq Task instance.

    Args:
        options (aiotaskq.interfaces.TaskOptions | None): Specify the options available for a task.
    """

    if options is None:
        options = {}

    def _wrapper(func: t.Callable[P, RT]) -> Task[P, RT]:
        func_module: t.Optional[ModuleType] = inspect.getmodule(func)

        if func_module is None:
            raise ModuleInvalidForTask(
                f'Function "{func.__name__}" is defined in an invalid module {func_module}'
            )

        task_ = Task[P, RT](func, **options)
        return task_

    return _wrapper
