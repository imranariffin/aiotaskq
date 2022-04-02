import multiprocessing
from operator import mul
import os
import subprocess
import time
import unittest


class TestCli(unittest.TestCase):
    def test_root_show_proper_help_message(self):
        bashCommand = "aiotaskq --help"
        with os.popen(bashCommand) as pipe:
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
                "  metric\n"
                "  worker\n"
            )
            self.assertEqual(output, output_expected)

    def test_worker_show_proper_help_message(self):
        bashCommand = "aiotaskq worker --help"
        with os.popen(bashCommand) as pipe:
            output = pipe.read()
            output_expected = (
                "Usage: aiotaskq worker [OPTIONS] APP\n"
                "\n"
                "Arguments:\n"
                "  APP  [required]\n"
                "\n"
                "Options:\n"
                "  --concurrency INTEGER\n"
                "  --help                 Show this message and exit.\n"
            )
            self.assertEqual(output, output_expected)

    def test_worker_concurrency_starts_child_workers(self):
        """
        Assert that when --concurrency N option is provided, N child processes will be spawn.
        """
        # Given that the worker cli is run with "--concurrency 4" option
        concurrency = 4
        bashCommand = [
            "aiotaskq",
            "worker",
            "--concurrency",
            str(concurrency),
            "aiotaskq.tests.test_app",
        ]
        with subprocess.Popen(bashCommand) as worker_cli_process:
            worker_cli_pid = worker_cli_process.pid
            # Once we've given enough time for child worker processes to be spawned
            time.sleep(1)
            # Then the number of child worker processes spawned should be the same as requested
            with os.popen(
                f"pgrep -P {worker_cli_pid} | wc -l"
            ) as child_process_counter:
                child_process_count = int(child_process_counter.read())
            self.assertEqual(child_process_count, concurrency)
            worker_cli_process.terminate()

    def test_worker_concurrency_starts_child_workers_with_default_concurrency(self):
        """
        Assert that when --concurrency N option is NOT provided, child processes will be spawn with N=cpu core on machine.
        """
        # Given that the worker cli is run without "--concurrency" option
        default_concurrency = multiprocessing.cpu_count()
        bashCommand = ["aiotaskq", "worker", "aiotaskq.tests.test_app"]
        with subprocess.Popen(bashCommand) as worker_cli_process:
            worker_cli_pid = worker_cli_process.pid
            # Once we've given enough time for child worker processes to be spawned
            time.sleep(1)
            # Then the number of child worker processes spawned should be the same as cpu core on machine
            with os.popen(
                f"pgrep -P {worker_cli_pid} | wc -l"
            ) as child_process_counter:
                child_process_count = int(child_process_counter.read())
            self.assertEqual(child_process_count, default_concurrency)
            worker_cli_process.terminate()
