"""Module to define the main logic for the worker."""

from abc import ABC, abstractmethod
import asyncio
from functools import cached_property
import importlib
import inspect
import json
import logging
import multiprocessing
import os
import signal
import sys
import typing as t
import types

from .concurrency_manager import ConcurrencyManagerSingleton
from .constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL
from .interfaces import ConcurrencyType, IConcurrencyManager, IPubSub
from .pubsub import PubSub

if t.TYPE_CHECKING:  # pragma: no cover
    from .task import Task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Define the abstract worker.

    Worker is meant to be run forever with some custom logic inside its forever loop.
    The custom logic inside the forever loop can be written in `_main_loop` -- This is
    where you write your `while True: some_logic`.
    """

    app: types.ModuleType
    pubsub: IPubSub
    concurrency_manager: IConcurrencyManager

    def __init__(self, app_import_path: str):
        self.app = importlib.import_module(app_import_path)

    def run_forever(self) -> None:
        """
        Run the worker forever in a loop, after running some preparation logic (in _pre_run).

        This is the entrypoint from sync world to async.
        """

        async def _start():
            await self._pre_run()
            await self._main_loop()

        asyncio.run(_start())

    @abstractmethod
    async def _pre_run(self):
        """Define any logic to run before running the _main_loop."""

    @abstractmethod
    async def _main_loop(self):
        """Define the logic for the main loop."""

    @cached_property
    def _logger(self):
        return logging.getLogger(f"[{self._pid}] [{self.__class__.__qualname__}]")

    @cached_property
    def _pid(self) -> int:
        return os.getpid()

    @staticmethod
    def _get_child_worker_tasks_channel(pid: int) -> str:
        return f"{TASKS_CHANNEL}:{pid}"


class Defaults:
    """Store default constants for the aiotaskq.worker module."""

    @classmethod
    def concurrency(cls) -> int:
        """Return the number of worker process to spawn."""
        return multiprocessing.cpu_count()

    @classmethod
    def concurrency_type(cls) -> str:
        """Return the default concurrency type ("multiprocessing")."""
        return ConcurrencyType.MULTIPROCESSING.value

    @classmethod
    def worker_rate_limit(cls) -> int:
        """Default to no worker rate limit."""
        return -1

    @classmethod
    def poll_interval_s(cls) -> float:
        """Return the time in seconds to poll for next task."""
        return 0.01


class WorkerManager(BaseWorker):
    """
    Spawn and manage a list of GruntWorkers.

    Each GruntWorker is spawned in its own process via IConcurrencyManager.
    Any task that WorkerManager receives will be published to the GruntWorkers
    via IPubSub. On its own death (TERM/INT signal), it's responsible for killing
    all of its GruntWorker processes.
    """

    def __init__(
        self,
        app_import_path: str,
        concurrency: int,
        concurrency_type: ConcurrencyType,
        worker_rate_limit: int,
        poll_interval_s: float,
    ) -> None:
        self.pubsub: IPubSub = PubSub.get(url=REDIS_URL, poll_interval_s=poll_interval_s)
        self.concurrency_manager: IConcurrencyManager = ConcurrencyManagerSingleton.get(
            concurrency_type=concurrency_type,
            concurrency=concurrency,
        )
        self._worker_rate_limit = worker_rate_limit
        self._poll_interval_s = poll_interval_s
        super().__init__(app_import_path=app_import_path)

    async def _pre_run(self):
        self._logger.info("Starting %s back workers", self.concurrency_manager.concurrency)
        self._start_grunt_workers()
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self._sigterm_handler)
        loop.add_signal_handler(signal.SIGINT, self._sigint_handler)

    def _sigterm_handler(self):
        # pylint: disable=no-member
        self._logger.debug("Handling signal %s (%s)", signal.SIGTERM.value, signal.SIGTERM.name)
        self._handle_murder_signals()

    def _sigint_handler(self):
        # pylint: disable=no-member
        self._logger.debug("Handling signal %s (%s)", signal.SIGINT.value, signal.SIGINT.name)
        self._handle_murder_signals()

    def _handle_murder_signals(self):
        """Terminate (send TERM) to child processes upon receiving murder signals (TERM, INT)."""
        for task in asyncio.tasks.all_tasks():
            task.cancel()
        self.concurrency_manager.terminate()

    async def _main_loop(self):
        self._logger.info("[%s] Started main loop", self._pid)

        async with self.pubsub as pubsub:  # pylint: disable=not-async-context-manager
            counter = -1
            await pubsub.subscribe(TASKS_CHANNEL)
            while True:
                self._logger.debug("[%s] Polling for a new task until it's available", self._pid)
                message = await pubsub.poll()

                # A new task is now available
                # Pass the task to one of the workers worker
                counter = (counter + 1) % len(self.concurrency_manager.processes)
                selected_grunt_worker_pid = self.concurrency_manager.processes[counter].pid
                channel: str = self._get_child_worker_tasks_channel(pid=selected_grunt_worker_pid)
                self._logger.debug(
                    "[%s] Passing task to %sth child worker [message=%s, channel=%s]",
                    *(self._pid, counter, message, channel),
                )
                await pubsub.publish(channel=channel, message=message["data"])

    def _start_grunt_workers(self):
        def _run_grunt_worker_forever():
            grunt_worker = GruntWorker(
                app_import_path=self.app.__name__,
                poll_interval_s=self._poll_interval_s,
                worker_rate_limit=self._worker_rate_limit,
            )
            grunt_worker.run_forever()

        self.concurrency_manager.start(func=_run_grunt_worker_forever)


class GruntWorker(BaseWorker):
    """
    Execute tasks received from WorkerManager.

    Task is received from WorkerManager via IPubSub. The result of a finished task
    will be published to the user via IPubSub.
    """

    def __init__(self, app_import_path: str, poll_interval_s: float, worker_rate_limit: int):
        self.pubsub: IPubSub = PubSub.get(url=REDIS_URL, poll_interval_s=poll_interval_s)
        self._worker_rate_limit = worker_rate_limit
        super().__init__(app_import_path=app_import_path)

    async def _pre_run(self):
        pass

    async def _main_loop(self):
        self._logger.debug("[%s] Started main loop", self._pid)
        channel: str = self._get_child_worker_tasks_channel(pid=self._pid)
        batch_size = self._worker_rate_limit if self._worker_rate_limit != -1 else 99

        # We only need to rate-limit the incoming tasks with batch size if batch_size is provided
        if batch_size != Defaults.worker_rate_limit():
            semaphore = asyncio.Semaphore(batch_size)

        async with self.pubsub as pubsub:  # pylint: disable=not-async-context-manager
            await pubsub.subscribe(channel=channel)
            while True:

                if semaphore is not None:
                    await semaphore.acquire()

                self._logger.debug(
                    "[%s] Polling for a new task from manager until it's available [channel=%s]",
                    *(self._pid, channel),
                )
                message = await pubsub.poll()

                # A new task is now available
                self._logger.debug(
                    "[%s] Received task to from main worker [message=%s, channel=%s]",
                    *(self._pid, message, channel),
                )
                task_info = json.loads(message["data"])
                task_args = task_info["args"]
                task_kwargs = task_info["kwargs"]
                task_id: str = task_info["task_id"]
                task_func_name: str = task_id.split(":")[0].split(".")[-1]
                task: "Task" = getattr(self.app, task_func_name)

                # Fire and forget: execute the task and publish result
                task_asyncio: "asyncio.Task" = self._execute_task_and_publish(
                    pubsub=pubsub,
                    task=task,
                    task_args=task_args,
                    task_kwargs=task_kwargs,
                    task_id=task_id,
                    semaphore=semaphore,
                )
                asyncio.create_task(task_asyncio)

    async def _execute_task_and_publish(
        self,
        pubsub: IPubSub,
        task: "Task",
        task_args: list,
        task_kwargs: dict,
        task_id: str,
        semaphore: t.Optional["asyncio.Semaphore"],
    ):
        self._logger.debug(
            "[%s] Executing task %s(*%s, **%s)",
            *(self._pid, task_id, task_args, task_kwargs),
        )
        if inspect.iscoroutinefunction(task.func):
            task_result = await task(*task_args, **task_kwargs)
        else:
            task_result = task(*task_args, **task_kwargs)

        # Publish the task return value
        self._logger.debug(
            "[%s] Publishing task result %s(*%s, **%s)",
            *(self._pid, task_id, task_args, task_kwargs),
        )
        task_result = json.dumps(task_result)
        result_channel = RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id)
        await pubsub.publish(channel=result_channel, message=task_result)

        if semaphore is not None:
            semaphore.release()


def validate_input(app_import_path: str) -> t.Optional[str]:
    """Validate all worker cli inputs and return an error string if any."""
    try:
        importlib.import_module(app_import_path)
    except ModuleNotFoundError:
        return (
            f"Error at argument `--app_import_path {app_import_path}`:"
            f' "{app_import_path}" is not a path to a valid Python module'
        )

    return None


def run_worker_forever(
    app_import_path: str,
    concurrency: int,
    concurrency_type: ConcurrencyType,
    worker_rate_limit: int,
    poll_interval_s: float,
) -> None:
    """Run the worker manager in a forever loop, and let it spawn and manage the workers."""
    err_msg: t.Optional[str] = validate_input(app_import_path=app_import_path)
    if err_msg:
        print(err_msg)
        sys.exit(1)

    try:
        worker_manager = WorkerManager(
            app_import_path=app_import_path,
            concurrency=concurrency,
            concurrency_type=concurrency_type,
            worker_rate_limit=worker_rate_limit,
            poll_interval_s=poll_interval_s,
        )
        worker_manager.run_forever()
    except asyncio.CancelledError:
        pass
