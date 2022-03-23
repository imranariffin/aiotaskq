# aiotask

A simple asynchronous task queue

## Motivation

Existing famously used asynchronous worker library (Celery) doesn't support asyncio and is hard to use. This library aims to help users compose tasks in a very native async-await manner. It is also full-typed for better productivity and correctness.

## How it works

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │      App                    Task Queue                   Workers        │
  │                                                                         │
  │                                                         ┌──────────┐    │
  │                                                         │          │    │
  │                                                       ┌─┴────────┐ │    │
  │                                                       │          │ │    │
  │ ┌─────────────┐         ┌─────────────────┐         ┌─┴────────┐ │ │    │
  │ │             │ Publish │                 │         │          │ │ │    │
  │ │             │ task    │                 │         │          │ │ │    │
  │ │   Task      ├─────────► Tasks channel   ├─────────►          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │ Publish │          │ │ │    │
  │ │             │         │                 │ result  │          │ │ │    │
  │ │ AsyncResult ◄─────────┤ Results channel ◄─────────┤          │ │ │    │
  │ │             │         │                 │         │          │ │ │    │
  │ │             │         │                 │         │          │ ├─┘    │
  │ │             │         │                 │         │          │ │      │
  │ │             │         │                 │         │          │ │      │
  │ │             │         │                 │         │          ├─┘      │
  │ │             │         │                 │         │          │        │
  │ └─────────────┘         └─────────────────┘         └──────────┘        │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

1. App publishes a new task to Task Queue (Task channel) by calling `.apply_async()`
2. One of the workers will pick up the task from Task Queue (Task channel)
3. The worker will run the body of the task and publish return value to Task Queue (Results channel)
4. Async Result picks up the result of the task from Task Queue (Results channel)
5. App, Task Queue, and Workers are different processes. Workers may consist of 1 or more processes. Task Queue is currently only Redis.

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
    return _naive_fib(b)


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