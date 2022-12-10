import logging

from celery.canvas import Signature, chord, group
from .tasks_celery import add, times

logger = logging.getLogger(__name__)


def apply_formula() -> Signature:
    """
    Implement f(x) -> sum(x * y for x, y in zip([1, 2], [3, 4])).
    """
    logger.info("apply_formula() ...")
    times_tasks: list[Signature] = [
        times.si(x=1, y=3),
        times.si(x=3, y=4),
    ]
    ret: Signature = chord(header=group(times_tasks), body=add.s())
    logger.info("apply_formula() -> %s", str(ret))
    return ret


def main():
    logger.info("Simple App (Celery)")
    ret = apply_formula().apply_async().get()
    logger.info("Result: %s", ret)
    assert ret == 15
    return ret


if __name__ == "__main__":
    main()
