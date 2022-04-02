import asyncio
import importlib
import json
import logging
import multiprocessing
import os
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

    @classmethod
    @property
    def concurrency(cls) -> int:
        return multiprocessing.cpu_count()


def _worker(
    app_import_path: str,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
):
    pid = os.getpid()
    channel = f"{TASKS_CHANNEL}:{pid}"
    app: types.ModuleType = importlib.import_module(app_import_path)
    logger.info("Child worker process [pid=%s]", pid)

    async def main_loop():
        logger.info("[%s] Main loop", pid)
        redis_client = aioredis.from_url(REDIS_URL)
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel)
            while True:
                # Poll for a new task until it's available
                logger.debug(
                    "Waiting for new tasks from main worker [channel=%s]", channel
                )
                message = None
                while message is None:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    await asyncio.sleep(poll_interval_s)

                # A new task is now available
                logger.debug(
                    "Received task to from main worker [message=%s, channel=%s]",
                    *(message, channel),
                )
                task_info = json.loads(message["data"])
                task_args = task_info["args"]
                task_kwargs = task_info["kwargs"]
                task_id: str = task_info["task_id"]
                task_func_name: str = task_id.split(":")[0].split(".")[-1]
                task_func = getattr(app, task_func_name)

                # Execute the task
                logger.debug(
                    "[%s] Executing task %s(*%s, **%s)",
                    *(os.getpid(), task_id, task_args, task_kwargs),
                )
                task_result = task_func(*task_args, **task_kwargs)

                # Publish the task return value
                task_result = json.dumps(task_result)
                await redis_client.publish(
                    RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id),
                    message=task_result,
                )

    asyncio.run(main_loop())


async def worker(
    app_import_path: str,
    concurrency: t.Optional[int] = None,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
):
    """Main loop for worker to poll for next task and execute them."""
    concurrency = concurrency if concurrency is not None else Defaults.concurrency
    logger.info(
        "aiotaskq worker \n"
        "\tversion: %s\n"
        "\tpoll interval (seconds): %s\n"
        "\tredis url: %s\n"
        "\tconcurrency: %s\n",
        *("1.0.0", poll_interval_s, REDIS_URL, concurrency),
    )
    pid = os.getpid()

    # Ensure child worker processes log parent's stderr
    multiprocessing.log_to_stderr(logging.INFO)

    # with multiprocessing.Pool(concurrency) as p:
    # Start child worker processes in background
    child_worker_processes = [
        multiprocessing.Process(target=_worker, args=(app_import_path, poll_interval_s))
        for _ in range(concurrency)
    ]
    for p in child_worker_processes:
        p.start()

    # Main worker accepts new task and pass it on to one of child workers
    # child_worker_processes = psutil.Process().children()
    logger.debug(
        "[%s] Forked %s child worker processes: [pids=%s]",
        *(pid, len(child_worker_processes), [c.pid for c in child_worker_processes]),
    )
    try:
        redis_client = aioredis.from_url(REDIS_URL)
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(TASKS_CHANNEL)

            counter = 0
            while True:
                # Poll for a new task until it's available
                message = None
                while message is None:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    await asyncio.sleep(poll_interval_s)

                # A new task is now available
                # Pass the task to one of the workers worker
                i = counter % len(child_worker_processes)
                selected_child_worker = child_worker_processes[i]
                channel = f"{TASKS_CHANNEL}:{selected_child_worker.pid}"
                logger.debug(
                    "[%s] Passing task to %sth child worker [message=%s, channel=%s]",
                    *(pid, i, message, channel),
                )
                await redis_client.publish(channel, message=message["data"])
                counter += 1
    except Exception as e:
        logger.error("Some error: %s", e)
    finally:
        logger.info("Cleaning up")
        # Clean up
        p.join()
