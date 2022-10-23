import asyncio

from .tasks import join


if __name__ == "__main__":  # pragma: no cover

    async def main():
        ret = await join.apply_async(["Hello", "World"], delimiter=" ")
        print(ret)

    asyncio.run(main())
