import logging

from celery import Celery
from celery import shared_task

logger = logging.getLogger(__name__)

app = Celery(
    include=["sample_apps.simple_app_implicit_instance.app_celery"],
)
app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/0"


@shared_task
def add(ls: list[int]) -> int:
    logger.debug("add(%s) ...", ls)
    ret = sum(x for x in ls)
    logger.debug("add(%s) -> %s", ls, ret)
    return ret


@shared_task
def times(x: int, y: int) -> int:
    logger.debug("times(%s, %s) ...", x, y)
    ret = x * y
    logger.debug("times(%s, %s) -> %s", x, y, ret)
    return ret
