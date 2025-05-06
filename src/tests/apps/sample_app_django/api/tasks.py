import logging
from threading import get_native_id

from celery import shared_task
from django.db.models import Sum

from aiotaskq.task import task

from .models import Order
from .utils import Timer

logger = logging.getLogger(__name__)
timer = Timer(logger)


SpendingByUser = dict[str, float]


@shared_task()
def get_spending_by_user_celery(user_ids: list[int]) -> dict[str, float]:  # pragma: no cover
    # Note that we're excluding this function from coverage since Celery with
    # pre-fork currently doesn't work well with coverage multi-process.
    # See: https://github.com/nedbat/coveragepy/issues/689)
    with timer(
        f"[{get_native_id()}][get_spending_by_user_celery] "
        f"Calculate spending for {len(user_ids)} users"
    ):
        qs = (
            Order.objects  # pylint: disable=no-member
            .filter(user_id__in=user_ids)
            .values("user__username")
            .order_by("user__username")
            .annotate(total_spending=Sum("price"))
        )
        ret = {v["user__username"]: float(v["total_spending"]) for v in qs}
    return ret


@task()
async def get_spending_by_user_aiotaskq(user_ids: list[int]) -> dict[str, float]:
    with timer(
        f"[{get_native_id()}][get_spending_by_user_aiotaskq] "
        f"Calculate spending for {len(user_ids)} users"
    ):
        qs = (
            Order.objects  # pylint: disable=no-member
            .filter(user_id__in=user_ids)
            .values("user__username")
            .order_by("user__username")
            .annotate(total_spending=Sum("price"))
        )
        ret = {v["user__username"]: float(v["total_spending"]) async for v in qs}
    return ret
