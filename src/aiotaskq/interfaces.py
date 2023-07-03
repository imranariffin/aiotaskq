"""
Define all interfaces for the library.

Interfaces are mainly typing.Protocol classes, but may also include
other declarative classes like enums or Types.
"""

import enum
import typing as t


Message = t.Union[str, bytes]


class PollResponse(t.TypedDict):
    """Define the dictionary returned from a pubsub."""

    type: str
    data: Message
    pattern: t.Optional[str]
    channel: bytes


class IProcess(t.Protocol):
    """
    Define the interface for a process used in the library.

    It's more or less the same as the `multiprocessing.Process` except this
    one only has attributes that are necessary for the library, and also has
    slightly different typing e.g. pid in our case is always an `int`, whereas
    the one from `multiprocessing.Process` is `Optional[int]`. This way we're
    not limited to `multiprocessing.Process` and may switch to another implementation
    if needed.
    """

    @property
    def pid(self) -> t.Optional[int]:
        """Return the process id (pid)."""

    def start(self):
        """Start running the process."""

    def terminate(self):
        """Send TERM signal to the process."""


class ConcurrencyType(str, enum.Enum):
    """Define supported concurrency types."""

    MULTIPROCESSING = "multiprocessing"


class IConcurrencyManager(t.Protocol):
    """
    Define the interface of a concurrency manager.

    It should be able to start x number of processes given & terminate them.
    """

    concurrency: int
    processes: list[IProcess]

    def __init__(self, concurrency: int) -> None:
        """Initialize the concurrency manager."""

    def start(self, func: t.Callable, *args: t.ParamSpecArgs) -> None:
        """Start each process under management."""

    def terminate(self) -> None:
        """Terminate each process under management."""


class IPubSub(t.Protocol):
    """
    Define the interface of Publisher-Subscriber.

    This is the typical usage of this interface:

    ```
    # Publisher code:
    async with SomePubSub() as some_publisher:
        message = "Hello World"
        channel = "Some-Channel"
        await some_publisher.publish(channel, message)
        print(f"Sent message: {message}")

    # Subscriber code:
    async with SomePubSub() as some_subscriber:
        channel = "Some-Channel"
        await some_subscriber.subscribe(channel)
        while True:
            message = await some_subscriber.poll()
            print(f"Got message: {message}")
    ```
    """

    def __init__(self, url: str, poll_interval_s: float, *args, **kwargs):
        """Initialize the pubsub class."""

    async def __aenter__(self) -> "IPubSub":
        """Instantiate/start resources when entering the async context."""

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Close resources when entering the async context."""

    async def publish(self, channel: str, message: Message) -> None:
        """Publish the given messaage to the given channel."""

    async def subscribe(self, channel: str) -> None:
        """Start subscribing to the given channel."""

    async def poll(self) -> PollResponse:
        """Poll for new message from the subscribed channel, and return it."""


class IWorker(t.Protocol):
    """
    Define the interface for a worker.

    It should also be tied to a specific app.
    It should be able to subscribe, poll and publish messages to the other worker.
    """

    pubsub: IPubSub
    app_import_path: str

    def run_forever(self) -> None:
        """Run the worker forever in a loop."""


class IWorkerManager(IWorker):
    """
    Define the interface for a worker manager.

    This is similar to a worker, but has more authority since it is the one
    one who create and kill other workers via its concurrency manager.
    """

    concurrency_manager: IConcurrencyManager
