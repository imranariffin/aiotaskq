import asyncio

import aioredis as redis


client: redis.Redis = redis.from_url("redis://127.0.0.1:6379")

async def _ping_until_ready():
    while True:
        try:
            response = await client.ping()
            if response is True:
                print("Redis is ready")
                break
        except redis.ConnectionError:
            wait_s = 0.5
            print(f"Redis is not ready. Try pinging again in {wait_s}")
            await asyncio.sleep(wait_s)

asyncio.run(_ping_until_ready())
