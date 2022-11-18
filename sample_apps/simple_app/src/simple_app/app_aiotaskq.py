import asyncio
import logging

from simple_app.tasks_aiotaskq import add, times

logger = logging.getLogger(__name__)


async def get_formula():
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    # TODO (Issue #44): Support chain of tasks
    """
    logger.info("get_formula() ...")
    x = await times.apply_async(x=1, y=3)
    y = await times.apply_async(x=3, y=4)
    ret = await add.apply_async([x, y])
    logger.info("get_formula() -> %s", str(ret))
    return ret


async def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("simple_app_aiotaskq.app")
    logger.info("Simple App (Aiotaskq)")
    ret = await get_formula()
    logger.info("Result: %s", ret)
    assert ret == 15


if __name__ == "__main__":
    asyncio.run(main())
