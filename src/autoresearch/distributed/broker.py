from __future__ import annotations

import json
import multiprocessing
from queue import Queue
from typing import Any, Optional, Tuple, cast

from ..logging_utils import get_logger

log = get_logger(__name__)


class InMemoryBroker:
    """Simple in-memory message broker using ``multiprocessing.Queue``."""

    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()
        self.queue: Queue[Any] = self._manager.Queue()

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self._manager.shutdown()


class RedisQueue:
    """Minimal queue wrapper backed by Redis lists."""

    def __init__(self, client: "redis.Redis", name: str) -> None:
        self.client = client
        self.name = name

    def put(self, message: dict[str, Any]) -> None:
        self.client.rpush(self.name, json.dumps(message))

    def get(self) -> dict[str, Any]:
        key_data = self.client.blpop([self.name])  # type: ignore[arg-type]
        key, data = cast(Tuple[str, bytes], key_data)  # type: ignore[misc]
        return json.loads(data)


class RedisBroker:
    """Message broker backed by Redis."""

    def __init__(self, url: str | None = None, queue_name: str = "autoresearch") -> None:
        import redis

        self.client = redis.Redis.from_url(url or "redis://localhost:6379/0")
        self.queue = RedisQueue(self.client, queue_name)

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self.client.close()


BrokerType = InMemoryBroker | RedisBroker


def get_message_broker(name: str | None, url: str | None = None) -> BrokerType:
    """Return a message broker instance by name."""
    if name in (None, "memory"):
        return InMemoryBroker()
    if name == "redis":
        return RedisBroker(url)
    raise ValueError(f"Unsupported message broker: {name}")
