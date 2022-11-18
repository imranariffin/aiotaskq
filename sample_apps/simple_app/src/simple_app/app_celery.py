import logging

from celery.canvas import Signature, chord, group
from simple_app.tasks_celery import add, times

logger = logging.getLogger(__name__)


def get_formula() -> Signature:
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    """
    logger.info("get_formula() ...")
    times_tasks: list[Signature] = [
        times.si(x=1, y=3),
        times.si(x=3, y=4),
    ]
    ret: Signature = chord(header=group(times_tasks), body=add.s())
    logger.info("get_formula() -> %s", str(ret))
    return ret


def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("simple_app_celery.app")
    logger.info("Simple App (Celery)")
    ret = get_formula().apply_async().get()
    logger.info("Result: %s", ret)
    assert ret == 15


if __name__ == "__main__":
    main()
