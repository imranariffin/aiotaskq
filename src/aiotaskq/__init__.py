"""
Simple Redis Task Queue with async support.

Usage::
    import asyncio

    import aiotaskq


    @aiotaskq.register_task
    def some_task(b: int) -> int:
        # Some task with high cpu usage
        def _naive_fib(n: int) -> int:
            if n <= 1:
                return 1
            elif n <= 2:
                return 2
            return _naive_fib(n - 1) + _naive_fib(n - 2)
        return _naive_fib(b)


    async def main():
        sync_result = some_task(21)
        async_result = await some_task.apply_async(21)
        assert async_result == sync_result

    if __name__ == "__main__":
        asyncio.run_until_complete(main())

"""

from .main import register_task


__all__ = ["register_task"]
