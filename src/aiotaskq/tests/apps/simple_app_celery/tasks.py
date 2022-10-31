import time
from celery import chord, group
import celery

from .celery import app


@app.task()
def add(ls: list[int]) -> int:
    time.sleep(5)
    return sum(x for x in ls)


@app.task()
def times(x: int, y: int) -> int:
    time.sleep(2)
    return x * y


def get_formula():
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    """

    times_tasks: list[celery.Task] = [
        times.si(x=1, y=2),
        times.si(x=3, y=4),
    ]
    return chord(
        header=group(times_tasks),
        body=add.s(),
    )
