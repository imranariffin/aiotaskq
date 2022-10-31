from ..some_file_name import some_app


@some_app.register_task
def add(a: int, b: int) -> int:
    return a + b
