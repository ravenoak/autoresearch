from __future__ import annotations

"""Message brokers for distributed orchestration.

The Redis implementation uses ``RedisClientProtocol`` so strict typing can
describe the subset of methods accessed at runtime without ``type: ignore``
directives.
"""

import contextlib
import json
import multiprocessing
from typing import Any, Literal, Protocol, Sequence, TypedDict, cast, runtime_checkable

from ..logging_utils import get_logger
from ._ray import RayLike, RayQueueProtocol, require_ray, require_ray_queue

log = get_logger(__name__)


class AgentResultMessage(TypedDict):
    """Agent execution result emitted by executors and aggregators."""

    action: Literal["agent_result"]
    agent: str
    result: dict[str, Any]
    pid: int


class PersistClaimMessage(TypedDict):
    """Request for the storage coordinator to persist a claim."""

    action: Literal["persist_claim"]
    claim: dict[str, Any]
    partial_update: bool


class StopMessage(TypedDict):
    """Sentinel instructing background workers to stop processing."""

    action: Literal["stop"]


BrokerMessage = AgentResultMessage | PersistClaimMessage | StopMessage


def _ensure_broker_message(payload: dict[str, Any]) -> BrokerMessage:
    """Validate queue payloads so strict typing stays intact."""

    action = payload.get("action")
    if action == "agent_result":
        if not isinstance(payload.get("agent"), str):
            raise TypeError("agent_result messages require an agent name")
        if not isinstance(payload.get("result"), dict):
            raise TypeError("agent_result messages require a result mapping")
        if not isinstance(payload.get("pid"), int):
            raise TypeError("agent_result messages require a worker pid")
        return cast(AgentResultMessage, payload)
    if action == "persist_claim":
        if not isinstance(payload.get("claim"), dict):
            raise TypeError("persist_claim messages require a claim mapping")
        partial_update = payload.get("partial_update")
        if not isinstance(partial_update, bool):
            raise TypeError("persist_claim messages require a boolean flag")
        return cast(PersistClaimMessage, payload)
    if action == "stop":
        return cast(StopMessage, payload)
    raise TypeError(f"Unsupported broker message action: {action!r}")


STOP_MESSAGE: StopMessage = {"action": "stop"}


class _CountingQueue:
    """Wrap ``multiprocessing.Queue`` with a reliable ``empty`` check."""

    def __init__(self) -> None:
        self._queue: multiprocessing.Queue[BrokerMessage] = multiprocessing.Queue()
        self._size = multiprocessing.Value("i", 0)

    def put(self, item: BrokerMessage) -> None:
        self._queue.put(item)
        with self._size.get_lock():
            self._size.value += 1

    def get(self) -> BrokerMessage:
        item = self._queue.get()
        with self._size.get_lock():
            self._size.value -= 1
        return item

    def empty(self) -> bool:  # pragma: no cover - trivial
        return bool(self._size.value == 0)

    def close(self) -> None:
        self._queue.close()

    def join_thread(self) -> None:
        self._queue.join_thread()


class InMemoryBroker:
    """Simple in-memory message broker using ``multiprocessing.Queue``."""

    def __init__(self) -> None:
        """Initialize a local queue without a manager process for speed."""
        self.queue: StorageBrokerQueueProtocol = _CountingQueue()

    def publish(self, message: BrokerMessage) -> None:
        """Enqueue ``message`` for later retrieval."""
        self.queue.put(message)

    def shutdown(self) -> None:
        """Close the queue and wait for background threads to exit."""
        self.queue.close()
        self.queue.join_thread()


class MessageQueueProtocol(Protocol):
    """Queue operations shared by all broker implementations."""

    def put(self, item: BrokerMessage) -> None: ...

    def get(self) -> BrokerMessage: ...

    def close(self) -> None: ...

    def join_thread(self) -> None: ...


@runtime_checkable
class StorageQueueProtocol(Protocol):
    """Queue interface required by the storage module."""

    def put(self, item: PersistClaimMessage) -> None: ...


class StorageBrokerQueueProtocol(MessageQueueProtocol, StorageQueueProtocol, Protocol):
    """Queue protocol compatible with both broker and storage interfaces."""


class RedisClientProtocol(Protocol):
    """Typed subset of redis client behaviour used by :class:`RedisQueue`."""

    def rpush(self, name: str, *values: Any) -> Any:  # pragma: no cover - thin wrapper
        ...

    def blpop(
        self, keys: Sequence[Any], timeout: int | None = None
    ) -> Any:  # pragma: no cover - thin wrapper
        ...

    def close(self) -> None:  # pragma: no cover - thin wrapper
        ...


class RedisQueue(MessageQueueProtocol):
    """Minimal queue wrapper backed by Redis lists."""

    def __init__(self, client: RedisClientProtocol, name: str) -> None:
        self.client = client
        self.name = name

    def put(self, message: BrokerMessage) -> None:
        self.client.rpush(self.name, json.dumps(message))

    def get(self) -> BrokerMessage:
        result = self.client.blpop([self.name])
        if result is None:  # pragma: no cover - blocking call should not return None
            raise RuntimeError("Redis BLPOP returned no data")
        _, data = result
        message = json.loads(data)
        if not isinstance(message, dict):
            raise TypeError("RedisQueue expected a JSON object payload")
        return _ensure_broker_message(cast(dict[str, Any], message))

    def close(self) -> None:  # pragma: no cover - redis connection handles cleanup
        with contextlib.suppress(Exception):
            self.client.close()

    def join_thread(self) -> None:  # pragma: no cover - compatibility shim
        return None


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

        client = redis.Redis.from_url(url or "redis://localhost:6379/0")
        self.client = cast(RedisClientProtocol, client)
        self.queue: StorageBrokerQueueProtocol = RedisQueue(self.client, queue_name)

    def publish(self, message: BrokerMessage) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self.client.close()


class RayMessageQueue(MessageQueueProtocol):
    """Adapter around Ray's distributed queue with a consistent API."""

    def __init__(self, queue: RayQueueProtocol) -> None:
        self._queue = queue

    def put(self, message: BrokerMessage) -> None:
        self._queue.put(message)

    def get(self) -> BrokerMessage:
        payload = self._queue.get()
        if not isinstance(payload, dict):
            raise TypeError("RayQueue expected a mapping payload")
        return _ensure_broker_message(payload)

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._queue.shutdown()

    def join_thread(self) -> None:  # pragma: no cover - Ray queues are remote actors
        return None


class RayBroker:
    """Message broker backed by Ray's distributed queue."""

    def __init__(self, queue_name: str = "autoresearch") -> None:
        ray = require_ray()
        queue_factory = require_ray_queue()
        if not ray.is_initialized():  # pragma: no cover - optional init
            ray.init(ignore_reinit_error=True, configure_logging=False)
        self._ray: RayLike = ray
        self.queue: StorageBrokerQueueProtocol = RayMessageQueue(
            queue_factory(actor_options={"name": queue_name})
        )

    def publish(self, message: BrokerMessage) -> None:
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
