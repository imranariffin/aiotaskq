import time

from aiotaskq.app import Aiotaskq

app = Aiotaskq(
    # includes=[".tasks"],
)
some_app = app


@app.register_task
def add(ls: list[int]) -> int:
    time.sleep(5)
    return sum(x for x in ls)
