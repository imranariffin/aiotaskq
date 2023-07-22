"""Module to define the main logic of the library."""

import inspect
import json
import logging
from types import ModuleType
import typing as t
import uuid

from .constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL
from .exceptions import InvalidArgument, ModuleInvalidForTask
from .interfaces import IPubSub, PollResponse
from .pubsub import PubSub

RT = t.TypeVar("RT")
P = t.ParamSpec("P")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AsyncResult(t.Generic[RT]):
    """
    Define the object returned by a Task once called asynchronously.

    To get the result of corresponding task, use `.get()`.
    """

    pubsub: IPubSub
    _result: RT
    _completed: bool = False
    _task_id: str

    def __init__(self, task_id: str) -> None:
        """Store task_id in AsyncResult instance."""
        self._task_id = task_id
        self.pubsub = PubSub.get(url=REDIS_URL, poll_interval_s=0.01)

    async def get(self) -> RT:
        """Return the result of the task once finished."""
        async with self.pubsub as pubsub:  # pylint: disable=not-async-context-manager
            message: PollResponse
            await pubsub.subscribe(RESULTS_CHANNEL_TEMPLATE.format(task_id=self._task_id))
            message = await self.pubsub.poll()
            logger.debug("Message: %s", message)
            _result: RT = json.loads(message["data"])
        return _result


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
    # @aiotaskq.task
    # def some_task(x: int, y: int) -> int:
    #     return x + y

    function_result = some_func(1, 2)
    sync_task_result = some_task(1, 2)
    async_task_result = some_task.apply_async(1, 2)

    assert function_result == sync_task_result == async_task_result
    ```
    """

    __qualname__: str
    func: t.Callable[P, RT]

    def __init__(self, func: t.Callable[P, RT]) -> None:
        """
        Store the underlying function and an automatically generated task_id in the Task instance.
        """
        self.func = func

    def __call__(self, *args, **kwargs) -> RT:
        """Call the task synchronously, by directly executing the underlying function."""
        return self.func(*args, **kwargs)

    def generate_task_id(self) -> str:
        """Generate a unique id for an individual call to a task."""
        id_ = uuid.uuid4()
        return f"{self.__qualname__}:{id_}"

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

        task_id: str = self.generate_task_id()
        message: str = json.dumps(
            {
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
            }
        )
        pubsub_ = PubSub.get(
            url=REDIS_URL, poll_interval_s=0.01, max_connections=10, decode_responses=True
        )
        async with pubsub_ as pubsub:  # pylint: disable=not-async-context-manager
            logger.debug("Publishing task [task_id=%s, message=%s]", task_id, message)
            await pubsub.publish(TASKS_CHANNEL, message=message)

            logger.debug("Retrieving result for task [task_id=%s]", task_id)
            async_result: AsyncResult[RT] = AsyncResult(task_id=task_id)
            result: RT = await async_result.get()

        return result

    def _validate_arguments(self, task_args: tuple, task_kwargs: dict):
        try:
            func_sig: "inspect.Signature" = inspect.signature(self.func)
            func_sig.bind(*task_args, **task_kwargs)
        except TypeError as exc:
            raise InvalidArgument(
                f"These arguments are invalid: args={task_args}, kwargs={task_kwargs}"
            ) from exc


def task(func: t.Callable[P, RT]) -> Task[P, RT]:
    """Decorator to convert a callable into an aiotaskq Task instance."""
    func_module: t.Optional[ModuleType] = inspect.getmodule(func)

    if func_module is None:
        raise ModuleInvalidForTask(
            f'Function "{func.__name__}" is defined in an invalid module {func_module}'
        )

    module_path = ".".join(
        [
            p.split(".py")[0]
            for p in func_module.__file__.strip("./").split("/")  # type: ignore
            if p != "src"
        ]
    )
    task_ = Task[P, RT](func)
    task_.__qualname__ = f"{module_path}.{func.__name__}"
    task_.__module__ = module_path
    return task_
