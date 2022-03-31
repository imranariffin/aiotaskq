import asyncio
import importlib
import json
import logging
import multiprocessing
import os
import sys
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
        """Return the time in seconds to poll for next task."""
        return 0.1

    @classmethod
    @property
    def concurrency(cls) -> int:
        """Return the number of worker process to spawn."""
        return multiprocessing.cpu_count()


async def worker(
    app_import_path: str,
    concurrency: t.Optional[int] = None,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
):
    """Main loop for worker to poll for next task and execute them."""

    err_msg: str = _validate_input(app_import_path=app_import_path)
    if err_msg:
        print(err_msg)
        sys.exit(1)

    concurrency: int = concurrency if concurrency is not None else Defaults.concurrency
    pid: int = os.getpid()
    logger.info(
        "[pid=%s] aiotaskq worker \n"
        "\tversion: %s\n"
        "\tpoll interval (seconds): %s\n"
        "\tredis url: %s\n"
        "\tconcurrency: %s\n",
        *(pid, "1.0.0", poll_interval_s, REDIS_URL, concurrency),
    )

    # Ensure child worker processes log to parent's stderr
    multiprocessing.log_to_stderr(logging.DEBUG)

    # Start child worker processes in background
    child_worker_processes: list["multiprocessing.Process"] = [
        multiprocessing.Process(target=_worker, args=(app_import_path, poll_interval_s))
        for _ in range(concurrency)
    ]
    for p in child_worker_processes:
        p.start()
    child_worker_pids = [c.pid for c in child_worker_processes]

    # Main worker accepts new task and pass it on to one of child workers
    logger.info(
        "[%s] Forked %s child worker processes: [pids=%s]",
        *(pid, len(child_worker_processes), child_worker_pids),
    )
    redis_client: aioredis.Redis = aioredis.from_url(REDIS_URL)
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(TASKS_CHANNEL)
        counter = 0
        while True:
            # Poll for a new task until it's available
            message: t.Optional[str] = None
            while message is None:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(poll_interval_s)

            # A new task is now available
            # Pass the task to one of the workers worker
            i = counter % len(child_worker_processes)
            selected_child_worker = child_worker_processes[i]
            channel: str = _get_child_worker_tasks_channel(pid=selected_child_worker.pid)
            logger.debug(
                "[%s] Passing task to %sth child worker [message=%s, channel=%s]",
                *(pid, i, message, channel),
            )
            # Wait for all child workers to be ready before publishing
            await _wait_for_child_workers_ready(
                publisher=redis_client,
                child_worker_pids=child_worker_pids,
                poll_interval_s=poll_interval_s,
            )
            await redis_client.publish(channel, message=message["data"])
            counter += 1


def _worker(
    app_import_path: str,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
):
    pid: int = os.getpid()
    channel: str = _get_child_worker_tasks_channel(pid=pid)
    app: types.ModuleType = importlib.import_module(app_import_path)
    logger.info("Child worker process [pid=%s]", pid)

    async def _main_loop():
        logger.info("[%s] Main loop", pid)
        redis_client: aioredis.Redis = aioredis.from_url(REDIS_URL)
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel)

            while True:
                # Poll for a new task until it's available
                logger.debug(
                    "[%s] Waiting for new tasks from main worker [channel=%s]",
                    *(pid, channel),
                )
                message = None
                while message is None:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    await asyncio.sleep(poll_interval_s)

                # A new task is now available
                logger.debug(
                    "[%s] Received task to from main worker [message=%s, channel=%s]",
                    *(pid, message, channel),
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
                    *(pid, task_id, task_args, task_kwargs),
                )
                task_result = task_func(*task_args, **task_kwargs)

                # Publish the task return value
                task_result = json.dumps(task_result)
                await redis_client.publish(
                    RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id),
                    message=task_result,
                )

    asyncio.run(main=_main_loop())


async def _wait_for_child_workers_ready(
    publisher: aioredis.Redis,
    child_worker_pids: list[int],
    poll_interval_s: int,
) -> None:
    while True:
        # Keep check until all child workers are ready
        ready_statuses_coro: list[t.Coroutine] = [
            publisher.pubsub_numsub(_get_child_worker_tasks_channel(pid=pid))
            for pid in child_worker_pids
        ]
        ready_statuses: list[list[tuple[bytes, int]]] = await asyncio.gather(*ready_statuses_coro)
        if all(is_ready for (_, is_ready), *_ in ready_statuses):
            break
        # Continue waiting and checking
        await asyncio.sleep(poll_interval_s)


def _get_child_worker_tasks_channel(pid: int) -> str:
    return f"{TASKS_CHANNEL}:{pid}"


def _validate_input(app_import_path: str) -> t.Optional[str]:
    try:
        importlib.import_module(app_import_path)
    except ModuleNotFoundError:
        return (
            f"Error at argument `--app_import_path {app_import_path}`:"
            f' "{app_import_path}" is not a path to a valid Python module'
        )

    return None
