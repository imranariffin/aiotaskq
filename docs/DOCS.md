[Back to README](/README.md)

* [API References](#api-references)
* [Guides](#guides)

# API References

TODO (Issue [#43](https://github.com/imranariffin/aiotaskq/issues/43))

# Guides

Note: We try to provide guides that you can follow along by copy pasting the codes as you read, given that you've already cloned the repository. We believe that's the best way to understand the concepts in full. If there's any guide that doesn't work, please create an issue.

### Outline

1. [Sample usage (Simple App)](#1-sample-usage---simple-app)
2. [Advanced usage (Simple App)](#2-advanced-usage---simple-app)
3. [Sample usage (Starlette Simple App)](#3-sample-usage---starlette-simple-app)

### 1. Sample usage - Simple App

Given a simple app with this structure:

```bash
tree src/aiotaskq/tests/apps/simple_app/
# src/aiotaskq/tests/apps/simple_app/
# ├── app.py
# ├── __init__.py
# └── tasks.py
```

Where this is the definition of app.py:

```py
# ../src/aiotaskq/tests/apps/simple_app/app.py

import asyncio

from .tasks import join


if __name__ == "__main__":  # pragma: no cover

    async def main():
        ret = await join.apply_async(["Hello", "World"], delimiter=" ")
        print(ret)

    asyncio.run(main())

```

Where this is the definition of the tasks:
```py
# ../src/aiotaskq/tests/apps/simple_app/tasks.py

import aiotaskq


@aiotaskq.task
def add(x: int, y: int) -> int:
    return x + y


@aiotaskq.task
def power(a: int, b: int = 1) -> int:
    return a**b


@aiotaskq.task
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


@aiotaskq.task
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 2:
            return 1
        return _naive_fib(n - 1) + _naive_fib(n - 2)

    return _naive_fib(b)

```

Then you can verify that one of the endpoint returns the expected response:
```bash
# ./check-guides.sh#L14-L35

echo -e "\n===\nExample usage 1: Sample usage - Simple App\n===\n"
echo "Run worker in the background & save the pid ..."
python -m aiotaskq worker aiotaskq.tests.apps.simple_app.tasks & worker_pid=$!
echo "Run server in the background & save the pid ..."
python -m aiotaskq.tests.apps.simple_app.app & server_pid=$!
echo "Wait 2 second(s) for server & worker to be ready ..."
sleep 2
echo "Run the app and check the output ..."
output_actual=$(python -m aiotaskq.tests.apps.simple_app.app)
output_expected="Hello World"
set +x
test "$output_actual" = "$output_expected"
if [ "$?" = "0" ]
then
  echo -e "🎉🎉🎉\n\nPass :D"
else
  echo -e "⛔⛔⛔\n\nFailed :("
  failed="1"
fi
set -x
echo "Kill the server & worker processes ..."
kill -TERM $worker_pid && unset worker_pid
```

For full example, see [src/aiotaskq/tests/apps/simple_app/test_integration.py](../src/aiotaskq/tests/apps/simple_app/test_integration.py)
```py
# ../src/aiotaskq/tests/test_integration.py#L14-L27

async def test_sync_and_async_parity__simple_app(worker: WorkerFixture):
    # Given a simple app running as a worker
    await worker.start(app=simple_app.__name__, concurrency=8)
    # Then there should be parity between sync and async call of the tasks
    tests: list[tuple[Task, tuple, dict]] = [
        (simple_app.add, tuple(), {"x": 41, "y": 1}),
        (simple_app.power, (2,), {"b": 64}),
        (simple_app.join, ([2021, 2, 20],), {}),
        (simple_app.some_task, (21,), {}),
    ]
    for task, args, kwargs in tests:
        sync_result = task(*args, **kwargs)
        async_result = await task.apply_async(*args, **kwargs)
        assert async_result == sync_result, f"{async_result} != {sync_result}"
```

### 2. Advanced usage - Simple App

TODO (Issue [#44](https://github.com/imranariffin/aiotaskq/issues/44))

### 3. Sample usage - Starlette Simple App

Say you define a simple starlette app with this structure:

```bash
tree src/aiotaskq/tests/apps/simple_app_starlette/
# src/aiotaskq/tests/apps/simple_app_starlette/
# ├── app.py
# ├── __init__.py
# └── tasks.py
```

Where this is the main app logic:

```py
# ../src/aiotaskq/tests/apps/simple_app_starlette/app.py

import logging
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

import uvicorn

from .tasks import (
    add as add_,
    fibonacci as fibonacci_,
    join as join_,
    power as power_,
)


async def add(request: Request) -> JSONResponse:
    body: dict = await request.json()
    x: int = body["x"]
    y: int = body["y"]
    content: int = await add_.apply_async(x, y)
    return JSONResponse(content=content, status_code=201)


async def power(request: Request) -> JSONResponse:
    body: dict = await request.json()
    a: int = body["a"]
    b: int = body["b"]
    content: int = await power_.apply_async(a=a, b=b)
    return JSONResponse(content=content, status_code=201)


async def join(request: Request) -> JSONResponse:
    body: dict = await request.json()
    ls: list = body["ls"]
    delimiter: str = body.get("delimiter", ",")
    content = await join_.apply_async(ls=ls, delimiter=delimiter)
    return JSONResponse(content=content, status_code=201)


async def fibonacci(request: Request) -> JSONResponse:
    body: dict = await request.json()
    n: int = body["n"]
    content: int = await fibonacci_.apply_async(n=n)
    return JSONResponse(content=content, status_code=201)


async def healthcheck(request: Request) -> JSONResponse:  # pylint: disable=unused-argument
    return JSONResponse(content={}, status_code=200)


routes = [
    Route("/add", add, methods=["POST"]),
    Route("/power", power, methods=["POST"]),
    Route("/join", join, methods=["POST"]),
    Route("/fibonacci", fibonacci, methods=["POST"]),
    Route("/healthcheck", healthcheck, methods=["GET"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app=app, log_level=logging.ERROR)

```
And this is the definition of the tasks:
```py
# ../src/aiotaskq/tests/apps/simple_app_starlette/tasks.py

import aiotaskq


@aiotaskq.task
def add(x: int, y: int) -> int:
    return x + y


@aiotaskq.task
def power(a: int, b: int = 1) -> int:
    return a**b


@aiotaskq.task
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


@aiotaskq.task
def fibonacci(n: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(m: int) -> int:
        if m <= 2:
            return 1
        return _naive_fib(m - 1) + _naive_fib(m - 2)

    return _naive_fib(n)

```

Then you can verify that one of the endpoint returns the expected response:
```bash
# ./check-guides.sh#L37-L62

echo -e "\n===\nExample usage 3: Sample usage - Starlette Simple App\n===\n"
echo "Run worker in the background & save the pid ..."
python -m aiotaskq worker aiotaskq.tests.apps.simple_app_starlette.tasks & worker_pid=$!
echo "Run server in the background & save the pid ..."
python -m aiotaskq.tests.apps.simple_app_starlette.app & server_pid=$!
echo "Wait 2 second(s) for server & worker to be ready ..."
sleep 2
echo "Make a request to one of the endpoints & check if correct ..."
response_actual=$(curl --silent -X POST \
  http://127.0.0.1:8000/add \
  -H 'Content-Type: application/json' \
  -d '{"x": 123, "y": 456}'
)
response_expected="579"
set +x
test "$response_actual" = "$response_expected"
if [ "$?" = "0" ]
then
  echo -e "🎉🎉🎉\n\nPass :D"
else
  echo -e "⛔⛔⛔\n\nFailed :("
  failed="1"
fi
set -x
echo "Kill the server & worker processes"
kill -TERM $server_pid $worker_pid && unset server_pid worker_pid
```

For full example, see this test at [../src/aiotaskq/tests/test_integration.py](../src/aiotaskq/tests/test_integration.py):
```py
# ../src/aiotaskq/tests/test_integration.py#L31-L66

async def test_sync_and_async_parity__simple_app_starlette(
    worker: WorkerFixture,
    server_starlette: ServerStarletteFixture,
):
    # Given a simple starlette app running as a worker
    await worker.start(app=simple_app_starlette_worker.__name__)
    # And a simple starlette app running as a server
    await server_starlette.start(app=f"{simple_app_starlette.__name__}:app")

    # Then there should be parity between sync and async call of the tasks
    tests: list[tuple[Task, tuple, dict]] = [
        (simple_app_starlette_worker.add, tuple(), {"x": 41, "y": 1}),
        (simple_app_starlette_worker.power, tuple(), {"a": 2, "b": 64}),
        (simple_app_starlette_worker.join, tuple(), {"ls": [2021, 2, 20]}),
        (simple_app_starlette_worker.fibonacci, tuple(), {"n": 21}),
    ]
    for task, args, kwargs in tests:
        sync_result = task(*args, **kwargs)
        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            body = {**kwargs}
            response = await client.post(
                f"http://127.0.0.1:8000/{task.__name__}", json=body, headers=headers
            )

            # And the endpoints should be working correctly with the worker
            status_code_actual = response.status_code
            status_code_expected = 201
            assert status_code_actual == status_code_expected
            # And the response should match the direct sync result from the task
            response_data_actual = response.json()
            response_data_expected = sync_result
            assert response_data_actual == response_data_expected
```
