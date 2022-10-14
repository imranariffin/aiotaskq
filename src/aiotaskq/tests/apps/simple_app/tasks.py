import aiotaskq


@aiotaskq.task
def add(x: int, y: int) -> int:
    return x + y


@aiotaskq.task
def power(a: int, b: int = 1) -> int:
    return a ** b


@aiotaskq.task
def join(ls: list, delimiter: str = ",") -> str:
    return delimiter.join([str(x) for x in ls])


@aiotaskq.task
def some_task(b: int) -> int:
    # Some task with high cpu usage
    def _naive_fib(n: int) -> int:
        if n <= 2:
            return 1
        return _naive_fib(n - 1) + _naive_fib(n - 2)

    return _naive_fib(b)
