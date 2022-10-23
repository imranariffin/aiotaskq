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
