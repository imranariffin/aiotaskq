from importlib import import_module
import json

from aiotaskq.serde import JsonTaskSerialization
from aiotaskq.task import Task, task


@task()
def some_task(a: int, b: int) -> int:
    return a * b


class SomeException(Exception):
    pass


@task(
    options={
        "retry": {"max_retries": 1, "on": (SomeException,)},
    },
)
def some_task_2(a: int, b: int) -> int:
    return a * b


def test_serialize_task_to_json():
    # Given a task definition
    assert isinstance(some_task, Task)

    # When the task has been serialized to json
    task_serialized = JsonTaskSerialization.serialize(some_task)

    # Then the resulting json should be in correct type and format
    assert isinstance(task_serialized, bytes)
    # And should able to deserialized into the same task
    task_deserialized = JsonTaskSerialization.deserialize(Task, task_serialized)
    task_format_str, task_serialized_str = task_serialized.decode("utf-8").split("|", 1)
    assert task_format_str == "json"
    # And the task should be serialized into correct json
    task_serialized_dict = json.loads(task_serialized_str)
    assert task_serialized_dict == {
        "func": {"module": "tests.test_serde", "qualname": "some_task"},
        "task_id": None,
        "args": None,
        "kwargs": None,
        "options": {},
    }
    # And should be functionally the same as the original task
    assert task_deserialized.func(1, 2) == some_task.func(1, 2)
    assert task_deserialized(3, 4) == some_task(3, 4)


def test_serialize_task_to_json__with_retry_param():
    # Given a task definition
    assert isinstance(some_task_2, Task)

    # When the task has been serialized to json
    task_serialized = JsonTaskSerialization.serialize(some_task_2)

    # Then the task should be serialized in the correct type and format
    assert isinstance(task_serialized, bytes)
    task_format_str, task_serialized_str = task_serialized.decode("utf-8").split("|", 1)
    assert task_format_str == "json"
    # And the serialized task should contain information about retry
    task_serialized_dict = json.loads(task_serialized_str)
    assert task_serialized_dict == {
        "func": {"module": "tests.test_serde", "qualname": "some_task_2"},
        "task_id": None,
        "args": None,
        "kwargs": None,
        "options": {
            "retry": {
                "max_retries": 1,
                "on": '{"py/tuple": [{"py/type": "tests.test_serde.SomeException"}]}',
            },
        },
    }
    # And the deserialized task should function the same as the original
    task_deserialized = import_module(task_serialized_dict["func"]["module"]).some_task_2
    assert task_deserialized(2, 3) == some_task_2(2, 3)
