#!/usr/bin/env python

import asyncio

import typer

from aiotaskq.worker import worker

cli = typer.Typer()


@cli.command(name="worker")
def _worker_command(app: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker(app_import_path=app))


@cli.command(name="metric")
def _metric_server(app: str):
    print(f"TODO: Running metrics server for app={app}")


if __name__ == "__main__":
    cli()
