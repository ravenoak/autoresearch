"""Tests for distributed message broker helpers."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from autoresearch.distributed.broker import (
    InMemoryBroker,
    RedisBroker,
    RayBroker,
    get_message_broker,
)


def test_get_message_broker_memory() -> None:
    broker = get_message_broker(None)
    assert isinstance(broker, InMemoryBroker)


def test_get_message_broker_invalid() -> None:
    with pytest.raises(ValueError):
        get_message_broker("unknown")


@pytest.mark.requires_distributed
def test_redis_broker_requires_dependency(monkeypatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "redis", None)
    with pytest.raises(ModuleNotFoundError):
        RedisBroker()


def test_ray_broker_publish(monkeypatch) -> None:
    class StubQueue:
        def __init__(self, *a, **k):
            pass

        def put(self, *a, **k):
            pass

    stub_ray = SimpleNamespace(
        is_initialized=lambda: True, shutdown=lambda: None, util=SimpleNamespace(queue=None)
    )
    monkeypatch.setitem(sys.modules, "ray", stub_ray)
    monkeypatch.setitem(sys.modules, "ray.util.queue", SimpleNamespace(Queue=StubQueue))
    broker = RayBroker()
    broker.publish({"x": 1})  # should not raise
