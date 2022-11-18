import asyncio
import logging
import time

from aiotaskq.task import task

logger = logging.getLogger(__name__)


@task
def add(ls: list[int]) -> int:
    logger.info("add(%s) ...", ls)
    time.sleep(5)
    ret = sum(x for x in ls)
    logger.info("add(%s) -> %s", ls, ret)
    return ret


@task
def times(x: int, y: int) -> int:
    logger.info("times(%s, %s) ...", x, y)
    time.sleep(2)
    ret = x * y
    logger.info("times(%s, %s) -> %s", x, y, ret)
    return ret
