import multiprocessing
import os


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
            f"  --concurrency INTEGER           [default: {multiprocessing.cpu_count()}]\n"
            "  --poll-interval-s FLOAT         [default: 0.01]\n"
            "  --concurrency-type [multiprocessing]\n"
            "                                  [default: multiprocessing]\n"
            "  --help                          Show this message and exit.\n"
        )
        assert output == output_expected
