from .tasks import join


if __name__ == "__main__":  # pragma: no cover
    from asyncio import get_event_loop

    async def main():
        ret = await join.apply_async(["Hello", "World"], delimiter=" ")
        print(ret)

    loop = get_event_loop()
    loop.run_until_complete(main())
