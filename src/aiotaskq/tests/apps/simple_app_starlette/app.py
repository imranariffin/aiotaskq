from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

import uvicorn

from .tasks import add as add_, join as join_, fibonacci as fibonacci_


async def add(request: Request) -> JSONResponse:
    body: dict = await request.json()
    x = body["x"]
    y = body["y"]
    content = await add_.apply_async(x, y)
    return JSONResponse(content=content, status_code=201)


async def join(request: Request) -> JSONResponse:
    body: dict = await request.json()
    ls = body["ls"]
    delimiter = body.get("delimiter", ",")
    content = await join_.apply_async(ls=ls, delimiter=delimiter)
    return JSONResponse(content=content, status_code=201)
    

async def fibonacci(request: Request) -> JSONResponse:
    body: dict = await request.json()
    n = body["n"]
    content = await fibonacci_.apply_async(n=n)
    return JSONResponse(content=content, status_code=201)


routes = [
    Route('/add', add, methods=["POST"]),
    Route('/join', join, methods=["POST"]),
    Route('/fibonacci', fibonacci, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app=app)
