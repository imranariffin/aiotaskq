"""Define IPubSub implementations."""

import asyncio
import typing as t

import aioredis as redis

from .exceptions import UrlNotSupported
from .interfaces import IPubSub, Message, PollResponse


class PubSub:
    """The user-facing facade for creating the right pubsub implementation based on url."""

    _instance: t.Optional[IPubSub] = None

    @classmethod
    def get(cls, url: str, poll_interval_s: float, **kwargs) -> IPubSub:
        """
        Return the correct pubsub implementation instance based on url.

        Currently supports only Redis (url="redis*").
        """
        if url.startswith("redis"):
            cls._instance = PubSubRedis(url=url, poll_interval_s=poll_interval_s, **kwargs)
            return cls._instance
        raise UrlNotSupported(f'Url "{url}" is currently not supported.')


class PubSubRedis:
    """Redis implementation of a pubsub."""

    def __init__(self, url: str, poll_interval_s: float, **kwargs) -> None:
        self._url = url
        self._poll_interval_s = poll_interval_s
        self._redis_client = redis.Redis.from_url(url=self._url, **kwargs)
        self._redis_pubsub = self._redis_client.pubsub()

    async def __aenter__(self) -> "PubSubRedis":
        """Initialize redis client and redis pubsub client on entering the async context."""
        await self._redis_client.__aenter__()
        await self._redis_pubsub.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Close redis client and redis pubsub client on exiting the async context."""
        await self._redis_pubsub.__aexit__(exc_type, exc_value, traceback)
        await self._redis_client.__aexit__(exc_type, exc_value, traceback)

    async def publish(self, channel: str, message: Message) -> None:
        """Publish the given message to the given channel."""
        await self._redis_client.publish(channel=channel, message=message)

    async def subscribe(self, channel: str) -> None:
        """Start subscribing to the given channel."""
        await self._redis_pubsub.subscribe(channel)

    async def poll(self) -> PollResponse:
        """Keep requesting for a new message on some interval, and return one only if available."""
        message: t.Optional[Message]
        while True:
            message = await self._redis_pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                break
            await asyncio.sleep(self._poll_interval_s)
        return message
