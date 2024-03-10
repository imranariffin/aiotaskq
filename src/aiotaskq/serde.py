"""
Define serialization and deserialization utilities.
"""

import importlib
import json
import types
import typing as t

import jsonpickle

from .config import Config
from .interfaces import ISerialization, SerializationType, T
from .task import AsyncResult, Task


class Serialization(t.Generic[T]):
    """Expose the JSON serialization and deserialization logic for any object behined a simple abstraction."""

    @classmethod
    def serialize(cls, obj: "T") -> bytes:
        """Serialize an object of type T into bytes via an appropriate serialization logic."""
        s_klass = _get_serde_class(obj.__class__)
        return s_klass.serialize(obj)

    @classmethod
    def deserialize(cls, klass: type["T"], s: bytes) -> "T":
        """Deserialize bytes into an object of type T via an appropriate deserialization logic."""
        s_klass = _get_serde_class(klass)
        return s_klass.deserialize(klass, s)


def _get_serde_class(klass: type["T"]) -> type[ISerialization["T"]]:
    """Get the Serializer-Deserializer class that implements `serialize` and `deserialize`."""
    map_ = {
        (Task, SerializationType.JSON): JsonTaskSerialization,
        (AsyncResult, SerializationType.JSON): JsonAsyncResultSerialization,
    }
    if (klass, Config.serialization_type()) not in map_:
        assert False, "Should not reach here"  # pragma: no cover
    return map_[klass, Config.serialization_type()]


class JsonTaskSerialization(Serialization):
    """Define the JSON serialization and deserialization logic for Task."""

    class TaskOptionsRetryOnDict(t.TypedDict):
        """Define the JSON structure of the retry options of a serialized Task object."""

        max_retries: int | None
        on: str

    class TaskOptionsDict(t.TypedDict):
        """Define the JSON structure of the options of a serialized Task object."""

        retry: "JsonTaskSerialization.TaskOptionsRetryOnDict | None"

    class TaskDict(t.TypedDict):
        """Define the JSON structure of a serialized Task object."""

        func: str
        task_id: str
        args: tuple[t.Any, ...]
        kwargs: dict
        options: "JsonTaskSerialization.TaskOptionsDict"

    @classmethod
    def serialize(cls, obj: "Task") -> bytes:
        """Serialize a Task object to JSON bytes."""
        options: JsonTaskSerialization.TaskOptionsDict = {}
        retry: JsonTaskSerialization.TaskOptionsRetryOnDict | None = None
        if obj.retry is not None:
            retry = {
                "max_retries": obj.retry["max_retries"],
                "on": jsonpickle.encode(obj.retry["on"]),
            }
            options["retry"] = retry
        d_obj: JsonTaskSerialization.TaskDict = {
            "func": {
                "module": obj.__module__,
                "qualname": obj.__qualname__,
            },
            "task_id": obj.id,
            "args": obj.args,
            "kwargs": obj.kwargs,
            "options": options,
        }
        s = f"json|{json.dumps(d_obj)}"
        return s.encode("utf-8")

    @classmethod
    def deserialize(cls, klass: type["Task"], s: bytes) -> "Task":
        """Deserialize JSON bytes to a Task object."""
        s_type, s_obj = s.decode("utf-8").split("|", 1)
        assert s_type == "json"
        d_obj: JsonTaskSerialization.TaskDict = json.loads(s_obj)

        d_options: JsonTaskSerialization.TaskOptionsDict = d_obj["options"]
        retry: JsonTaskSerialization.TaskOptionsRetryOnDict | None = None
        if d_options.get("retry") is not None:
            s_retry: "JsonTaskSerialization.TaskOptionsRetryOnDict" = d_obj["options"]["retry"]
            max_retries: int | None = s_retry["max_retries"]
            retry_on: tuple[type[Exception], ...] = jsonpickle.decode(s_retry["on"])
            retry = {
                "max_retries": max_retries,
                "on": retry_on,
            }

        func_module_path, func_qualname = d_obj["func"]["module"], d_obj["func"]["qualname"]
        func_module: types.ModuleType = importlib.import_module(func_module_path)
        func: types.FunctionType = getattr(func_module, func_qualname).func
        assert func is not None

        obj: "Task" = klass(
            func=func,
            task_id=d_obj["task_id"],
            args=d_obj["args"],
            kwargs=d_obj["kwargs"],
            retry=retry,
        )
        return obj


class JsonAsyncResultSerialization(Serialization):
    """Define the JSON serialization and deserialization logic for AsyncResult."""

    class AsyncResultDict(t.TypedDict):
        """Define the JSON structure of a serialized AsyncResult."""

        task_id: str
        ready: bool
        result: t.Any
        error: str

    @classmethod
    def serialize(cls, obj: "AsyncResult") -> bytes:
        """Serialize AsyncResult object to JSON bytes."""
        error_s: str = jsonpickle.encode(obj.error)
        result_json: JsonAsyncResultSerialization.AsyncResultDict = {
            "task_id": obj.task_id,
            "ready": obj.ready,
            "result": obj.result,
            "error": error_s,
        }
        return f"json|{json.dumps(result_json)}".encode("utf-8")

    @classmethod
    def deserialize(cls, klass: type["AsyncResult"], s: bytes) -> "AsyncResult":
        """Deserialize JSON bytes to a AsyncResult object."""
        s: str = s.decode("utf-8")
        s_type, s_obj = s.split("|", 1)
        assert s_type == "json"
        obj_d: JsonAsyncResultSerialization.AsyncResultDict = json.loads(s_obj)
        result: "AsyncResult" = klass(
            task_id=obj_d["task_id"],
            ready=obj_d["ready"],
            result=obj_d["result"],
            error=jsonpickle.decode(obj_d["error"]),
        )
        return result
