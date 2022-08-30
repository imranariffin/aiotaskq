"""Module to define the main commands for the cli."""

#!/usr/bin/env python

import typing as t

import typer

from .interfaces import ConcurrencyType
from .worker import Defaults, run_worker_forever

cli = typer.Typer()


@cli.command(name="worker")
def worker_command(
    app: str,
    concurrency: t.Optional[int] = Defaults.concurrency,
    poll_interval_s: t.Optional[float] = Defaults.poll_interval_s,
    concurrency_type: t.Optional[ConcurrencyType] = Defaults.concurrency_type,
):
    """Command to start workers."""
    run_worker_forever(
        app_import_path=app,
        concurrency=concurrency,
        concurrency_type=concurrency_type,
        poll_interval_s=poll_interval_s,
    )


@cli.command(name="metric")
def metric_server(app: str):
    """Command to start server to collect and report tasks metrics (TODO)."""
    print(f"TODO: Running metrics server for app={app}")


if __name__ == "__main__":
    cli()
