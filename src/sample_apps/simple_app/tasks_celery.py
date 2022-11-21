import logging
import time

from celery.canvas import chord, group
import celery

from .celery import app

logger = logging.getLogger(__name__)


@app.task()
def add(ls: list[int]) -> int:
    logger.info("add(%s) ...", ls)
    ret = sum(x for x in ls)
    logger.info("add(%s) -> %s", ls, ret)
    return ret


@app.task()
def times(x: int, y: int) -> int:
    logger.info("times(%s, %s) ...", x, y)
    ret = x * y
    logger.info("times(%s, %s) -> %s", x, y, ret)
    return ret
