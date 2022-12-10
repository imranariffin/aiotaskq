import asyncio
import logging
import os

from .tasks_aiotaskq import add, times

logger = logging.getLogger(__name__)


async def apply_formula():
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    # TODO (Issue #44): Support chain of tasks
    """
    logger.info("apply_formula() ...")
    x = await times.apply_async(x=1, y=3)
    y = await times.apply_async(x=3, y=4)
    ret = await add.apply_async([x, y])
    logger.info("apply_formula() -> %s", str(ret))
    return ret


async def main():
    log_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "FATAL": logging.FATAL,
    }[os.environ["LOG_LEVEL"].upper()]
    logging.basicConfig(level=log_level)
    logger.info("Simple App (Aiotaskq)")
    ret = await apply_formula()
    logger.info("Result: %s", ret)
    assert ret == 15
    return ret


if __name__ == "__main__":
    asyncio.run(main())
