# aiotask

A simple asynchronous task queue

## Motivation

Existing famously used asynchronous worker library (Celery) doesn't support asyncio and is hard to use. This library aims to help users compose tasks in a very native async-await manner. It is also full-typed for better productivity and correctness.

## Simple Usage

```python
import asyncio

import aiotaskq


@aiotaskq.register_task
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 1:
            return 1
        elif n <= 2:
            return 2
        return _naive_fib(n - 1) + _naive_fib(n - 2)
    return _naove_fib(b)


async def main():
    async_result = await some_task.apply_async(42)
    sync_result = some_task(42)
    assert async_result == sync_result

if __name__ == "__main__":
    asyncio.run_until_complete(main())
```

## Advance usage

```python
# TODO: Example of composing chain of tasks (chord + chain in Celery terms)
```

## Install
```bash
pip install aiotaskq
```

## Links

* [PYPI](https://pypi.org/project/aiotaskq/)