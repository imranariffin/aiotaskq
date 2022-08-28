import multiprocessing
import os
import subprocess
import time


def test_root_show_proper_help_message():
    bash_command = "aiotaskq --help"
    with os.popen(bash_command) as pipe:
        output = pipe.read()
        output_expected = (
            "Usage: aiotaskq [OPTIONS] COMMAND [ARGS]...\n"
            "\n"
            "Options:\n"
            "  --install-completion [bash|zsh|fish|powershell|pwsh]\n"
            "                                  Install completion for the specified shell.\n"
            "  --show-completion [bash|zsh|fish|powershell|pwsh]\n"
            "                                  Show completion for the specified shell, to\n"
            "                                  copy it or customize the installation.\n"
            "  --help                          Show this message and exit.\n"
            "\n"
            "Commands:\n"
            "  metric  Command to start server to collect and report tasks metrics...\n"
            "  worker  Command to start workers.\n"
        )
        assert output == output_expected


def test_worker_show_proper_help_message():
    bash_command = "aiotaskq worker --help"
    with os.popen(bash_command) as pipe:
        output = pipe.read()
        output_expected = (
            "Usage: aiotaskq worker [OPTIONS] APP\n"
            "\n"
            "  Command to start workers.\n"
            "\n"
            "Arguments:\n"
            "  APP  [required]\n"
            "\n"
            "Options:\n"
            "  --concurrency INTEGER  [default: 8]\n"
            "  --help                 Show this message and exit.\n"
        )
        assert output == output_expected


def test_worker_concurrency_starts_child_workers():
    """
    Assert that when --concurrency N option is provided, N child processes will be spawn.
    """
    # Given that the worker cli is run with "--concurrency 4" option
    concurrency = 4
    bash_command = [
        "aiotaskq",
        "worker",
        "--concurrency",
        str(concurrency),
        "aiotaskq.tests.apps.simple_app",
    ]
    with subprocess.Popen(bash_command) as worker_cli_process:
        worker_cli_pid = worker_cli_process.pid
        # Once we've given enough time for child worker processes to be spawned
        time.sleep(0.5)
        # Then the number of child worker processes spawned should be the same as requested
        with os.popen(f"pgrep -P {worker_cli_pid} | wc -l") as child_process_counter:
            child_process_count = int(child_process_counter.read())
        assert child_process_count == concurrency
        worker_cli_process.terminate()


def test_worker_concurrency_starts_child_workers_with_default_concurrency():
    """
    Assert that when --concurrency is NOT provided, N child processes will be spawned, N=cpu cores.
    """
    # Given that the machine has the following cpu count
    cpu_count_on_machine = multiprocessing.cpu_count()
    # When the worker cli is run without "--concurrency" option
    bash_command = ["aiotaskq", "worker", "aiotaskq.tests.apps.simple_app"]
    with subprocess.Popen(bash_command) as worker_cli_process:
        worker_cli_pid = worker_cli_process.pid
        # Once we've given enough time for child worker processes to be spawned
        time.sleep(0.5)
        # Then the number of child worker processes spawned should be the same
        # as cpu core on machine
        with os.popen(f"pgrep -P {worker_cli_pid} | wc -l") as child_process_counter:
            child_process_count = int(child_process_counter.read())
        assert child_process_count == cpu_count_on_machine
        worker_cli_process.terminate()


def test_worker_incorrect_app():
    # Given that the worker is started with an incorrect app name
    incorrect_app_name = "some.incorrect.app.name"
    bash_command = ["aiotaskq", "worker", incorrect_app_name]
    worker_cli_process = subprocess.Popen(args=bash_command, stdout=subprocess.PIPE)
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


class WrapClose:
    def __init__(self, proc: subprocess.Popen):
        self._proc = proc
        self._stdout = proc.stdout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.close()

    def __getattr__(self, name):
        print(f"__getattr__({name})")
        return getattr(self._stdout, name)

    def close(self):
        self._stdout.close()
        self._proc.wait()
