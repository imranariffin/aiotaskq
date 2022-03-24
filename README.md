# aiotask

A simple asynchronous task queue

## Motivation

Existing famous asynchronous worker library (Celery) doesn't support asyncio and is hard to use. This library aims to help users compose tasks in a very native async-await manner. It is also full-typed for better productivity and correctness.

## Example Usage
Install aiotaskq
```bash
python -m pip install --upgrade pip
pip install aiotaskq
```
Define simple app like the following:
```bash
tree .
.
└── app
    └── app.py
```
Where `app.py` contains the following:
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
    print(f"sync_result == async_result == 165580141. Awesome!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```
Start redis
```bash
docker run --publish 127.0.0.1:6379:6379 redis
```
In a different terminal, start the aiotaskq worker
```bash
python -m aiotaskq worker app.app
```
Then in another different terminal, run your app
```bash
python ./app.py
# Output: sync_result == async_result == {42}. Awesome!
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