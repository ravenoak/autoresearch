# mypy: ignore-errors
"""Shared executor helpers for distributed integration tests.

These utilities provide lightweight doubles for process- and Ray-based
executors so individual tests can focus on behavioural assertions without
duplicating boilerplate agent definitions.
"""

from __future__ import annotations

import os
from collections.abc import MutableSequence
from dataclasses import dataclass
from typing import Callable

from pytest import MonkeyPatch

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from autoresearch.distributed.broker import StorageBrokerQueueProtocol


@dataclass(slots=True)
class TrackingAgent:
    """Agent stub that records process identifiers for assertions."""

    name: str
    pids: MutableSequence[int]

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Always allow execution while satisfying the agent protocol."""

        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict[str, object]:
        """Record the current process identifier and update the state."""

        self.pids.append(os.getpid())
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


TrackingAgentGetter = Callable[[str], TrackingAgent]
AgentFactoryInstaller = Callable[[MonkeyPatch, MutableSequence[int]], TrackingAgentGetter]
BrokerQueueInstaller = Callable[
    [MonkeyPatch, StorageBrokerQueueProtocol | None],
    StorageBrokerQueueProtocol,
]


def patch_tracking_agent_factory(
    monkeypatch: MonkeyPatch, pids: MutableSequence[int]
) -> TrackingAgentGetter:
    """Monkeypatch :class:`AgentFactory` to return :class:`TrackingAgent` instances."""

    def _get_agent(name: str, llm_adapter: object | None = None) -> TrackingAgent:  # noqa: ARG001
        return TrackingAgent(name=name, pids=pids)

    monkeypatch.setattr(AgentFactory, "get", _get_agent)
    return _get_agent


__all__ = [
    "AgentFactoryInstaller",
    "BrokerQueueInstaller",
    "TrackingAgent",
    "TrackingAgentGetter",
    "patch_tracking_agent_factory",
]
