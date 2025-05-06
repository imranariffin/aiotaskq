import multiprocessing
import os
import subprocess
from typing import TYPE_CHECKING

import pytest

from aiotaskq.interfaces import ConcurrencyType
from aiotaskq.worker import validate_input

if TYPE_CHECKING:
    from tests.conftest import WorkerFixture


@pytest.mark.asyncio
async def test_concurrency_starts_child_workers(worker: "WorkerFixture"):
    """
    Assert that when --concurrency N option is provided, N child processes will be spawn.
    """
    # Given that the worker cli is run with "--concurrency 4" option
    concurrency = 4
    await worker.start(app="tests.apps.simple_app", concurrency=concurrency)

    # Then the number of child worker processes spawned should be the same as requested
    with os.popen(f"pgrep -P {worker.proc.pid} | wc -l") as child_process_counter:
        child_process_count = int(child_process_counter.read())
    assert child_process_count == concurrency, f"{child_process_count} != {concurrency}"


@pytest.mark.asyncio
async def test_concurrency_starts_child_workers_with_default_concurrency(
    worker: "WorkerFixture",
):
    """
    Assert that when --concurrency is NOT provided, N child processes will be spawned, N=cpu cores.
    """
    # Given that the machine has the following cpu count
    cpu_count_on_machine = multiprocessing.cpu_count()

    # When the worker cli is run without "--concurrency" option
    await worker.start(app="tests.apps.simple_app")

    # Then the number of child worker processes spawned should be the same
    # as cpu core on machine
    with os.popen(f"pgrep -P {worker.pid} | wc -l") as child_process_counter:
        child_process_count = int(child_process_counter.read())
    assert child_process_count == cpu_count_on_machine


def test_incorrect_app():
    # Given that the worker is started with an incorrect app name
    incorrect_app_name = "some.incorrect.app.name"
    bash_command = ["aiotaskq", "worker", incorrect_app_name]
    with subprocess.Popen(args=bash_command, stdout=subprocess.PIPE) as worker_cli_process:
        with WrapClose(proc=worker_cli_process) as worker_cli_process_pipe:
            # Then the worker process should print error message
            output = str(worker_cli_process_pipe.read())
            output_expected = (
                "Error at argument `--app_import_path some.incorrect.app.name`: "
                '"some.incorrect.app.name" is not a path to a valid Python module'
            )
            assert output_expected in output
    # And exit immediately with an error exit code
    assert worker_cli_process.returncode == 1


def test_validate_input():
    # Given an incorrect app path
    incorrect_app_import_path = "some.incorrect.app.name"

    # When validating with `validate_input`
    error_msg = validate_input(app_import_path=incorrect_app_import_path)

    # Then a descriptive error_message should be returned
    assert error_msg == (
        "Error at argument `--app_import_path some.incorrect.app.name`:"
        ' "some.incorrect.app.name" is not a path to a valid Python module'
    )


@pytest.mark.asyncio
async def test_run_worker__incorrect_app_name(worker: "WorkerFixture"):
    # Given a worker being started with an incorrect app path
    await worker.start(
        app="some.incorrect.app.name",
        concurrency=2,
        concurrency_type=ConcurrencyType.MULTIPROCESSING,
        poll_interval_s=1.0,
    )

    # Then the worker should exit immediately with an error exit code
    assert worker.proc.exitcode == 1


@pytest.mark.asyncio
async def test_handle_keyboard_interrupt(worker: "WorkerFixture"):
    # Given a running worker with some child processes
    concurrency = 4
    await worker.start(app="tests.apps.simple_app", concurrency=concurrency)
    bash_command = (
        f"pgrep -P {worker.proc.pid} "  # Get pids of all child processes of the worker
        "| wc -l"  # Count the number of pids
    )
    with os.popen(bash_command) as process_counter:
        process_count_before = int(process_counter.read())
    assert process_count_before == concurrency

    # When SIGINT signal (Keyboard Interrupt aka Ctrl-C) is sent to the worker process
    worker.interrupt()

    # Then all child processes should be terminated
    with os.popen(bash_command) as process_counter:
        process_count_after = int(process_counter.read())
    assert process_count_after == 0


@pytest.mark.asyncio
async def test_handle_termination_signal(worker: "WorkerFixture"):
    # Given a running worker with some child processes
    concurrency = 4
    await worker.start(app="tests.apps.simple_app", concurrency=concurrency)
    bash_command = (
        f"pgrep -P {worker.proc.pid} "  # Get pids of all child processes of the worker
        "| wc -l"  # Count the number of pids
    )
    with os.popen(bash_command) as process_counter:
        process_count_before = int(process_counter.read())
    assert process_count_before == concurrency

    # When SIGTERM signal (Termination signal) is sent to the worker process
    worker.terminate()

    # Then all child processes should be terminated
    with os.popen(bash_command) as process_counter:
        process_count_after = int(process_counter.read())
    assert process_count_after == 0


class WrapClose:
    """Wrap a process and provide context manager support for closing all resources properly."""

    def __init__(self, proc: subprocess.Popen):
        self._proc = proc
        self._stdout = proc.stdout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.close()

    def __getattr__(self, name):
        return getattr(self._stdout, name)

    def close(self):
        self._stdout.close()
        self._proc.wait()
