"""Shared orchestrator doubles used by integration tests.

These helpers centralise monkeypatched collaborators so individual tests only
need to describe the behaviour they exercise.  The dataclass-backed agent
double records coalition visibility, invocation order, and optionally produces
final answers.  Queue stubs implement the broker protocols with precise
``BrokerMessage`` typing so type-checks remain strict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

from pytest import MonkeyPatch

import autoresearch.storage as storage_module
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.distributed.broker import BrokerMessage
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager

AgentResultFactory = Callable[[QueryState, ConfigModel], Mapping[str, object]]


@dataclass(slots=True)
class AgentDouble:
    """Configurable agent stub for orchestrator integration tests."""

    name: str
    call_log: list[str] = field(default_factory=list)
    seen_coalitions: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    can_execute_value: bool = True
    answer_on_execute: bool = False
    result: Mapping[str, object] | None = None
    result_factory: AgentResultFactory | None = None
    error: Exception | None = None

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Record visible coalitions while returning the configured decision."""

        self.seen_coalitions[self.name] = {
            coalition: list(members)
            for coalition, members in state.coalitions.items()
        }
        return self.can_execute_value

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        **_: Any,
    ) -> dict[str, Any]:
        """Return a result payload while updating orchestrator state."""

        if self.error is not None:
            raise self.error

        self.call_log.append(self.name)
        payload = self._build_payload(state, config)

        if self.answer_on_execute:
            final_answer = ", ".join(self.call_log)
            payload.setdefault("answer", final_answer)
            results_section = payload.setdefault("results", {})
            if isinstance(results_section, Mapping):
                results_section = dict(results_section)
                results_section.setdefault("final_answer", final_answer)
            payload["results"] = results_section

        state.update(payload)
        return payload

    def _build_payload(
        self,
        state: QueryState,
        config: ConfigModel,
    ) -> dict[str, Any]:
        if self.result_factory is not None:
            source = self.result_factory(state, config)
        elif self.result is not None:
            source = self.result
        else:
            source = {
                "results": {self.name: "ok"},
                "claims": [
                    {
                        "id": f"{self.name.lower()}-claim",
                        "text": f"claim {self.name}",
                        "content": f"claim {self.name}",
                        "audit_status": "supported",
                        "audit": {
                            "claim_id": f"{self.name.lower()}-claim",
                            "status": "supported",
                        },
                    }
                ],
                "reasoning": [f"claim {self.name}"],
            }
        return {key: value for key, value in source.items()}


@dataclass(slots=True)
class BrokerQueueStub:
    """In-memory queue conforming to ``StorageBrokerQueueProtocol``."""

    items: list[BrokerMessage] = field(default_factory=list)
    closed: bool = False
    joined: bool = False

    def put(self, item: BrokerMessage) -> None:
        self.items.append(item)

    def get(self) -> BrokerMessage:
        if not self.items:
            raise RuntimeError("BrokerQueueStub is empty")
        return self.items.pop(0)

    def close(self) -> None:
        self.closed = True

    def join_thread(self) -> None:
        self.joined = True


@dataclass(slots=True)
class PersistClaimCall:
    """Capture payloads passed to ``StorageManager.persist_claim``."""

    claim: dict[str, Any]
    partial_update: bool


def patch_agent_factory_get(
    monkeypatch: MonkeyPatch,
    agents: Iterable[AgentDouble],
) -> Callable[[str], AgentDouble]:
    """Monkeypatch :class:`AgentFactory` to return the provided doubles."""

    agent_map = {agent.name: agent for agent in agents}

    def get_agent(name: str) -> AgentDouble:
        try:
            return agent_map[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise AssertionError(f"Unexpected agent requested: {name}") from exc

    monkeypatch.setattr(AgentFactory, "get", get_agent)
    return get_agent


def patch_storage_persist(
    monkeypatch: MonkeyPatch,
    calls: list[PersistClaimCall] | None = None,
) -> Callable[[dict[str, Any], bool], None]:
    """Monkeypatch storage persistence while recording invocations."""

    records: list[PersistClaimCall] = calls if calls is not None else []

    def persist_claim(claim: dict[str, Any], partial_update: bool = False) -> None:
        records.append(
            PersistClaimCall(claim=dict(claim), partial_update=partial_update)
        )

    monkeypatch.setattr(StorageManager, "persist_claim", persist_claim)
    return persist_claim


def patch_storage_queue(
    monkeypatch: MonkeyPatch,
    queue: BrokerQueueStub | None = None,
) -> BrokerQueueStub:
    """Attach a stubbed broker queue to :mod:`autoresearch.storage`."""

    stub = queue if queue is not None else BrokerQueueStub()
    monkeypatch.setattr(storage_module, "_message_queue", stub, raising=False)
    return stub


__all__ = [
    "AgentDouble",
    "AgentResultFactory",
    "BrokerQueueStub",
    "PersistClaimCall",
    "patch_agent_factory_get",
    "patch_storage_persist",
    "patch_storage_queue",
]
