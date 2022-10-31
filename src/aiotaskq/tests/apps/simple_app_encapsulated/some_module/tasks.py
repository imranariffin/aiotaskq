from ..aiotaskq import app


@app.register_task
def add(a: int, b: int) -> int:
    return a + b
