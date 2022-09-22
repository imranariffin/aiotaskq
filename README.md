# aiotaskq

[![codecov](https://codecov.io/gh/imranariffin/aiotaskq/branch/main/graph/badge.svg)](https://codecov.io/gh/imranariffin/aiotaskq)
[![build](https://github.com/imranariffin/aiotaskq/actions/workflows/build.yaml/badge.svg)](https://github.com/imranariffin/aiotaskq/actions/workflows/build.yaml)
[![pylint](https://github.com/imranariffin/aiotaskq/actions/workflows/pylint.yaml/badge.svg)](https://github.com/imranariffin/aiotaskq/actions/workflows/pylint.yaml)

A simple asynchronous task queue

## Motivation

Popular asynchronous worker library like [Celery](https://github.com/celery/celery) doesn't support asyncio and is hard to use for advanced usage. `aiotaskq` aims to help users compose tasks in a very native async-await manner.

Plus, it is also fully-typed for better productivity and correctness.

Give it a try and let us know if you like it. For questions or feedback feel to file issues on this repository.

## Example Usage
Install aiotaskq
```bash
python -m pip install --upgrade pip
pip install aiotaskq
```
Define a simple app like the following:
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


@aiotaskq.task
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 2:
            return 1
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
# Output: sync_result == async_result == 165580141. Awesome!
```

## Advanced usage example
Let's say we want to compose a workflow where we want to break up some of the tasks and run them in parallel:
```
                    |-- task_2 --> |
                    |-- task_2 --> |     | task_3 --> |
START -> task_1 --> |-- task_2 --> | --> | task_3 --> | --> task_4 --> FINISH
                    |-- task_2 --> |     | task_3 --> |
                    |-- task_2 --> |
```

Using `celery` we might end up with this
```python
from celery import Celery

app = Celery()


@app.task
def task_1(*args, **kwargs):
        pass


@app.task
def task_2(*args, **kwargs):
        pass


@app.task
def task_3(*args, **kwargs):
        pass


@app.task
def task_4(*args, **kwargs):
        pass


if __name__ == "__main__":
    step_1 = task_1.si(some_arg="a")
    step_2 = [task_2.si(some_arg=f"{i}") for i in range(5)]
    step_3 = [task_3.si(some_arg=f"{i}") for i in range(3)]
    step_4 = task_4.si(some_arg="b")
    workflow = chord(
        header=step_1,
        body=chord(
            header=step_2,
            body=chord(
                header=step_3,
                body=step_4,
            ),
        ),
    )
    output = workflow.apply_async().get()
    print(output)
```

Using `aiotaskq` we may end up with the following:
```python
import asyncio

from aiotaskq import task


@task
def task_1(*args, **kwargs):
        pass


@task
def task_2(*args, **kwargs):
        pass


@task
def task_3(*args, **kwargs):
        pass


@task
def task_4(*args, **kwargs):
        pass


# So far the same as celery

# And now the workflow is just native python, and you're free
# to use any `asyncio` library of your choice to help with composing
# your workflow e.g. `trio` to handle more advanced scenarios like
# error propagation, task cancellation etc.
if __name__ == "__main__":
    step_1 = task_1.apply_async()
    step_2 = asyncio.gather(task_2.apply_async(arg=f"{i}" for i in range(5)))
    step_3 = asyncio.gather(task_3.apply_async(arg=f"{i}" for i in range(3)))
    step_4 = task_4.apply_async()
    workflow = [step_1, step_2, step_3, step_4]
    output = await asyncio.gather(workflow)
    print(output)
```

## Install

```bash
pip install aiotaskq
```

## Development

```bash
source ./activate.sh
```

## Tests

In another terminal

```bash
./docker.sh
```

In the main terminal

```bash
source ./activate.sh
./test.sh
```

## Links

* [PYPI](https://pypi.org/project/aiotaskq/)
