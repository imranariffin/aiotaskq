import asyncio
import importlib
import json
import logging
import types
import typing as t

import aioredis

from aiotaskq.constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Defaults:
    """Store default constants for the aiotaskq.worker module."""

    @classmethod
    @property
    def poll_interval_s(cls) -> float:
        """Seconds to poll for next task."""
        return 0.1


async def worker(
    app_import_path: str,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
):
    """Main loop for worker to poll for next task and execute them."""
    app: types.ModuleType = importlib.import_module(app_import_path)

    logger.info(
        "aiotaskq worker \n\tversion: %s\n\tpoll interval (seconds): %s\n\tredis url: %s",
        *("1.0.0", poll_interval_s, REDIS_URL),
    )

    redis_client = aioredis.from_url(REDIS_URL)
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(TASKS_CHANNEL)

        while True:
            # Poll for a new task until it's available
            result = None
            while result is None:
                result = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(poll_interval_s)

            # A new task is now available
            task_info = json.loads(result["data"])
            task_args = task_info["args"]
            task_kwargs = task_info["kwargs"]
            task_id: str = task_info["task_id"]
            task_func_name: str = task_id.split(":")[0].split(".")[-1]
            task_func = getattr(app, task_func_name)

            # Execute the task
            logger.debug("Executing task %s(*%s, **%s)", task_id, task_args, task_kwargs)
            task_result = task_func(*task_args, **task_kwargs)

            # Publish the task return value
            task_result = json.dumps(task_result)
            await redis_client.publish(
                RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id), message=task_result
            )
