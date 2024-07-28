import asyncio
import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import User
from ...tasks import get_spending_by_user_celery, get_spending_by_user_aiotaskq
from ...utils import Timer, chunker

logger = logging.getLogger(__name__)
timer = Timer(logger, level=logging.INFO)


SpendingByUser = dict[str, float]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--celery", action="store_true")
        parser.add_argument("--aiotaskq", action="store_true")

    def handle(self, *args, **options):
        assert options["celery"] and not options["aiotaskq"] or not options["celery"] or options["aiotaskq"]
        assert not (options["celery"] and options["aiotaskq"])

        r: SpendingByUser
        if options["celery"]:
            with timer("CMD show_total_spending_by_user --celery"):
                r = get_total_spending_by_user_celery()
        else:
            with timer("CMD show_total_spending_by_user --aiotaskq"):
                loop = asyncio.get_event_loop()
                r = loop.run_until_complete(get_total_spending_by_user_aiotaskq())

        suffix = "celery" if options["celery"] else "aiotaskq"
        with (Path(settings.BASE_DIR) / f"out-{suffix}.json").open(mode="w") as fo:
            logger.debug("Writing output to %s ...", fo.name)
            print(json.dumps(r, sort_keys=True, indent=2), file=fo)


def get_total_spending_by_user_celery() -> SpendingByUser:
    logger.debug("get_total_spending_by_user_celery")
    user_ids = list(User.objects.all().values_list("id", flat=True))

    async_results = []
    for user_ids_chunk in chunker(user_ids):
        async_result = get_spending_by_user_celery.si(user_ids=user_ids_chunk).apply_async()
        async_results.append(async_result)

    ret: SpendingByUser = {}
    logger.info("Waiting for %s tasks to finish", len(async_results))
    for async_result in async_results:
        ret.update(async_result.get())
    return ret


async def get_total_spending_by_user_aiotaskq() -> SpendingByUser:
    logger.debug("get_total_spending_by_user_aiotaskq")
    user_ids = [u async for u in User.objects.all().values_list("id", flat=True)]

    tasks = []
    for user_ids_chunk in chunker(user_ids):
        task = get_spending_by_user_aiotaskq.apply_async(user_ids=user_ids_chunk)
        tasks.append(task)

    ret: SpendingByUser = {}
    logger.info("Waiting for %s tasks to finish", len(tasks))
    results: list[SpendingByUser] = await asyncio.gather(*tasks)
    for result in results:
        ret.update(result)
    return ret
