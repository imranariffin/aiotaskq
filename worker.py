import asyncio
import json

import aioredis

from aio_redis_taskq.main import *

REDIS_URL = "redis://127.0.0.1:6379"
TASKS_CHANNEL = "channel:tasks"
TASKS_DICT = "dict:tasks"
RESULTS_CHANNEL_TEMPLATE = "channel:results:{task_id}"


def some_task():
    print("Doing some task!")


async def worker():
    redis_client = aioredis.from_url(REDIS_URL)
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(TASKS_CHANNEL)

        while True:
            result = None
            while result is None:
                result = await pubsub.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0.1)
            task_result = (await redis_client.hkeys(TASKS_DICT))[0]
            task_info = json.loads(result["data"])
            task_args = task_info["args"]
            task_kwargs = task_info["kwargs"]
            task_id: str = task_info["task_id"]
            task_func_name: str = task_id.split(":")[0].split(".")[-1]
            task_func = globals()[task_func_name]
            task_result = task_func(*task_args, **task_kwargs)
            await redis_client.publish(RESULTS_CHANNEL_TEMPLATE.format(task_id=task_id), message=task_result)
            # task_json = json.loads(task_result["data"])
            


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker())
