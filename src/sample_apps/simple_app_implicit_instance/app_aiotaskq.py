import asyncio
import logging

from aiotaskq.task import task

logger = logging.getLogger(__name__)


@task
def add(ls: list[int]) -> int:
    logger.info("add(%s) ...", ls)
    ret = sum(x for x in ls)
    logger.info("add(%s) -> %s", ls, ret)
    return ret


@task
def times(x: int, y: int) -> int:
    logger.info("times(%s, %s) ...", x, y)
    ret = x * y
    logger.info("times(%s, %s) -> %s", x, y, ret)
    return ret


async def apply_formula():
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    # TODO (Issue #44): Support chain of tasks
    """
    logger.info("apply_formula() ...")
    x, y = await asyncio.gather(times.apply_async(x=1, y=3), times.apply_async(x=3, y=4))
    ret = await add.apply_async([x, y])
    logger.info("apply_formula() -> %s", str(ret))
    return ret


async def main():
    logger.info("Simple App (Aiotaskq)")
    ret = await apply_formula()
    logger.info("Result: %s", ret)
    assert ret == 15
    return ret


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())