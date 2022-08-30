"""Module to define the main commands for the cli."""

#!/usr/bin/env python

import asyncio
import typing as t

import typer

from aiotaskq.worker import Defaults, worker

cli = typer.Typer()


@cli.command(name="worker")
def worker_command(app: str, concurrency: t.Optional[int] = Defaults.concurrency):
    """Command to start workers."""
    # loop = asyncio.get_event_loop()
    asyncio.run(worker(app_import_path=app, concurrency=concurrency))


@cli.command(name="metric")
def metric_server(app: str):
    """Command to start server to collect and report tasks metrics (TODO)."""
    print(f"TODO: Running metrics server for app={app}")


if __name__ == "__main__":
    cli()
