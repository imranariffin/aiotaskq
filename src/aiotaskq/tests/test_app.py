from asyncio import get_event_loop

import aiotaskq
from aiotaskq.worker import worker


@aiotaskq.register_task
def add(x: int, y: int) -> int:
    return x + y


@aiotaskq.register_task
def power(a: int, b: int = 1) -> int:
    return a**b


@aiotaskq.register_task
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


@aiotaskq.register_task
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 0:
            return 0
        elif n <= 2:
            return 1
        return _naive_fib(n - 1) + _naive_fib(n - 2)

    return _naive_fib(b)


if __name__ == "__main__":

    async def main():
        sync_result = add(x=41, y=1)
        async_result = await add.apply_async(x=41, y=1)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
        sync_result = power(2, b=64)
        async_result = await power.apply_async(2, b=64)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
        sync_result = join([2021, 2, 20])
        async_result = await join.apply_async([2021, 2, 20])
        assert async_result == sync_result, f"{async_result} != {sync_result}"
        sync_result = some_task(21)
        async_result = await some_task.apply_async(21)
        assert async_result == sync_result, f"{async_result} != {sync_result}"

    loop = get_event_loop()
    t = loop.create_task(worker("aiotaskq.tests.test_app"))
    loop.run_until_complete(main())
    t.cancel()
