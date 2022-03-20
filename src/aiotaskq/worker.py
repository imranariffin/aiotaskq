import asyncio
import importlib
import json
import types

import aioredis
import typer

from aiotaskq.constants import REDIS_URL, RESULTS_CHANNEL_TEMPLATE, TASKS_CHANNEL

cli = typer.Typer()


async def worker(app_import_path: str):
    app: types.ModuleType = importlib.import_module(app_import_path)

    redis_client = aioredis.from_url(REDIS_URL)
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(TASKS_CHANNEL)

        while True:
            result = None
            while result is None:
                result = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0.1)
            task_info = json.loads(result["data"])
            task_args = task_info["args"]
            task_kwargs = task_info["kwargs"]
            task_id: str = task_info["task_id"]
            task_func_name: str = task_id.split(":")[0].split(".")[-1]
            task_func = getattr(app, task_func_name)
            task_result = task_func(*task_args, **task_kwargs)
            task_result = json.dumps(task_result)
            await redis_client.publish(RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id), message=task_result)


@cli.command()
def main(app: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker(app_import_path=app))


if __name__ == "__main__":
    cli()
