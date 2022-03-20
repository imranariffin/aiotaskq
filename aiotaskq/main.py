import asyncio
import functools
import json
import typing as t
import uuid

import aioredis

REDIS_URL = "redis://127.0.0.1:6379"
TASKS_CHANNEL = "channel:tasks"
RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"

RT = t.TypeVar("RT")
P = t.ParamSpec("P")


REGISTERED_TASKS: dict[str, tuple[tuple, dict]] = {}


class TaskAlreadyRegistered(RuntimeError):
    pass


class AsyncResult(t.Generic[RT]):
    _result: RT
    _completed: bool = False
    _task_id: str

    def __init__(self, task_id: str) -> None:
        self._task_id = task_id
    
    async def get(self) -> RT:
        redis_client = aioredis.from_url(REDIS_URL)
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(RESULTS_CHANNEL_TEMPLATE.format(task_id=self._task_id))
            _result: RT
            result = None
            while result is None:
                result = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0.1)
            print(result)
            _result = json.loads(result["data"])
        return _result


class Task(t.Generic[P, RT]):
    def __init__(self, f: t.Callable[P, RT]) -> None:
        self.f = f
        self._register_task()

    def __call__(self, *args, **kwargs) -> RT:
        return self.f(*args, **kwargs)

    async def apply_async(self, *args: P.args, **kwargs: P.kwargs) -> RT:
        task_id = _get_task_id(f=self.f, task_id=uuid.uuid4())
        message = json.dumps(
            {
                "task_id": task_id,
                "args": args, 
                "kwargs": kwargs,
            }
        )
        publisher = _get_redis_client()
        await publisher.publish(TASKS_CHANNEL, message=message)
        async_result: AsyncResult[RT] = AsyncResult(task_id=task_id)
        result = await async_result.get()
        return result

    def _register_task(self) -> None:
        f_key: str = f"{self.f.__module__}.{self.f.__qualname__}"
        if f_key in REGISTERED_TASKS:
            raise TaskAlreadyRegistered(f"Task {f_key} has already been registered.")

        REGISTERED_TASKS[f_key] = (tuple(self.f.__annotations__.keys()), {})


_redis_client = None

def _get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    return aioredis.from_url(REDIS_URL, max_connections=10, decode_responses=True)


def register_task(f: t.Callable[P, RT]) -> Task[P, RT]:
    task = Task[P, RT](f)
    return task


def _get_task_id(f: t.Callable, task_id: uuid.UUID) -> str:
    return f"{f.__module__}.{f.__qualname__}:{task_id}"


@register_task
def add(x: int, y: int) -> int:
    return x + y


@register_task
def power(a: int, b: int = 1) -> int:
    return a ** b


@register_task
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


if __name__ == "__main__":
    
    async def main():
        sync_result = add(x=41, y=1)
        async_result = await add.apply_async(x=41, y=1)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
        sync_result = power(2, 64)
        async_result = await power.apply_async(2, 64)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
        sync_result = join([2021, 2, 20])
        async_result = await join.apply_async([2021, 2, 20])
        assert async_result == sync_result, f"{async_result} != {sync_result}"
    
    from asyncio import get_event_loop

    loop = get_event_loop()
    loop.run_until_complete(main())
