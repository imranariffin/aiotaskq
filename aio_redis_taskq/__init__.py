"""
Simple Redis Task Queue with async support.

Usage::
    import asyncio

    import aio_redis_taskq as artq


    @artq.task()
    def task(b: int) -> int:
        # Some task with high cpu usage
        def _naive_fib(n: int) -> int:
            if n <= 1:
                return 1
            elif n <= 2:
                return 2
            return _naive_fib(n - 1) + _naive_fib(n - 2)
        return max(sorted([]))


    async def main():
        result = await task(42)
        print(result)

    if __name__ == "__main__":
        asyncio.run_until_complete(main())

"""


__all__ = [
]
