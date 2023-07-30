from contextlib import redirect_stdout
import io
import multiprocessing
import os

import pytest
import typer

from aiotaskq import __version__
from aiotaskq.__main__ import _version_callback
from aiotaskq.worker import Defaults


def test_root_show_proper_help_message():
    bash_command = "aiotaskq --help"
    with os.popen(bash_command) as pipe:
        output = pipe.read()
        output_expected = (
            "Usage: aiotaskq [OPTIONS] COMMAND [ARGS]...\n"
            "\n"
            "  A simple asynchronous task queue.\n"
            "\n"
            "Options:\n"
            "  --version\n"
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


def test_root__version():
    bash_command = "aiotaskq --version"
    with os.popen(bash_command) as pipe:
        output = pipe.read()
        output_expected = os.popen("grep '^version\\s\\=' pyproject.toml | tr -dc '0-9.'").read()
        assert output == f"{output_expected}\n"


@pytest.mark.lowlevel
def test_version():
    with io.StringIO() as buf, redirect_stdout(buf):
        error = None
        try:
            _version_callback(value=True)
        except typer.Exit as err:
            error = err
        finally:
            assert error is not None
            output = buf.getvalue()
            assert output == f"{__version__}\n"


def test_worker_show_proper_help_message():
    bash_command = "aiotaskq worker --help"
    default_cpu_count: int = multiprocessing.cpu_count()
    default_poll_interval_s: float = Defaults.poll_interval_s()
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
            f"  --concurrency INTEGER           [default: {default_cpu_count}]\n"
            f"  --poll-interval-s FLOAT         [default: {default_poll_interval_s}]\n"
            "  --concurrency-type [multiprocessing]\n"
            "                                  [default: multiprocessing]\n"
            "  --worker-rate-limit INTEGER     [default: -1]\n"
            "  --help                          Show this message and exit.\n"
        )
        assert output == output_expected
