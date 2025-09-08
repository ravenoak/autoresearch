from __future__ import annotations

import json
import multiprocessing
from typing import TYPE_CHECKING, Any, Tuple, cast

from ..logging_utils import get_logger

log = get_logger(__name__)


class _CountingQueue:
    """Wrap ``multiprocessing.Queue`` with a reliable ``empty`` check."""

    def __init__(self) -> None:
        self._queue: multiprocessing.Queue[Any] = multiprocessing.Queue()
        self._size = multiprocessing.Value("i", 0)

    def put(self, item: Any) -> None:
        self._queue.put(item)
        with self._size.get_lock():
            self._size.value += 1

    def get(self) -> Any:
        item = self._queue.get()
        with self._size.get_lock():
            self._size.value -= 1
        return item

    def empty(self) -> bool:  # pragma: no cover - trivial
        return self._size.value == 0

    def close(self) -> None:
        self._queue.close()

    def join_thread(self) -> None:
        self._queue.join_thread()


class InMemoryBroker:
    """Simple in-memory message broker using ``multiprocessing.Queue``."""

    def __init__(self) -> None:
        """Initialize a local queue without a manager process for speed."""
        self.queue = _CountingQueue()

    def publish(self, message: dict[str, Any]) -> None:
        """Enqueue ``message`` for later retrieval."""
        self.queue.put(message)

    def shutdown(self) -> None:
        """Close the queue and wait for background threads to exit."""
        self.queue.close()
        self.queue.join_thread()


if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    import redis


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
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "RedisBroker requires the 'redis' package. Install it via the"
                " '[distributed]' extra."
            ) from exc

        self.client = redis.Redis.from_url(url or "redis://localhost:6379/0")
        self.queue = RedisQueue(self.client, queue_name)

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self.client.close()


class RayBroker:
    """Message broker backed by Ray's distributed queue."""

    def __init__(self, queue_name: str = "autoresearch") -> None:
        import ray
        from ray.util.queue import Queue as RayQueue

        if not ray.is_initialized():  # pragma: no cover - optional init
            ray.init(ignore_reinit_error=True, configure_logging=False)
        self._ray = ray
        self.queue = RayQueue(actor_options={"name": queue_name})

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        try:
            if self._ray.is_initialized():
                self._ray.shutdown()
        except Exception as e:  # pragma: no cover - best effort
            log.warning("Failed to shutdown Ray", exc_info=e)


BrokerType = InMemoryBroker | RedisBroker | RayBroker


def get_message_broker(name: str | None, url: str | None = None) -> BrokerType:
    """Return a message broker instance by name."""
    if name in (None, "memory"):
        return InMemoryBroker()
    if name == "redis":
        return RedisBroker(url)
    if name == "ray":
        return RayBroker()
    raise ValueError(f"Unsupported message broker: {name}")
