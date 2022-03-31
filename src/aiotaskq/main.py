import asyncio
import inspect
import json
import logging
from types import ModuleType
import typing as t
import uuid

import aioredis

from aiotaskq.constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL
from aiotaskq.exceptions import ModuleInvalidForTask, WorkerNotReady

RT = t.TypeVar("RT")
P = t.ParamSpec("P")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AsyncResult(t.Generic[RT]):
    _result: RT
    _completed: bool = False
    _task_id: str

    def __init__(self, task_id: str) -> None:
        self._task_id = task_id

    async def get(self) -> RT:
        redis_client = aioredis.from_url(REDIS_URL)
        async with redis_client.pubsub() as pubsub:
            message: t.Optional[dict] = None
            while message is None:
                await pubsub.subscribe(RESULTS_CHANNEL_TEMPLATE.format(task_id=self._task_id))
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0.1)
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

    function_result = some_func(1, 2)
    sync_task_result = some_task(1, 2)
    async_task_result = some_task.apply_async(1, 2)

    assert function_result == sync_task_result == async_task_result
    ```
    """

    __qualname__: str

    def __init__(self, func: t.Callable[P, RT]) -> None:
        self._f = func
        self._id = uuid.uuid4()

    def __call__(self, *args, **kwargs) -> RT:
        """Call the task synchronously, by directly executing the underlying function."""
        return self._f(*args, **kwargs)

    def get_task_id(self) -> str:
        """Return the task id."""
        return f"{self.__qualname__}:{self._id}"

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
        task_id: str = self.get_task_id()
        message: str = json.dumps(
            {
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
            }
        )
        publisher: aioredis.Redis = _get_redis_client()

        num_subscribers_res: list[tuple[str, int]] = await publisher.pubsub_numsub(TASKS_CHANNEL)
        is_worker_ready = num_subscribers_res[0][1] > 0
        if not is_worker_ready:
            raise WorkerNotReady("No worker is ready to pick up tasks. Have you run your workers?")

        await publisher.publish(TASKS_CHANNEL, message=message)
        async_result: AsyncResult[RT] = AsyncResult(task_id=task_id)
        result: RT = await async_result.get()
        return result


def task(func: t.Callable[P, RT]) -> Task[P, RT]:
    """Decorator to convert a callable into an aiotaskq Task instance."""
    func_module: t.Optional[ModuleType] = inspect.getmodule(func)

    if func_module is None:
        raise ModuleInvalidForTask(f"Function \"{func.__name__}\" is defined in an invalid module {func_module}")

    module_path = ".".join(
        [
            p.split(".py")[0]
            for p in func_module.__file__.strip("./").split("/")  # type: ignore
            if p != "src"
        ]
    )
    task = Task[P, RT](func)
    task.__qualname__ = f"{module_path}.{func.__name__}"
    task.__module__ = module_path
    return task


_REDIS_CLIENT: t.Optional[aioredis.Redis] = None


def _get_redis_client() -> aioredis.Redis:
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    return aioredis.from_url(REDIS_URL, max_connections=10, decode_responses=True)
