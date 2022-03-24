import asyncio
import json
import logging
import typing as t
import uuid

from aiotaskq.constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL
from aiotaskq.exceptions import WorkerNotReady

import aioredis

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
                await pubsub.subscribe(
                    RESULTS_CHANNEL_TEMPLATE.format(task_id=self._task_id)
                )
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0.1)
            logger.debug("Message: %s", message)
            _result: RT = json.loads(message["data"])
        return _result


class Task(t.Generic[P, RT]):

    __qualname__: str

    def __init__(self, f: t.Callable[P, RT]) -> None:
        self._f = f
        self._id = uuid.uuid4()

    def __call__(self, *args, **kwargs) -> RT:
        return self._f(*args, **kwargs)

    def get_task_id(self) -> str:
        return f"{self.__qualname__}:{self._id}"

    async def apply_async(self, *args: P.args, **kwargs: P.kwargs) -> RT:
        task_id = self.get_task_id()
        message = json.dumps(
            {
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
            }
        )
        publisher = _get_redis_client()

        is_worker_ready = (await publisher.pubsub_numsub(TASKS_CHANNEL))[0][1] > 0
        if not is_worker_ready:
            raise WorkerNotReady(
                "No worker is ready to pick up tasks. Have you run your workers?"
            )

        await publisher.publish(TASKS_CHANNEL, message=message)
        async_result: AsyncResult[RT] = AsyncResult(task_id=task_id)
        result = await async_result.get()
        return result


def register_task(f: t.Callable[P, RT]) -> Task[P, RT]:
    import inspect

    func_module = inspect.getmodule(f)
    module_path = ".".join(
        [p.split(".py")[0] for p in func_module.__file__.strip("./").split("/") if p != "src"]  # type: ignore
    )
    task = Task[P, RT](f)
    task.__qualname__ = f"{module_path}.{f.__name__}"
    task.__module__ = module_path
    return task


_redis_client = None


def _get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    return aioredis.from_url(REDIS_URL, max_connections=10, decode_responses=True)
