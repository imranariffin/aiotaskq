import asyncio
import logging
import os

import aiotaskq

logger = logging.getLogger(__name__)


class SomeException(Exception):
    pass


class SomeException2(Exception):
    pass


@aiotaskq.task(
    options={
        "retry": {
            "max_retries": 2,
            "on": (SomeException,),
        },
    },
)
async def append_to_file(filename: str) -> None:
    """
    Append pid to file for testing purpose and unconditionally raise SomeException.

    How is this useful for testing?

    This task is defined with retry options. By appending to a file and raising exception at the
    end, we can check how many times this task has been applied and verify if the retry logic is
    working.
    """
    _append_pid_to_file(filename=filename)
    raise SomeException("Some error")


@aiotaskq.task()
async def append_to_file_2(filename: str) -> None:
    """
    Append pid to file for testing purpose and unconditionally raise SomeException2.

    This works exactly the same as `append_to_file` except that:
     1. We're raising a different exception.
     2. The task is not defined with the retry options

    This can help us verify that:
     1. The retry logic can also be provided during task call instead of only during task
        defintion
     2. The retry logic is applied only against the specified exception classes
    """
    _append_pid_to_file(filename=filename)
    raise SomeException2


@aiotaskq.task(
    options={
        "retry": {
            "max_retries": 2,
            "on": (SomeException,),
        },
    },
)
async def append_to_file_first_3_times_with_error(filename: str) -> None:
    """
    Append pid to file for testing purpose and *conditionally* raise SomeException.

    This works exactly the same as `append_to_file` except that we're raising
    SomeException only on a certain condition.

    This can help us verify that a task will only be retried while it fails -- once
    it successfully run without error, it will no longer be retried.
    """
    _append_pid_to_file(filename=filename)
    # If func has been called <= 2 times (file has <= 2 lines), raise SomeException2.
    # Else, return without error.
    with open(filename, mode="r", encoding="utf-8") as fi:
        num_lines = len(fi.read().rstrip("\n").split("\n"))
    if num_lines <= 2:
        raise SomeException


def _append_pid_to_file(filename: str) -> None:
    content: str = str(os.getpid())
    with open(filename, mode="a", encoding="utf-8") as fo:
        fo.write(content + "\n")
        fo.flush()


@aiotaskq.task()
def echo(x):
    return x


@aiotaskq.task()
async def wait(t_s: int) -> int:
    """Wait asynchronously for `t_s` seconds."""
    await asyncio.sleep(t_s)
    return t_s


@aiotaskq.task()
def add(x: int, y: int) -> int:
    return x + y


@aiotaskq.task()
def power(a: int, b: int = 1) -> int:
    return a**b


@aiotaskq.task()
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


@aiotaskq.task()
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 2:
            return 1
        return _naive_fib(n - 1) + _naive_fib(n - 2)

    return _naive_fib(b)


if __name__ == "__main__":  # pragma: no cover
    from asyncio import get_event_loop

    async def main():
        ret = await join.apply_async(["Hello", "World"], delimiter=" ")
        print(ret)

    loop = get_event_loop()
    loop.run_until_complete(main())
